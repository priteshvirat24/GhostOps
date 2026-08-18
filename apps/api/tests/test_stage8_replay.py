import pytest
from datetime import datetime, timezone, timedelta
from app.db.models import (
    Incident,
    InfrastructureSnapshot,
    OperationalActionHistory,
    RemediationExecution,
    InstitutionalMemoryVector,
    ReplayRun,
    MemoryRegressionRecord,
    SimulationMutationRecord
)
from app.services.replay import (
    SimulationEnvironment,
    SimulationActionExecutor,
    HistoricalScenarioReconstructor,
    MemoryRegressionDetector,
    GhostReplayEngine,
    InfrastructureChangefeedMonitor,
    ReplayScheduler
)
from app.schemas.ghost_replay import ReplayMode
from ghostops_shared import IncidentSeverity, TrustLevel

def test_historical_scenario_reconstruction(db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-recon-1", title="Recon Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)

    snap = InfrastructureSnapshot(incident_id=inc.id, snapshot_timestamp=now_time, db_version="CockroachDB v23.2.3", service_version="v4.2.0")
    act = OperationalActionHistory(incident_id=inc.id, actor="Ops", command="test", tool="tool", target="target", reason="reason", idempotency_key="k-recon", result="SUCCESS", timestamp=now_time)
    exec_rec = RemediationExecution(id="exec-recon-1", plan_id="p-1", plan_version=1, incident_id=inc.id, status="COMPLETED", started_at=now_time, trace_id="t-recon")
    
    db_session.add_all([snap, act, exec_rec])
    db_session.commit()

    scen = HistoricalScenarioReconstructor.reconstruct_scenario(db_session, inc.id, "r-recon-1")
    assert scen.source_incident_id == inc.id
    assert scen.completeness_score >= 0.85
    assert scen.infrastructure_state["service"] == "auth-service"

def test_simulation_state_isolation():
    env = SimulationEnvironment({"i-ec2-01": {"connection_pool_max": 50}})
    pre_st = env.get_resource_state("i-ec2-01")
    assert pre_st["connection_pool_max"] == 50

    mut, ok, summary = SimulationActionExecutor.execute_simulated_action(
        env, "r-iso-1", "i-ec2-01", "ADJUST_CONNECTION_POOL", {"max_connections": 150}
    )

    assert mut.simulated_only is True
    assert mut.post_state["connection_pool_max"] == 150
    # Original baseline call in new env should be isolated
    new_env = SimulationEnvironment({"i-ec2-01": {"connection_pool_max": 50}})
    assert new_env.get_resource_state("i-ec2-01")["connection_pool_max"] == 50

def test_deterministic_ghost_replay(db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-deter-1", title="Deter Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    run1 = GhostReplayEngine.run_replay(db_session, inc.id, deterministic_seed=42)
    score1 = run1.replay_score

    run2 = GhostReplayEngine.run_replay(db_session, inc.id, deterministic_seed=42)
    score2 = run2.replay_score

    assert score1 == score2
    assert run1.predicted_outcome == run2.predicted_outcome

def test_counterfactual_simulation(db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-cf-1", title="CF Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    cf_params = {"service_version": "v4.3.0", "connection_pool_max": 200}
    run = GhostReplayEngine.run_replay(db_session, inc.id, mode=ReplayMode.COUNTERFACTUAL_REPLAY, counterfactual_params=cf_params)

    assert run.mode == ReplayMode.COUNTERFACTUAL_REPLAY
    assert run.status == "COMPLETED"
    assert len(run.scenarios) == 1
    assert run.scenarios[0].infrastructure_state["service_version"] == "v4.3.0"

def test_memory_regression_detection(db_session):
    mem = InstitutionalMemoryVector(
        id="mem-reg-1", title="Test Memory", content="Content", memory_type="remediation",
        embedding=[0.1]*1536, confidence=0.90, memory_status="ACTIVE"
    )
    db_session.add(mem)
    db_session.commit()

    reg = MemoryRegressionDetector.evaluate_memory_regressions(
        db_session, "r-reg-1", mem.id, historical_score=0.90, observed_score=0.65
    )

    assert reg is not None
    assert reg.score_delta == -0.25
    assert reg.severity in ["HIGH", "CRITICAL"]
    assert reg.status == "DETECTED"

def test_changefeed_monitor_and_replay_scheduler(db_session):
    ReplayScheduler.clear_queue()

    mem = InstitutionalMemoryVector(id="mem-cf-1", title="T", content="C", memory_type="r", embedding=[0.1]*1536, confidence=0.8)
    db_session.add(mem)
    db_session.commit()

    res = InfrastructureChangefeedMonitor.process_change_event(
        db_session, "CONFIGURATION_CHANGED", "i-auth-ec2", {"incident_id": "inc-cf-test", "version": "v4.3.0"}
    )

    assert res["status"] == "QUEUED"
    job_id = res["enqueued_job_id"]

    # Test deduplication
    job_id_dup = ReplayScheduler.enqueue_replay(
        incident_id="inc-cf-test", mode="INFRASTRUCTURE_DRIFT_SIMULATION", counterfactual_params={"incident_id": "inc-cf-test", "version": "v4.3.0"}
    )
    assert job_id == job_id_dup

def test_replay_api_endpoints(client, db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-api-rplay", title="API Rplay Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    # 1. Trigger incident replay
    res1 = client.post(f"/api/v1/replay/incidents/{inc.id}", json={"mode": "HISTORICAL_REPLAY", "deterministic_seed": 42})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "COMPLETED"
    assert data1["score"]["overall_score"] >= 0.70

    replay_id = data1["replay_id"]

    # 2. GET replay detail
    res_detail = client.get(f"/api/v1/replay/{replay_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["replay_id"] == replay_id

    # 3. GET replay steps
    res_steps = client.get(f"/api/v1/replay/{replay_id}/steps")
    assert res_steps.status_code == 200
    assert len(res_steps.json()) >= 1

    # 4. GET replay provenance
    res_prov = client.get(f"/api/v1/replay/{replay_id}/provenance")
    assert res_prov.status_code == 200
    assert res_prov.json()["replay_id"] == replay_id

    # 5. GET regressions
    res_reg = client.get("/api/v1/replay/regressions")
    assert res_reg.status_code == 200

    # 6. GET replay queue
    res_q = client.get("/api/v1/replay/queue")
    assert res_q.status_code == 200
    assert res_q.json()["total_replays"] >= 1
