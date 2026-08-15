from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_health_endpoint_reports_not_ready_in_foundation_phase():
    response = client.get("/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["capabilities"]["vision"]["ready"] is False
    assert body["capabilities"]["llm"]["ready"] is False
