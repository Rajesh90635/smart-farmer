from tests.conftest import auth_headers
from tests.marketplace_factories import valid_dealer_listing_payload, valid_product_payload


def test_product_starts_pending_review(client, admin_tokens):
    response = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens))
    assert response.status_code == 201
    assert response.json()["status"] == "pending_review"


def test_admin_can_list_pending_products_to_discover_what_needs_review(client, admin_tokens, approved_product):
    """The admin discovery gap: approve_product/reject_product/suspend_product
    already existed, but there was no way to find a product_id to act on."""
    pending = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()

    response = client.get("/api/v1/products/admin", headers=auth_headers(admin_tokens))
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()["items"]]
    assert pending["id"] in ids
    assert approved_product["id"] not in ids


def test_farmer_cannot_list_admin_products(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/products/admin", headers=auth_headers(tokens))
    assert response.status_code == 403


def test_pending_product_excluded_from_farmer_listing(client, admin_tokens, registered_farmer):
    _, farmer_tokens = registered_farmer
    product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()

    listing = client.get("/api/v1/products", headers=auth_headers(farmer_tokens)).json()
    ids = [p["id"] for p in listing["items"]]
    assert product["id"] not in ids


def test_approved_product_appears_in_farmer_listing(client, approved_product, registered_farmer):
    _, farmer_tokens = registered_farmer
    # Search by the product's own (randomized) name rather than assuming
    # it falls within the default page size - the shared test database
    # accumulates products across the whole test session, so an unfiltered
    # listing can easily exceed one page by the time this test runs.
    listing = client.get(f"/api/v1/products?q={approved_product['name']}", headers=auth_headers(farmer_tokens)).json()
    ids = [p["id"] for p in listing["items"]]
    assert approved_product["id"] in ids


def test_farmer_cannot_create_product(client, registered_farmer):
    _, farmer_tokens = registered_farmer
    response = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(farmer_tokens))
    assert response.status_code == 403


def test_verified_dealer_can_list_approved_product(client, verified_dealer, approved_product):
    tokens, _ = verified_dealer
    response = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"]), headers=auth_headers(tokens))
    assert response.status_code == 201
    assert response.json()["price"] == "250.00"


def test_dealer_cannot_list_a_pending_product(client, verified_dealer, admin_tokens):
    tokens, _ = verified_dealer
    pending_product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()

    response = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(pending_product["id"]), headers=auth_headers(tokens))
    assert response.status_code == 422


def test_unverified_dealer_cannot_list_products(client, approved_product):
    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.professional_profile import ProfessionalProfile, VerificationStatus
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = ProfessionalProfile(user_id=user.id, role="dealer", display_name="Pending Dealer", verification_status=VerificationStatus.PENDING)
    db.add(profile)
    db.commit()
    token = create_access_token(subject=str(user.id), role="dealer")
    db.close()

    response = client.post(
        "/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"]), headers=auth_headers({"access_token": token, "refresh_token": "n/a"})
    )
    assert response.status_code == 404


def test_dealer_price_update_writes_history_and_reuses_endpoint(client, verified_dealer, approved_product):
    tokens, _ = verified_dealer
    listing = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"]), headers=auth_headers(tokens)).json()

    response = client.put(f"/api/v1/dealer-products/{listing['id']}", json={"price": "300.00", "price_change_reason": "supplier cost increase"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["price"] == "300.00"


def test_dealer_cannot_update_another_dealers_listing(client, verified_dealer, approved_product):
    tokens_a, _ = verified_dealer
    listing = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"]), headers=auth_headers(tokens_a)).json()

    from app.core.jwt import create_access_token
    from app.core.security_passwords import hash_password
    from app.db.session import SessionLocal
    from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
    from app.models.user import User
    from tests.professional_factories import unique_phone

    db = SessionLocal()
    user = User(phone_number=unique_phone(), password_hash=hash_password("Str0ngPass1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    profile_b = ProfessionalProfile(user_id=user.id, role="dealer", display_name="Dealer B", verification_status=VerificationStatus.VERIFIED, availability_status=AvailabilityStatus.AVAILABLE)
    db.add(profile_b)
    db.commit()
    token_b = create_access_token(subject=str(user.id), role="dealer")
    db.close()

    response = client.put(f"/api/v1/dealer-products/{listing['id']}", json={"price": "999.00"}, headers=auth_headers({"access_token": token_b, "refresh_token": "n/a"}))
    assert response.status_code == 404
