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
