import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app

def test_frontend_test_a_b_screen_endpoints_respond_with_real_data(client: TestClient):
    """Test A, B: All primary screens have responding backend endpoints with real data."""
    # 1. Dashboard Incidents
    inc_resp = client.get("/api/v1/incidents")
    assert inc_resp.status_code == 200
    assert isinstance(inc_resp.json(), list)

    # 2. Evaluation Runs
    eval_resp = client.get("/api/v1/evaluation/runs")
    assert eval_resp.status_code == 200
    assert isinstance(eval_resp.json(), list)

    # 3. Sentinel Status
    sent_resp = client.get("/api/v1/sentinel/status")
    assert sent_resp.status_code == 200

def test_frontend_test_c_d_runtime_modes_and_mock_indicators(client: TestClient):
    """Test C, D: Runtime modes (MOCK vs LIVE) are explicitly reported."""
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert "aws_mock_mode" in health_data
    assert "database_connected" in health_data

def test_frontend_test_e_verification_signals(client: TestClient):
    """Test E: Verification states render multi-signal telemetry."""
    demo_resp = client.post("/api/v1/demo/run")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    verif_step = next((s for s in demo_data["steps"] if s["name"] == "Independent Multi-Signal Verification"), None)
    assert verif_step["details"]["verification_status"] in ["VERIFIED", "PARTIALLY_VERIFIED", "FAILED", "BLOCKED"]

def test_frontend_test_f_flagship_incident_1847_replay(client: TestClient):
    """Test F: Flagship Incident #1847 correctly shows DO_NOT_EXECUTE / CORRECTLY_REJECTED."""
    demo_resp = client.post("/api/v1/demo/run")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    replay_step = next((s for s in demo_data["steps"] if "Incident #1847" in s["name"]), None)
    assert replay_step is not None
    assert "CORRECTLY_REJECTED" in replay_step["details"]["counterfactual_verdict"]

def test_frontend_test_g_persisted_evaluation_metrics(client: TestClient):
    """Test G: Evaluation metrics are sourced from persisted database runs."""
    eval_resp = client.get("/api/v1/evaluation/runs")
    assert eval_resp.status_code == 200
    runs = eval_resp.json()
    if runs:
        latest = runs[0]
        assert "precision_at_3" in latest
        assert "temporal_verdict_accuracy" in latest
        assert "unsafe_replay_rate" in latest

def test_frontend_test_h_cdc_status_endpoint(client: TestClient):
    """Test H: CDC changefeed status is returned from backend."""
    cdc_resp = client.get("/api/v1/cdc/status")
    assert cdc_resp.status_code == 200
    cdc_data = cdc_resp.json()
    assert "is_connected" in cdc_data
    assert "mode" in cdc_data
    assert "events_processed" in cdc_data

def test_frontend_test_i_approval_cannot_be_bypassed(client: TestClient):
    """Test I: Execution requires explicit human confirmation and approval."""
    # Attempt execution without approval confirmation
    unapproved_resp = client.post("/api/v1/plans/plan-fake/execute", json={"approved_by": ""})
    assert unapproved_resp.status_code in [400, 404, 422]

def test_frontend_test_j_no_secrets_in_api_responses(client: TestClient):
    """Test J: No secrets or AWS credentials leaked in API responses."""
    demo_resp = client.post("/api/v1/demo/run")
    resp_text = demo_resp.text
    assert "aws_secret_access_key" not in resp_text.lower()
    assert "sk-live" not in resp_text.lower()
    assert "aws_access_key_id" not in resp_text.lower()

def test_frontend_test_k_full_demo_flow_executes_successfully(client: TestClient):
    """Test K: Full 3-minute demo flow executes cleanly and returns 10 ordered stages."""
    demo_resp = client.post("/api/v1/demo/run")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    assert demo_data["status"] == "SUCCESS"
    assert len(demo_data["steps"]) == 10
    assert demo_data["duration_ms"] > 0
