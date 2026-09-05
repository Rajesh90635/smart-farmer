from tests.conftest import override_sms_provider
from tests.fake_sms_provider import FakeSmsOtpProvider


def test_reset_password_with_valid_otp_succeeds(client, registered_farmer):
    payload, _ = registered_farmer
    fake = FakeSmsOtpProvider(valid_code="654321")
    with override_sms_provider(fake):
        otp_response = client.post(
            "/api/v1/auth/reset-password/request-otp", json={"phone_number": payload["phone_number"]}
        )
        assert otp_response.status_code == 204
        assert fake.sent_to == [f"+91{payload['phone_number']}"]

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"phone_number": payload["phone_number"], "new_password": "NewPass1!", "otp_code": "654321"},
        )
    assert response.status_code == 200, response.text
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


def test_reset_password_rejects_wrong_otp(client, registered_farmer):
    payload, _ = registered_farmer
    fake = FakeSmsOtpProvider(valid_code="654321")
    with override_sms_provider(fake):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"phone_number": payload["phone_number"], "new_password": "NewPass1!", "otp_code": "000000"},
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_OTP"

    # The password must be genuinely unchanged - not just an error response.
    login_old = client.post(
        "/api/v1/auth/login", json={"phone_number": payload["phone_number"], "password": payload["password"]}
    )
    assert login_old.status_code == 200


def test_reset_password_fails_closed_when_no_sms_provider_is_configured(client, registered_farmer):
    """No override active here - production default (NotConfiguredSmsOtpProvider)
    applies. Must refuse the reset entirely, never silently skip verification
    the way the old no-OTP behavior did."""
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": payload["phone_number"], "new_password": "NewPass1!", "otp_code": "123456"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OTP_DELIVERY_FAILED"


def test_request_otp_for_nonexistent_account_is_rejected(client):
    fake = FakeSmsOtpProvider()
    with override_sms_provider(fake):
        response = client.post(
            "/api/v1/auth/reset-password/request-otp", json={"phone_number": "9000000001"}
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert fake.sent_to == []  # never pay for an SMS to a number with no account


def test_request_otp_is_rate_limited(client, registered_farmer):
    payload, _ = registered_farmer
    fake = FakeSmsOtpProvider()
    with override_sms_provider(fake):
        for _ in range(3):
            assert client.post(
                "/api/v1/auth/reset-password/request-otp", json={"phone_number": payload["phone_number"]}
            ).status_code == 204
        limited = client.post(
            "/api/v1/auth/reset-password/request-otp", json={"phone_number": payload["phone_number"]}
        )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


def test_reset_password_for_nonexistent_account_is_rejected(client):
    fake = FakeSmsOtpProvider(valid_code="654321")
    with override_sms_provider(fake):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"phone_number": "9000000001", "new_password": "NewPass1!", "otp_code": "654321"},
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_reset_password_rejects_weak_password(client, registered_farmer):
    payload, _ = registered_farmer
    fake = FakeSmsOtpProvider(valid_code="654321")
    with override_sms_provider(fake):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"phone_number": payload["phone_number"], "new_password": "short", "otp_code": "654321"},
        )
    assert response.status_code == 422


def test_reset_password_rejects_invalid_phone_number(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": "not-a-phone", "new_password": "NewPass1!", "otp_code": "654321"},
    )
    assert response.status_code == 422


def test_reset_password_requires_otp_code_field(client, registered_farmer):
    payload, _ = registered_farmer
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"phone_number": payload["phone_number"], "new_password": "NewPass1!"},
    )
    assert response.status_code == 422
