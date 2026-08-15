import uuid

from tests.conftest import auth_headers
from tests.professional_factories import unique_phone, valid_professional_payload


def _register_professional_user(client, role="expert"):
    """Registers a plain farmer-flow user then assigns a professional
    role directly via the DB, since there's no self-service role-switch
    endpoint - registration always creates a FARMER by design (Prompt 3).
    This mirrors how a real deployment would provision non-farmer
    accounts (an admin/ops action), not exercised as an API call here."""
    import uuid as uuid_mod

    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), role=role)
    user_id = str(user.id)
    db.close()
    return {"access_token": token, "refresh_token": "n/a"}, user_id


def test_register_professional_starts_pending(client):
    tokens, _ = _register_professional_user(client)
    response = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["verification_status"] == "pending"  # never auto-verified


def test_cannot_register_professional_profile_twice(client):
    tokens, _ = _register_professional_user(client)
    client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens))
    second = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens))
    assert second.status_code == 409


def test_invalid_role_is_rejected(client):
    tokens, _ = _register_professional_user(client, role="expert")
    response = client.post("/api/v1/professionals", json=valid_professional_payload(role="farmer"), headers=auth_headers(tokens))
    assert response.status_code == 422


def test_invalid_language_code_is_rejected(client):
    tokens, _ = _register_professional_user(client)
    response = client.post(
        "/api/v1/professionals", json=valid_professional_payload(language_codes=["xx"]), headers=auth_headers(tokens)
    )
    assert response.status_code == 422


def test_professional_cannot_self_verify(client):
    """There is no endpoint a professional can call to change their own
    verification_status - only /verify /reject /suspend /reactivate exist,
    and all require the ADMIN role."""
    tokens, _ = _register_professional_user(client)
    profile = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/professionals/{profile['id']}/verify", json={}, headers=auth_headers(tokens))
    assert response.status_code == 403


def test_admin_can_verify_a_professional(client):
    tokens, user_id = _register_professional_user(client)
    profile = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens)).json()

    admin_tokens, _ = _register_professional_user(client, role="admin")
    response = client.post(f"/api/v1/professionals/{profile['id']}/verify", json={"reason": "docs checked"}, headers=auth_headers(admin_tokens))
    assert response.status_code == 200
    assert response.json()["verification_status"] == "verified"


def test_admin_can_suspend_a_verified_professional(client):
    tokens, _ = _register_professional_user(client)
    profile = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens)).json()
    admin_tokens, _ = _register_professional_user(client, role="admin")
    client.post(f"/api/v1/professionals/{profile['id']}/verify", json={}, headers=auth_headers(admin_tokens))

    response = client.post(f"/api/v1/professionals/{profile['id']}/suspend", json={"reason": "complaint"}, headers=auth_headers(admin_tokens))
    assert response.status_code == 200
    assert response.json()["verification_status"] == "suspended"


def test_unverified_professional_excluded_from_public_listing(client):
    tokens, _ = _register_professional_user(client)
    created = client.post("/api/v1/professionals", json=valid_professional_payload(), headers=auth_headers(tokens)).json()

    farmer_tokens_source, _ = _register_professional_user(client, role="farmer")
    listing = client.get("/api/v1/professionals?role=expert", headers=auth_headers(farmer_tokens_source))
    assert listing.status_code == 200
    # The listing is a global directory (not farmer-scoped), so other
    # tests' verified experts may legitimately also appear - the real
    # assertion is that THIS pending professional specifically is absent.
    ids = [p["id"] for p in listing.json()["items"]]
    assert created["id"] not in ids


def test_verified_professional_appears_in_listing(client, verified_expert):
    _, professional_id = verified_expert
    farmer_tokens, _ = _register_professional_user(client, role="farmer")
    listing = client.get("/api/v1/professionals?role=expert", headers=auth_headers(farmer_tokens))
    ids = [p["id"] for p in listing.json()["items"]]
    assert professional_id in ids


def test_update_availability(client, verified_expert):
    tokens, _ = verified_expert
    response = client.put("/api/v1/professionals/me/availability", json={"availability_status": "busy"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["availability_status"] == "busy"
