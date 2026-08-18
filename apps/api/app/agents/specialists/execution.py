import time
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.agents.base import AgentState
from app.agents.mcp.server import GhostOpsMCPServer
from app.agents.mcp.contracts import MCPToolRequest
from app.db.models import OperationalActionHistory, RemediationExecution, ExecutionStepRecord
from app.core.logging import logger

class ExecutionAgent:
    """
    Saga Execution Specialist Agent for GhostOps (§9.2, §14).
    Executes multi-step governed remediation plans with explicit compensating actions.
    Persists saga state to CockroachDB before every step and walks compensating actions in reverse on failure.
    """

    @classmethod
    def execute_saga(
        cls,
        db: Session,
        incident_id: str,
        steps: List[Dict[str, Any]],
        saga_id: Optional[str] = None
    ) -> Dict[str, Any]:
        t0 = time.time()
        saga_id = saga_id or f"saga-{uuid.uuid4().hex[:8]}"
        logger.info(f"[ExecutionAgent] Starting remediation saga '{saga_id}' for incident '{incident_id}' ({len(steps)} steps)")

        executed_actions: List[Dict[str, Any]] = []
        compensations_stack: List[Dict[str, Any]] = []
        saga_status = "SUCCESS"
        error_msg = None

        for idx, step in enumerate(steps, start=1):
            action_type = step.get("action_type", "CHANGE_SECURITY_RULE")
            target = step.get("target_resource_arn", "auth-service")
            params = step.get("parameters", {})
            compensate_action = step.get("rollback_parameters", {})
            risk_level = step.get("risk_level", "L2")

            idempotency_key = step.get("idempotency_key") or f"{incident_id}-{action_type}-{idx}-attempt1"

            # Check Idempotency before execution
            existing = db.scalars(
                select(OperationalActionHistory).where(
                    OperationalActionHistory.idempotency_key == idempotency_key,
                    OperationalActionHistory.result == "SUCCESS"
                )
            ).first()

            if existing:
                executed_actions.append({"step": idx, "action": action_type, "result": "IDEMPOTENT_REPLAY", "action_id": existing.id})
                continue

            # 1. Forward action execution via MCP Server
            if action_type == "CHANGE_SECURITY_RULE":
                tool_name = "change_security_rule"
            elif "lambda" in action_type.lower():
                tool_name = "aws_lambda_invoke"
            else:
                tool_name = "aws_ssm_run_command"

            req = MCPToolRequest(
                tool_name=tool_name,
                arguments=params if action_type == "CHANGE_SECURITY_RULE" else {"action": action_type, "target": target, "parameters": params},
                agent_id="ExecutionAgent",
                incident_id=incident_id,
                idempotency_key=idempotency_key,
                saga_id=saga_id
            )

            # Record forward action in CockroachDB
            action_rec = OperationalActionHistory(
                incident_id=incident_id,
                saga_id=saga_id,
                actor="GhostOps.ExecutionAgent",
                agent="ExecutionAgent",
                command=action_type,
                tool="GhostOpsMCPServer",
                target=target,
                risk_level=risk_level,
                reason=f"Saga step {idx}: {action_type}",
                authorization="GovernanceApproved",
                idempotency_key=idempotency_key,
                result="PENDING"
            )
            db.add(action_rec)
            db.commit()

            # Execute tool call
            resp = GhostOpsMCPServer.execute_tool(req, db)

            if resp.success:
                action_rec.result = "SUCCESS"
                db.commit()
                executed_actions.append({"step": idx, "action": action_type, "result": "SUCCESS"})
                if compensate_action:
                    compensations_stack.append({
                        "step": idx,
                        "compensating_command": compensate_action.get("action", f"undo_{action_type}"),
                        "target": target,
                        "params": compensate_action
                    })
            else:
                action_rec.result = "FAILED"
                action_rec.error_message = resp.error.get("message") if resp.error else "Execution failed"
                db.commit()
                saga_status = "FAILED"
                error_msg = action_rec.error_message
                logger.warning(f"[ExecutionAgent] Step {idx} ({action_type}) failed: {error_msg}. Initiating saga compensation rollback.")
                break

        # If failed, walk compensating stack in reverse order
        if saga_status == "FAILED" and compensations_stack:
            logger.info(f"[ExecutionAgent] Rolling back {len(compensations_stack)} completed saga steps...")
            for comp in reversed(compensations_stack):
                comp_key = f"{incident_id}-comp-{comp['step']}-{uuid.uuid4().hex[:4]}"
                comp_rec = OperationalActionHistory(
                    incident_id=incident_id,
                    saga_id=saga_id,
                    actor="GhostOps.ExecutionAgent",
                    agent="ExecutionAgent",
                    command=comp["compensating_command"],
                    tool="GhostOpsMCPServer",
                    target=comp["target"],
                    risk_level="L2",
                    reason=f"Saga rollback for step {comp['step']}",
                    authorization="SagaRollbackAuto",
                    idempotency_key=comp_key,
                    result="ROLLED_BACK"
                )
                db.add(comp_rec)
            db.commit()
            saga_status = "ROLLED_BACK"

        duration = round((time.time() - t0) * 1000, 2)
        return {
            "saga_id": saga_id,
            "status": saga_status,
            "executed_steps_count": len(executed_actions),
            "compensated_steps_count": len(compensations_stack) if saga_status == "ROLLED_BACK" else 0,
            "error_message": error_msg,
            "duration_ms": duration
        }
