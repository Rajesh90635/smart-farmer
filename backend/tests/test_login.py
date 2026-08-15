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
