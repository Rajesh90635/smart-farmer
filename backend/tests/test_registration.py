def test_valid_registration_returns_tokens(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload())
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_registration_never_returns_password_or_hash(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload())
    body_text = response.text
    assert "password" not in body_text.lower() or "password_hash" not in body_text.lower()


def test_duplicate_phone_number_is_rejected(client, valid_register_payload):
    payload = valid_register_payload()
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_ACCOUNT"


def test_invalid_phone_number_is_rejected(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload(phone_number="not-a-phone"))
    assert response.status_code == 422


def test_weak_password_is_rejected(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload(password="short"))
    assert response.status_code == 422


def test_password_with_no_digit_is_rejected(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload(password="alllettersnodigits"))
    assert response.status_code == 422


def test_missing_required_consent_is_rejected(client, valid_register_payload):
    payload = valid_register_payload(consents=[{"consent_type": "terms_of_service", "version": "1.0"}])
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_language_code_is_rejected(client, valid_register_payload):
    response = client.post("/api/v1/auth/register", json=valid_register_payload(preferred_language_code="xx"))
    assert response.status_code == 422


def test_registration_assigns_farmer_role(client, valid_register_payload, db_session):
    from app.core.jwt import decode_access_token

    response = client.post("/api/v1/auth/register", json=valid_register_payload())
    token = response.json()["access_token"]
    payload = decode_access_token(token)
    assert payload["role"] == "farmer"
