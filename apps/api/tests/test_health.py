from unittest.mock import patch

def test_root_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ghostops-api"

@patch("app.services.health.check_db_health", return_value=True)
def test_v1_health(mock_check_db, client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "aws_mock_mode" in data
    assert data["aws_mock_mode"] is True
