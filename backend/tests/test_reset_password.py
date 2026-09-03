def test_reset_password_with_existing_phone_number_succeeds(client, registered_farmer):
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": payload["phone_number"], "new_password": "NewPass1!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body

    login_new = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": "NewPass1!"}
    )
    assert login_new.status_code == 200

    login_old = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert login_old.status_code == 401


def test_reset_password_for_nonexistent_account_is_rejected(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": "9000000001", "new_password": "NewPass1!"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_reset_password_rejects_weak_password(client, registered_farmer):
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": payload["phone_number"], "new_password": "short"},
    )
    assert response.status_code == 422


def test_reset_password_rejects_invalid_phone_number(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": "not-a-phone", "new_password": "NewPass1!"},
    )
    assert response.status_code == 422
