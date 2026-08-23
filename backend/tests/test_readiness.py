def test_ready_endpoint_reports_ready_when_database_is_reachable(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
