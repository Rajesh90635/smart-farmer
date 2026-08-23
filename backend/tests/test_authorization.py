def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/farmers/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_authenticated_farmer_can_access_own_profile(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/farmers/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200


def test_malformed_bearer_token_is_rejected(client):
    response = client.get("/api/v1/farmers/me", headers={"Authorization": "Bearer garbage-not-a-jwt"})
    assert response.status_code == 401


def test_wrong_role_is_forbidden(client, registered_farmer):
    from app.core.jwt import create_access_token

    _, tokens = registered_farmer
    from app.core.jwt import decode_access_token

    user_id = decode_access_token(tokens["access_token"])["sub"]

    # A token for the same user but a different role must not pass the
    # farmer-only role gate.
    wrong_role_token = create_access_token(subject=user_id, role="dealer")
    response = client.get("/api/v1/farmers/me", headers={"Authorization": f"Bearer {wrong_role_token}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
