def _auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_change_password_with_correct_current_password_succeeds(client, registered_farmer):
    payload, tokens = registered_farmer
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": payload["password"], "new_password": "NewPass1!"},
        headers=_auth_headers(tokens),
    )
    assert response.status_code == 204

    login = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": "NewPass1!"}
    )
    assert login.status_code == 200


def test_change_password_with_wrong_current_password_is_rejected(client, registered_farmer):
    payload, tokens = registered_farmer
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPass1", "new_password": "NewPass1!"},
        headers=_auth_headers(tokens),
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INCORRECT_CURRENT_PASSWORD"

    login = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert login.status_code == 200


def test_change_password_rejects_weak_new_password(client, registered_farmer):
    payload, tokens = registered_farmer
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": payload["password"], "new_password": "short"},
        headers=_auth_headers(tokens),
    )
    assert response.status_code == 422


def test_change_password_requires_authentication(client):
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Whatever1", "new_password": "NewPass1!"},
    )
    assert response.status_code == 401
