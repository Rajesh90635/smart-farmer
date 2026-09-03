def test_refresh_issues_new_tokens(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_tokens = response.json()
    # The refresh token MUST rotate (this is the actual security property -
    # a used refresh token must never be reusable). The access token is not
    # required to differ - two access tokens issued within the same second
    # for the same user/role are legitimately identical JWTs (same claims,
    # same signature), which is not a security issue since either is a
    # valid, independently-expiring credential.
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert "access_token" in new_tokens


def test_refresh_token_is_single_use_rotation(client, registered_farmer):
    _, tokens = registered_farmer
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200

    # Reusing the same (now-rotated/revoked) refresh token must fail.
    second = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert second.status_code == 401
    assert second.json()["error"]["code"] == "SESSION_EXPIRED"


def test_refresh_with_garbage_token_is_rejected(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_logout_revokes_the_session(client, registered_farmer):
    _, tokens = registered_farmer
    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 401


def test_logout_requires_authentication(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_logout_cannot_revoke_another_users_session(client, registered_farmer):
    _, tokens_a = registered_farmer

    from tests.factories import valid_register_payload as make_payload

    # Register a second, independent farmer.
    import uuid as uuid_mod

    other_payload = {
        "phone_number": "9" + str(uuid_mod.uuid4().int)[:9],
        "password": "Str0ngPass!",
        "full_name": "Other Farmer",
        "preferred_language_code": "en",
        "consents": [
            {"consent_type": "terms_of_service", "version": "1.0"},
            {"consent_type": "privacy_policy", "version": "1.0"},
        ],
    }
    reg_b = client.post("/api/v1/auth/register", json=other_payload)
    tokens_b = reg_b.json()

    # Farmer B tries to log out using Farmer A's refresh token.
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens_a["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert response.status_code == 401

    # Farmer A's session must still be valid afterward.
    still_valid = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens_a["refresh_token"]})
    assert still_valid.status_code == 200
