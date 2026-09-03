def _auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_get_own_profile_returns_expected_fields(client, registered_farmer):
    payload, tokens = registered_farmer
    response = client.get("/api/v1/farmers/me", headers=_auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == payload["full_name"]
    # The stored/returned phone number is the CANONICAL +91 form (see
    # app/core/phone_utils.py) - unique_phone() in tests/factories.py
    # generates a bare 10-digit number, so the canonical form is that
    # same value with "+91" prepended, not the raw payload value itself.
    assert body["phone_number"] == f"+91{payload['phone_number']}"
    assert body["preferred_language_code"] == "en"
    assert "password" not in body
    assert "password_hash" not in body


def test_update_own_profile_persists_changes(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.put(
        "/api/v1/farmers/me",
        json={"full_name": "Updated Name", "preferred_language_code": "hi"},
        headers=_auth_headers(tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Name"
    assert body["preferred_language_code"] == "hi"

    # Confirm it actually persisted, not just echoed back.
    refetched = client.get("/api/v1/farmers/me", headers=_auth_headers(tokens))
    assert refetched.json()["full_name"] == "Updated Name"


def test_update_with_invalid_language_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.put(
        "/api/v1/farmers/me", json={"preferred_language_code": "xx"}, headers=_auth_headers(tokens)
    )
    assert response.status_code == 422


def test_two_farmers_see_only_their_own_profile(client):
    import uuid as uuid_mod

    def register(name):
        payload = {
            "phone_number": "9" + str(uuid_mod.uuid4().int)[:9],
            "password": "Str0ngPass!",
            "full_name": name,
            "preferred_language_code": "en",
            "consents": [
                {"consent_type": "terms_of_service", "version": "1.0"},
                {"consent_type": "privacy_policy", "version": "1.0"},
            ],
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        return resp.json()

    tokens_a = register("Farmer A")
    tokens_b = register("Farmer B")

    profile_a = client.get("/api/v1/farmers/me", headers=_auth_headers(tokens_a)).json()
    profile_b = client.get("/api/v1/farmers/me", headers=_auth_headers(tokens_b)).json()

    assert profile_a["full_name"] == "Farmer A"
    assert profile_b["full_name"] == "Farmer B"
    assert profile_a["user_id"] != profile_b["user_id"]
    # There is no route that accepts an arbitrary farmer id (see farmers.py
    # docstring) - each token can only ever resolve to its own profile.


def test_consent_can_be_listed_and_recorded(client, registered_farmer):
    _, tokens = registered_farmer

    initial = client.get("/api/v1/farmers/me/consents", headers=_auth_headers(tokens))
    assert initial.status_code == 200
    types = {c["consent_type"] for c in initial.json()}
    assert "terms_of_service" in types
    assert "privacy_policy" in types

    added = client.post(
        "/api/v1/farmers/me/consents",
        json={"consent_type": "crop_image_processing", "version": "1.0", "status": "accepted"},
        headers=_auth_headers(tokens),
    )
    assert added.status_code == 201

    updated_list = client.get("/api/v1/farmers/me/consents", headers=_auth_headers(tokens))
    types_after = {c["consent_type"] for c in updated_list.json()}
    assert "crop_image_processing" in types_after
