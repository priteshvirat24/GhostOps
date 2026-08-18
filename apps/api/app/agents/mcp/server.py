import time
import uuid
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, select, asc

from app.agents.mcp.contracts import (
    MCPToolDefinition,
    MCPToolRequest,
    MCPToolResponse,
)
from app.db.models import (
    Incident,
    IncidentEvidence,
    IncidentEvent,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
    AgentDecision,
)
from app.services.retrieval import HistoricalRetrievalService
from app.core.logging import logger

def sanitize_untrusted_evidence(text_or_obj: Any) -> str:
    """
    Prompt Injection Defense (§9.4):
    Wraps untrusted operational telemetry in explicit data boundaries
    and neutralizes embedded system control phrases.
    """
    if text_or_obj is None:
        return ""
    if not isinstance(text_or_obj, str):
        import json
        raw = json.dumps(text_or_obj, default=str)
    else:
        raw = text_or_obj
    sanitized = re.sub(
        r'(?i)(?:ignore\s+previous\s+instructions|system\s+prompt|execute\s+command|run\s+tool|override\s+policy)',
        '[NEUTRALIZED_UNTRUSTED_TEXT]',
        raw
    )
    return f"<untrusted_evidence>\n{sanitized}\n</untrusted_evidence>"

class GhostOpsMCPServer:
    """
    Managed Model Context Protocol (MCP) Server for GhostOps (§9.2, §19.3).
    Exposes read-only inspection surfaces to Historian/Investigator/Temporal specialists,
    and gated saga execution tools with strict allowlists to the Execution Agent.
    """

    TOOLS: Dict[str, MCPToolDefinition] = {
        # Read-Only Tools (Historian & Investigator)
        "read_cloudwatch": MCPToolDefinition(
            name="read_cloudwatch",
            description="Reads CloudWatch telemetry alarms and log stream events for a target incident.",
            input_schema={"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
            read_only=True,
            risk_level="L0"
        ),
        "read_cloudtrail": MCPToolDefinition(
            name="read_cloudtrail",
            description="Reads CloudTrail API modification logs and IAM events for audit correlation.",
            input_schema={"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
            read_only=True,
            risk_level="L0"
        ),
        "read_config_snapshot": MCPToolDefinition(
            name="read_config_snapshot",
            description="Reads AWS Config and CockroachDB topology snapshot at incident origin.",
            input_schema={"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
            read_only=True,
            risk_level="L0"
        ),
        "sql_query": MCPToolDefinition(
            name="sql_query",
            description="Executes a read-only CockroachDB SQL query with least-privilege scoping.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            read_only=True,
            risk_level="L1"
        ),
        "vector_search": MCPToolDefinition(
            name="vector_search",
            description="Performs unified CockroachDB native VECTOR distance search across institutional memories.",
            input_schema={"type": "object", "properties": {"incident_id": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["incident_id"]},
            read_only=True,
            risk_level="L1"
        ),
        "diff_infra_state": MCPToolDefinition(
            name="diff_infra_state",
            description="Computes structured 9-dimension diff between historical snapshot and current environment.",
            input_schema={"type": "object", "properties": {"historical_incident_id": {"type": "string"}, "current_incident_id": {"type": "string"}}, "required": ["historical_incident_id"]},
            read_only=True,
            risk_level="L1"
        ),
        "get_version_matrix": MCPToolDefinition(
            name="get_version_matrix",
            description="Retrieves CockroachDB and microservice version compatibility matrix.",
            input_schema={"type": "object", "properties": {"db_version": {"type": "string"}}, "required": ["db_version"]},
            read_only=True,
            risk_level="L0"
        ),
        # Policy & Sandbox Validation Tools
        "policy_check": MCPToolDefinition(
            name="policy_check",
            description="Deterministic policy engine evaluation against governance allowlist (not LLM).",
            input_schema={"type": "object", "properties": {"action_type": {"type": "string"}, "target_resource": {"type": "string"}, "parameters": {"type": "object"}}, "required": ["action_type", "target_resource"]},
            read_only=True,
            risk_level="L1"
        ),
        "sandbox_execute": MCPToolDefinition(
            name="sandbox_execute",
            description="Executes command dry-run on ephemeral CockroachDB ccloud sandbox cluster.",
            input_schema={"type": "object", "properties": {"command": {"type": "string"}, "schema_version": {"type": "string"}}, "required": ["command"]},
            read_only=True,
            risk_level="L2"
        ),
        # Governed Execution Tools (Execution Agent only)
        "ccloud_cli": MCPToolDefinition(
            name="ccloud_cli",
            description="Executes governed CockroachDB cluster administration actions via ccloud CLI.",
            input_schema={"type": "object", "properties": {"command": {"type": "string"}, "cluster_id": {"type": "string"}}, "required": ["command"]},
            read_only=False,
            requires_approval=True,
            risk_level="L4"
        ),
        "change_security_rule": MCPToolDefinition(
            name="change_security_rule",
            description="Modifies or revokes network ingress/egress security group rules in AWS EC2.",
            input_schema={"type": "object", "properties": {"security_group_id": {"type": "string"}, "protocol": {"type": "string"}, "port": {"type": "integer"}, "cidr_block": {"type": "string"}}, "required": ["security_group_id", "protocol", "port", "cidr_block"]},
            read_only=False,
            requires_approval=True,
            risk_level="L3"
        ),
        "aws_lambda_invoke": MCPToolDefinition(
            name="aws_lambda_invoke",
            description="Invokes target AWS Lambda remediation handler function.",
            input_schema={"type": "object", "properties": {"function_name": {"type": "string"}, "payload": {"type": "object"}}, "required": ["function_name"]},
            read_only=False,
            requires_approval=True,
            risk_level="L3"
        ),
        "aws_ssm_run_command": MCPToolDefinition(
            name="aws_ssm_run_command",
            description="Executes predefined SSM document script on target EC2/ECS node.",
            input_schema={"type": "object", "properties": {"document_name": {"type": "string"}, "instance_id": {"type": "string"}}, "required": ["document_name", "instance_id"]},
            read_only=False,
            requires_approval=True,
            risk_level="L3"
        ),
        # Independent Verification Tools
        "read_metrics": MCPToolDefinition(
            name="read_metrics",
            description="Reads independent CloudWatch application error rates and p99 latency recovery metrics.",
            input_schema={"type": "object", "properties": {"service": {"type": "string"}, "metric_name": {"type": "string"}, "window_minutes": {"type": "integer"}}, "required": ["service"]},
            read_only=True,
            risk_level="L0"
        ),
        "read_security_group_state": MCPToolDefinition(
            name="read_security_group_state",
            description="Performs independent readback of EC2 Security Group rules to verify revocation/state.",
            input_schema={"type": "object", "properties": {"security_group_id": {"type": "string"}, "port": {"type": "integer"}}, "required": ["security_group_id"]},
            read_only=True,
            risk_level="L0"
        ),
    }

    @classmethod
    def list_tools(cls) -> List[MCPToolDefinition]:
        return list(cls.TOOLS.values())

    @classmethod
    def execute_tool(cls, request: MCPToolRequest, db: Session) -> MCPToolResponse:
        t0 = time.time()
        req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"

        if request.tool_name not in cls.TOOLS:
            return MCPToolResponse(
                success=False,
                tool_name=request.tool_name,
                request_id=req_id,
                idempotency_key=request.idempotency_key,
                error={"code": "TOOL_NOT_FOUND", "message": f"Tool '{request.tool_name}' is not registered in MCP catalog."},
                duration_ms=round((time.time() - t0) * 1000, 2)
            )

        tool_def = cls.TOOLS[request.tool_name]

        # Enforce Read/Write segregation & Idempotency check for mutating tools
        if not tool_def.read_only:
            existing_action = db.scalars(
                select(OperationalActionHistory).where(OperationalActionHistory.idempotency_key == request.idempotency_key)
            ).first()
            if existing_action and existing_action.result == "SUCCESS":
                return MCPToolResponse(
                    success=True,
                    tool_name=request.tool_name,
                    request_id=req_id,
                    idempotency_key=request.idempotency_key,
                    data={"status": "IDEMPOTENT_REPLAY", "action_id": existing_action.id, "result": existing_action.result, "execution_mode": existing_action.execution_mode},
                    evidence_refs=[existing_action.id],
                    duration_ms=round((time.time() - t0) * 1000, 2)
                )

        try:
            handler_method = getattr(cls, f"_handle_{request.tool_name}", None)
            if handler_method:
                data, evidence_refs = handler_method(request.arguments, db, request)
                duration = round((time.time() - t0) * 1000, 2)
                return MCPToolResponse(
                    success=True,
                    tool_name=request.tool_name,
                    request_id=req_id,
                    idempotency_key=request.idempotency_key,
                    data=data,
                    evidence_refs=evidence_refs,
                    duration_ms=duration
                )
            else:
                from app.core.config import settings
                if not settings.AWS_MOCK_MODE and not tool_def.read_only:
                    # In real AWS mode, never simulate success for unhandled mutating tools
                    duration = round((time.time() - t0) * 1000, 2)
                    return MCPToolResponse(
                        success=False,
                        tool_name=request.tool_name,
                        request_id=req_id,
                        idempotency_key=request.idempotency_key,
                        error={"code": "REAL_EXECUTION_BLOCKED", "message": f"Real AWS handler not configured for '{request.tool_name}' in production mode."},
                        duration_ms=duration
                    )

                duration = round((time.time() - t0) * 1000, 2)
                return MCPToolResponse(
                    success=True,
                    tool_name=request.tool_name,
                    request_id=req_id,
                    idempotency_key=request.idempotency_key,
                    data={"status": "MOCK_SUCCESS", "args": request.arguments, "execution_mode": "MOCK"},
                    duration_ms=duration
                )
        except Exception as e:
            logger.error(f"[GhostOpsMCPServer] Execution error in {request.tool_name}: {e}")
            duration = round((time.time() - t0) * 1000, 2)
            return MCPToolResponse(
                success=False,
                tool_name=request.tool_name,
                request_id=req_id,
                idempotency_key=request.idempotency_key,
                error={"code": "EXECUTION_ERROR", "message": str(e)},
                duration_ms=duration
            )

    # Tool Handlers
    @classmethod
    def _handle_read_cloudwatch(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        inc_id = args.get("incident_id")
        evidence = db.scalars(
            select(IncidentEvidence).where(IncidentEvidence.incident_id == inc_id, IncidentEvidence.source == "cloudwatch")
        ).all()
        data = [
            {
                "evidence_id": ev.id,
                "event_type": ev.event_type,
                "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
                "payload_sanitized": sanitize_untrusted_evidence(ev.raw_payload),
            } for ev in evidence
        ]
        return data, [ev.id for ev in evidence]

    @classmethod
    def _handle_read_cloudtrail(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        inc_id = args.get("incident_id")
        evidence = db.scalars(
            select(IncidentEvidence).where(IncidentEvidence.incident_id == inc_id, IncidentEvidence.source == "cloudtrail")
        ).all()
        data = [
            {
                "evidence_id": ev.id,
                "event_type": ev.event_type,
                "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
                "payload_sanitized": sanitize_untrusted_evidence(ev.raw_payload),
            } for ev in evidence
        ]
        return data, [ev.id for ev in evidence]

    @classmethod
    def _handle_read_config_snapshot(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        inc_id = args.get("incident_id")
        snap = db.scalars(
            select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == inc_id)
        ).first()
        if not snap:
            return {}, []
        data = {
            "snapshot_id": snap.id,
            "db_version": snap.db_version,
            "service_version": snap.service_version,
            "topology": snap.topology,
            "configuration": snap.configuration,
            "dependencies": snap.dependencies,
            "region": snap.region
        }
        return data, [snap.id]

    @classmethod
    def _handle_vector_search(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        inc_id = args.get("incident_id")
        limit = args.get("limit", 3)
        res = HistoricalRetrievalService.get_similar_incidents(db=db, incident_id=inc_id, limit=limit)
        return res.model_dump(), [c.incident_id for c in res.candidates]

    @classmethod
    def _handle_read_metrics(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        from app.services.verification.telemetry_reader import AWSVerificationTelemetryReader
        service = args.get("service", "auth-service")
        metric_name = args.get("metric_name", "ErrorRate")
        window_minutes = int(args.get("window_minutes", 15))
        threshold = float(args.get("threshold", 1.0))
        force_real = args.get("force_real_aws", False)

        sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(
            service_name=service,
            metric_name=metric_name,
            window_minutes=window_minutes,
            threshold=threshold,
            force_real_aws=force_real
        )
        if sig.status == "BLOCKED":
            raise RuntimeError(sig.error_message or "CloudWatch telemetry blocked")

        data = {
            "service": service,
            "metric_name": metric_name,
            "observed_value": sig.observed_value,
            "status": sig.status.value if hasattr(sig.status, "value") else str(sig.status),
            "expected_condition": sig.expected_condition,
            "observation_window": sig.observation_window,
            "verification_mode": sig.verification_mode,
            "independent_source": sig.source
        }
        return data, [sig.evidence_ref] if sig.evidence_ref else []

    @classmethod
    def _handle_read_security_group_state(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        from app.services.verification.telemetry_reader import AWSVerificationTelemetryReader
        target = args.get("security_group_id") or args.get("target") or "sg-012345"
        port = int(args.get("port", 22))
        cidr = str(args.get("cidr_block", "0.0.0.0/0"))
        force_real = args.get("force_real_aws", False)

        sig = AWSVerificationTelemetryReader.verify_security_group_state(
            target_resource=target,
            expected_revoked_port=port,
            expected_revoked_cidr=cidr,
            force_real_aws=force_real
        )
        if sig.status == "BLOCKED":
            raise RuntimeError(sig.error_message or "Security group readback blocked")

        data = {
            "target": target,
            "observed_value": sig.observed_value,
            "status": sig.status.value if hasattr(sig.status, "value") else str(sig.status),
            "expected_condition": sig.expected_condition,
            "verification_mode": sig.verification_mode,
            "independent_source": sig.source
        }
        return data, [sig.evidence_ref] if sig.evidence_ref else []

    @classmethod
    def _handle_change_security_rule(cls, args: Dict[str, Any], db: Session, req: MCPToolRequest):
        from app.services.execution.aws_executor import AWSActionExecutor
        target = args.get("security_group_id") or args.get("target") or "sg-012345"
        success, pre_st, post_st, req_id, summary, mode = AWSActionExecutor.execute_action(
            action_type="CHANGE_SECURITY_RULE",
            target_resource=target,
            parameters=args,
            idempotency_key=req.idempotency_key
        )
        if not success:
            raise RuntimeError(summary)
        return {
            "status": "SUCCESS",
            "execution_mode": mode,
            "pre_state": pre_st,
            "post_state": post_st,
            "summary": summary
        }, []
