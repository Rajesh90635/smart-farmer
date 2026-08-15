def test_app_starts_and_exposes_openapi(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Smart Farmer API"


def test_health_endpoint_returns_healthy(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp_utc" in body
