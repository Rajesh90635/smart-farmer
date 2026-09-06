def _auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_valid_login_returns_tokens(client, registered_farmer):
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_with_wrong_password_is_rejected(client, registered_farmer):
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": "WrongPass1"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_with_nonexistent_account_gives_same_generic_error(client):
    response = client.post("/api/v1/auth/login", json={"phone_number": "9000000000", "password": "WhoKnows1"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    # Message must not reveal whether the account exists.
    assert "does not exist" not in response.json()["error"]["message"].lower()


def test_disabled_account_cannot_login(client, registered_farmer, db_session):
    import uuid

    payload, tokens = registered_farmer
    from app.core.jwt import decode_access_token
    from app.models.user import AccountStatus, User

    user_id = uuid.UUID(decode_access_token(tokens["access_token"])["sub"])
    user = db_session.get(User, user_id)
    user.status = AccountStatus.SUSPENDED
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_repeated_failed_logins_are_rate_limited(client, registered_farmer):
    payload, _ = registered_farmer
    last_response = None
    for _ in range(7):
        last_response = client.post(
            "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": "WrongPass1"}
        )
    assert last_response.status_code == 429
    assert last_response.json()["error"]["code"] == "RATE_LIMITED"


def test_login_returns_admin_role_when_admin_role_is_assigned(client, registered_farmer, db_session):
    """The exact scenario scripts/create_admin.py exists for: an account
    provisioned with the admin role must authenticate as admin through
    the real POST /auth/login endpoint, not silently as farmer."""
    import uuid

    from app.core.jwt import decode_access_token
    from app.repositories import user_repository

    payload, tokens = registered_farmer
    user_id = uuid.UUID(decode_access_token(tokens["access_token"])["sub"])
    admin_role = user_repository.get_role_by_code(db_session, "admin")
    user_repository.assign_role(db_session, user_id, admin_role.id)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"])["role"] == "admin"


def test_login_role_resolution_is_deterministic_for_multi_role_accounts(client, registered_farmer, db_session):
    """Without a deterministic order, the role claim for a multi-role,
    non-admin account would depend on arbitrary DB row order. Assigning
    a second role after registration's FARMER assignment must still
    resolve to the FIRST assigned role (farmer), never flip depending on
    query-plan order."""
    import uuid

    from app.core.jwt import decode_access_token
    from app.repositories import user_repository

    payload, tokens = registered_farmer
    user_id = uuid.UUID(decode_access_token(tokens["access_token"])["sub"])
    expert_role = user_repository.get_role_by_code(db_session, "expert")
    user_repository.assign_role(db_session, user_id, expert_role.id)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"])["role"] == "farmer"


def test_login_from_a_new_device_notifies_the_farmer(client, registered_farmer):
    """D78-13 (docs/audit/FINAL_CANONICAL_group_D.md): the new-device-login
    half of this scenario, previously disclosed as unbuilt (no device
    identifier existed anywhere in this codebase)."""
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/login",
        json={"phone_number": payload["phone_number"], "password": payload["password"], "device_id": "device-alpha"},
    )
    assert response.status_code == 200
    tokens = response.json()
    notifications = client.get("/api/v1/notifications", headers=_auth_headers(tokens)).json()["items"]
    security_alerts = [n for n in notifications if n["category"] == "security_alert"]
    assert len(security_alerts) == 1


def test_repeated_login_from_the_same_known_device_does_not_re_notify(client, registered_farmer):
    payload, _ = registered_farmer
    client.post(
        "/api/v1/auth/login",
        json={"phone_number": payload["phone_number"], "password": payload["password"], "device_id": "device-alpha"},
    )
    second = client.post(
        "/api/v1/auth/login",
        json={"phone_number": payload["phone_number"], "password": payload["password"], "device_id": "device-alpha"},
    ).json()
    notifications = client.get("/api/v1/notifications", headers=_auth_headers(second)).json()["items"]
    security_alerts = [n for n in notifications if n["category"] == "security_alert"]
    assert len(security_alerts) == 1  # only the first login's alert, never a duplicate for the same device


def test_login_from_a_second_distinct_device_notifies_again(client, registered_farmer):
    payload, _ = registered_farmer
    client.post(
        "/api/v1/auth/login",
        json={"phone_number": payload["phone_number"], "password": payload["password"], "device_id": "device-alpha"},
    )
    second = client.post(
        "/api/v1/auth/login",
        json={"phone_number": payload["phone_number"], "password": payload["password"], "device_id": "device-beta"},
    ).json()
    notifications = client.get("/api/v1/notifications", headers=_auth_headers(second)).json()["items"]
    security_alerts = [n for n in notifications if n["category"] == "security_alert"]
    assert len(security_alerts) == 2  # one per distinct device this farmer has ever logged in from


def test_login_without_a_device_id_does_not_trigger_new_device_detection(client, registered_farmer):
    """No device_id sent (older client) means honestly "cannot determine" -
    see auth_service.login() - never fabricated as new or as known."""
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    ).json()
    notifications = client.get("/api/v1/notifications", headers=_auth_headers(response)).json()["items"]
    security_alerts = [n for n in notifications if n["category"] == "security_alert"]
    assert security_alerts == []
