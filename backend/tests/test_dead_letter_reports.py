"""D87-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from tests.conftest import auth_headers


def _report(client, tokens, client_upload_id="upload-1", reason="retries exhausted"):
    return client.post(
        "/api/v1/crop-photos/dead-letter-report",
        json={"client_upload_id": client_upload_id, "reason": reason},
        headers=auth_headers(tokens),
    )


def test_farmer_can_report_a_dead_lettered_upload(client, registered_farmer):
    _, tokens = registered_farmer
    response = _report(client, tokens)
    assert response.status_code == 201
    body = response.json()
    assert body["client_upload_id"] == "upload-1"
    assert body["reason"] == "retries exhausted"
    assert body["reported_at"] is not None


def test_only_admin_can_read_the_report_list(client, registered_farmer, admin_tokens):
    _, tokens = registered_farmer
    _report(client, tokens, client_upload_id="upload-admin-visibility")

    farmer_attempt = client.get("/api/v1/admin/dead-letter-reports", headers=auth_headers(tokens))
    assert farmer_attempt.status_code == 403

    admin_response = client.get("/api/v1/admin/dead-letter-reports", headers=auth_headers(admin_tokens))
    assert admin_response.status_code == 200
    assert any(r["client_upload_id"] == "upload-admin-visibility" for r in admin_response.json()["items"])


def test_unauthenticated_report_is_rejected(client):
    response = client.post(
        "/api/v1/crop-photos/dead-letter-report", json={"client_upload_id": "upload-1", "reason": "test"}
    )
    assert response.status_code == 401
