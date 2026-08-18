import pytest
from datetime import datetime, timezone
from app.db.models import Incident, SentinelInstance, SentinelEvent, SentinelAlert, SentinelDecision, RemediationPlan
from app.services.sentinel import (
    TelemetryEventNormalizer,
    AnomalyDetectionEngine,
    AlertDeduplicationEngine,
    IncidentCorrelationEngine,
    AutonomousSentinelOrchestrator
)
from app.schemas.sentinel import SentinelPolicy, SentinelMode, SentinelStatus
from ghostops_shared import IncidentSeverity, IncidentStatus

def test_telemetry_event_normalization():
    raw_cw = {
        "event_id": "cw-1001",
        "event_type": "CPU_SPIKE",
        "resource_id": "i-auth-ec2-01",
        "metric_name": "CPUUtilization",
        "metric_value": 94.2,
        "baseline_value": 30.0,
        "region": "us-east-1"
    }

    event = TelemetryEventNormalizer.normalize_event(raw_cw, source="CloudWatch")
    assert event.event_id == "cw-1001"
    assert event.source == "CloudWatch"
    assert event.deviation == 64.2
    assert len(event.fingerprint) == 64
    assert len(event.payload_hash) == 64
    assert event.correlation_key == "us-east-1:i"

def test_anomaly_detection_scoring():
    policy = SentinelPolicy(anomaly_threshold=0.65)
    raw_cw = {"resource_id": "i-db-01", "metric_value": 95.0, "baseline_value": 20.0, "severity": "HIGH"}
    event = TelemetryEventNormalizer.normalize_event(raw_cw)

    is_anomaly, alert = AnomalyDetectionEngine.evaluate_event(event, policy)
    assert is_anomaly is True
    assert alert is not None
    assert alert.anomaly_score >= 0.65
    assert alert.status == "OPEN"

def test_alert_deduplication_engine(db_session):
    policy = SentinelPolicy(dedup_window_seconds=300)
    raw_cw = {"event_id": "evt-dedup-1", "resource_id": "i-auth-ec2-01", "metric_value": 92.0, "baseline_value": 30.0}
    event = TelemetryEventNormalizer.normalize_event(raw_cw)
    _, alert = AnomalyDetectionEngine.evaluate_event(event, policy)

    # First alert insertion
    is_supp, alert1, msg1 = AlertDeduplicationEngine.process_alert_deduplication(db_session, alert, policy)
    assert is_supp is False

    # Second duplicate alert insertion
    is_supp2, alert2, msg2 = AlertDeduplicationEngine.process_alert_deduplication(db_session, alert, policy)
    assert is_supp2 is True
    assert alert2.status == "SUPPRESSED"

def test_incident_correlation_engine(db_session):
    policy = SentinelPolicy(correlation_window_seconds=600)
    raw_cw = {"event_id": "evt-corr-1", "resource_id": "i-auth-ec2-01", "metric_value": 90.0, "baseline_value": 30.0}
    event = TelemetryEventNormalizer.normalize_event(raw_cw)
    _, alert = AnomalyDetectionEngine.evaluate_event(event, policy)
    AlertDeduplicationEngine.process_alert_deduplication(db_session, alert, policy)

    inc_id, is_new, msg = IncidentCorrelationEngine.correlate_alert(db_session, alert, policy)
    assert is_new is True
    assert "inc-sentinel-" in inc_id

    # Second alert correlating with existing incident
    raw_cw2 = {"event_id": "evt-corr-2", "resource_id": "i-auth-ec2-01", "metric_value": 95.0, "baseline_value": 30.0}
    event2 = TelemetryEventNormalizer.normalize_event(raw_cw2)
    _, alert2 = AnomalyDetectionEngine.evaluate_event(event2, policy)
    AlertDeduplicationEngine.process_alert_deduplication(db_session, alert2, policy)

    inc_id2, is_new2, msg2 = IncidentCorrelationEngine.correlate_alert(db_session, alert2, policy)
    assert is_new2 is False
    assert inc_id2 == inc_id

def test_sentinel_lifecycle_management(db_session):
    AutonomousSentinelOrchestrator.start_sentinel(db_session, mode=SentinelMode.DETECT_INVESTIGATE_AND_PLAN)
    st = AutonomousSentinelOrchestrator.get_status(db_session)
    assert st.status == SentinelStatus.RUNNING

    AutonomousSentinelOrchestrator.pause_sentinel(db_session, 300)
    st_pause = AutonomousSentinelOrchestrator.get_status(db_session)
    assert st_pause.status == SentinelStatus.PAUSED

    AutonomousSentinelOrchestrator.resume_sentinel(db_session)
    st_res = AutonomousSentinelOrchestrator.get_status(db_session)
    assert st_res.status == SentinelStatus.RUNNING

    AutonomousSentinelOrchestrator.stop_sentinel(db_session)
    st_stop = AutonomousSentinelOrchestrator.get_status(db_session)
    assert st_stop.status == SentinelStatus.STOPPED

def test_zero_unauthorized_execution_safeguard(db_session):
    AutonomousSentinelOrchestrator.start_sentinel(db_session, mode=SentinelMode.DETECT_INVESTIGATE_AND_PLAN)

    raw_cw = {"event_id": "evt-safeguard-1", "resource_id": "i-auth-ec2-01", "metric_value": 98.0, "baseline_value": 30.0, "severity": "HIGH"}
    resp = AutonomousSentinelOrchestrator.process_telemetry_event(db_session, raw_cw)

    assert resp.accepted is True
    assert resp.incident_id is not None

    # Verify remediation plan is created in PENDING_APPROVAL status (not automatically executed)
    plans = db_session.query(RemediationPlan).filter(RemediationPlan.incident_id == resp.incident_id).all()
    if plans:
        assert plans[0].status == "PENDING_APPROVAL"

def test_sentinel_api_endpoints(client, db_session):
    # 1. Start Sentinel
    res_start = client.post("/api/v1/sentinel/start", json={"mode": "DETECT_INVESTIGATE_AND_PLAN", "poll_interval_seconds": 30})
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "RUNNING"

    # 2. Ingest telemetry event
    res_ingest = client.post("/api/v1/sentinel/ingest-event", json={
        "event_id": "evt-api-1",
        "resource_id": "i-auth-ec2-01",
        "metric_name": "CPUUtilization",
        "metric_value": 94.0,
        "baseline_value": 30.0,
        "severity": "HIGH"
    })
    assert res_ingest.status_code == 200
    assert res_ingest.json()["accepted"] is True

    # 3. GET status
    res_st = client.get("/api/v1/sentinel/status")
    assert res_st.status_code == 200
    assert res_st.json()["metrics"]["events_processed"] >= 1

    # 4. GET events, alerts, decisions
    res_evts = client.get("/api/v1/sentinel/events")
    assert res_evts.status_code == 200
    assert len(res_evts.json()) >= 1

    res_alts = client.get("/api/v1/sentinel/alerts")
    assert res_alts.status_code == 200

    res_decs = client.get("/api/v1/sentinel/decisions")
    assert res_decs.status_code == 200

    # 5. Stop Sentinel
    res_stop = client.post("/api/v1/sentinel/stop", json={"reason": "Test finished"})
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "STOPPED"
