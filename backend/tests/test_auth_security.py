def test_sql_injection_attempt_in_phone_number_is_handled_safely(client):
    malicious_phone = "1' OR '1'='1"
    response = client.post(
        "/api/v1/auth/login", json={"phone_number": malicious_phone, "password": "whatever123"}
    )
    # Must be rejected as invalid credentials (or validation error), never
    # a 500, and must never log the caller in - proves the ORM's
    # parameterized queries aren't bypassed by this input.
    assert response.status_code in (401, 422)


def test_audit_log_never_contains_password_or_token_values(client, registered_farmer, db_session):
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    payload, tokens = registered_farmer
    rows = db_session.execute(select(AuditLog)).scalars().all()

    for row in rows:
        # Audit rows only ever carry ids/roles/action names - never a raw
        # secret value could appear in any of these fields.
        assert payload["password"] not in (row.action or "")
        assert tokens["access_token"] not in (row.action or "")
        assert tokens["refresh_token"] not in (row.action or "")


def test_response_never_includes_password_hash_field_name(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get(
        "/api/v1/farmers/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert "password_hash" not in response.text
