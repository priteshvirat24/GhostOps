import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models import Incident, InfrastructureSnapshot, IncidentEvidence, OperationalActionHistory, InstitutionalMemoryVector
from app.agents.mcp.server import GhostOpsMCPServer
from app.agents.mcp.contracts import MCPToolRequest
from app.integrations.cockroach.ccloud_sandbox import CockroachCloudSandboxManager
from app.services.cdc.memory_bus import CDCMemoryBus
from app.services.evaluation.harness import AgentEvaluationHarness
from app.agents.model_provider import get_model_provider
from app.agents.specialists.execution import ExecutionAgent
from app.agents.specialists.verification import VerificationAgent

def test_mcp_server_catalog_and_read_only_tool(db_session: Session):
    """Test §9.2 & §19.3: Managed MCP Server tool surface & read-only execution."""
    tools = GhostOpsMCPServer.list_tools()
    assert len(tools) >= 10
    tool_names = [t.name for t in tools]
    assert "read_cloudwatch" in tool_names
    assert "vector_search" in tool_names
    assert "sandbox_execute" in tool_names
    assert "ccloud_cli" in tool_names

    # Create dummy incident
    now = datetime.now(timezone.utc)
    inc = Incident(title="MCP Test Incident", description="Desc", service="auth-service", region="us-east-1", start_time=now)
    db_session.add(inc)
    db_session.commit()

    # Call read_cloudwatch tool via MCP
    req = MCPToolRequest(
        tool_name="read_cloudwatch",
        arguments={"incident_id": inc.id},
        agent_id="HistorianAgent",
        incident_id=inc.id,
        idempotency_key=f"mcp-test-cw-{inc.id}"
    )
    resp = GhostOpsMCPServer.execute_tool(req, db_session)
    assert resp.success is True
    assert resp.tool_name == "read_cloudwatch"

def test_ccloud_sandbox_dry_run_and_rejection():
    """Test §13, §17 & §19.4: ccloud ephemeral sandbox provisioning & unsafe command rejection."""
    sandbox_ctx = CockroachCloudSandboxManager.provision_ephemeral_sandbox()
    assert sandbox_ctx["status"] == "PROVISIONED"

    # Test safe command dry run on v24.1
    safe_res = CockroachCloudSandboxManager.execute_dry_run(
        sandbox_ctx,
        command="ec2:RevokeSecurityGroupIngress",
        target_schema_version="v24.1.0"
    )
    assert safe_res["dry_run_success"] is True
    assert safe_res["verification_signal"] == "PASSED"

    # Test unsafe leaseholder command on v26.0 (Flagship rejected replay case)
    unsafe_res = CockroachCloudSandboxManager.execute_dry_run(
        sandbox_ctx,
        command="reset_leaseholder --cluster=crdb-prod",
        target_schema_version="v26.0.0"
    )
    assert unsafe_res["dry_run_success"] is False
    assert unsafe_res["verification_signal"] == "REJECTED_UNSAFE_PATTERN"
    assert len(unsafe_res["risk_flags"]) > 0

    teardown_ok = CockroachCloudSandboxManager.teardown_sandbox(sandbox_ctx)
    assert teardown_ok is True

def test_cdc_memory_bus_trust_propagation(db_session: Session):
    """Test §19.2 & §20: Changefeed (CDC) stream trust-score delta propagation."""
    now = datetime.now(timezone.utc)
    inc = Incident(title="CDC Test", description="Desc", service="auth-service", region="us-east-1", start_time=now)
    db_session.add(inc)
    db_session.commit()

    mem = InstitutionalMemoryVector(
        title="CDC Memory",
        content="Test content",
        incident_id=inc.id,
        embedding=[0.1] * 1536,
        confidence=0.80
    )
    db_session.add(mem)
    db_session.commit()

    # Emit simulated CDC event
    cdc_event = {
        "table": "remediation_outcomes",
        "op": "INSERT",
        "row": {
            "incident_id": inc.id,
            "execution_status": "SUCCESS",
            "rollback_successful": False,
            "effectiveness_score": 0.95
        }
    }
    result = CDCMemoryBus.handle_changefeed_event(cdc_event, db_session)
    assert result["status"] == "PROCESSED"
    assert result["propagated_trust_delta"] > 0

    # Verify memory confidence increased
    db_session.refresh(mem)
    assert mem.confidence > 0.80
    assert mem.usage_count == 1
    assert mem.successful_usage_count == 1

def test_agent_evaluation_golden_dataset(db_session: Session):
    """Test §9.5: Agent Evaluation Harness against golden benchmark dataset."""
    bench = AgentEvaluationHarness.run_benchmark(db_session, split="development")
    assert bench["total_cases"] == 10
    assert bench["dataset_version"] == "ghostops-golden-v2"
    assert bench["corpus_version"] == "ghostops-history-v1"
    assert bench["temporal_verdict_accuracy"] >= 0.85
    assert bench["unsafe_replay_rate"] == 0.0
    assert bench["false_execution_rate"] == 0.0
    assert bench["regression_gate_passed"] is True
    assert bench["status"] == "COMPLETED"

def test_bedrock_multi_tier_routing():
    """Test §9.3 & §22: Amazon Bedrock multi-tier model routing."""
    provider = get_model_provider()

    fast_out = provider.generate_completion("Triage event", tier="fast")
    assert "Classification:" in fast_out

    reason_out = provider.generate_completion("Reason step by step", tier="reasoning")
    assert "GhostOps Analysis Summary & Step-by-Step Reasoning:" in reason_out

    vec = provider.generate_embedding("Test text")
    assert len(vec) == 1536

def test_saga_execution_and_rollback(db_session: Session):
    """Test §14: Saga-based execution with forward tool calls and compensating rollback on failure."""
    now = datetime.now(timezone.utc)
    inc = Incident(title="Saga Test", description="Desc", service="auth-service", region="us-east-1", start_time=now)
    db_session.add(inc)
    db_session.commit()

    steps = [
        {
            "action_type": "drain_alb_target",
            "target_resource_arn": "arn:aws:elasticloadbalancing:tg/auth",
            "parameters": {"target": "i-auth-01"},
            "rollback_parameters": {"action": "undrain_alb_target", "target": "i-auth-01"},
            "risk_level": "L2"
        },
        {
            "action_type": "restart_ecs_task",
            "target_resource_arn": "arn:aws:ecs:task/auth-01",
            "parameters": {"task": "auth-01"},
            "rollback_parameters": {},
            "risk_level": "L2"
        }
    ]

    res = ExecutionAgent.execute_saga(db_session, inc.id, steps)
    assert res["status"] == "SUCCESS"
    assert res["executed_steps_count"] == 2

def test_independent_verification_agent(db_session: Session):
    """Test §16: Independent Verification Agent signal checks."""
    from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
    StatefulMockInfrastructure.apply_mutation("sg-012345", "CHANGE_SECURITY_RULE", {"security_group_id": "sg-012345", "port": 22, "cidr_block": "0.0.0.0/0"})

    now = datetime.now(timezone.utc)
    inc = Incident(title="Verify Test", description="Desc", service="auth-service", region="us-east-1", start_time=now)
    db_session.add(inc)
    db_session.commit()

    v_res = VerificationAgent.verify_outcome(db_session, inc.id, "plan-101", "exec-101", mock_metric_value=0.20)
    assert str(v_res.overall_status).lower() in ["verified", "provisionally_successful", "verificationstatus.verified"]
    assert "application_error_rate" in v_res.signal_results
    assert "p99_latency_recovery" in v_res.signal_results
    assert v_res.trust_delta > 0
