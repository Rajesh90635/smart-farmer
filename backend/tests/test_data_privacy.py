"""
D100-09 (docs/audit/c13_governance_farmbrain_security.md): data export
and account deletion. See app/services/data_privacy_service.py's module
docstring for the full scoping disclosure - this is a good-faith MVP
implementation, not a certified compliance review.
"""
from tests.conftest import auth_headers


def test_data_export_includes_farm_and_crop_cycle(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get("/api/v1/farmers/me/data-export", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()

    assert body["profile"]["full_name"]
    assert len(body["farms"]) >= 1
    assert any(cc["id"] == crop_cycle_id for cc in body["crop_cycles"])
    assert "not_included" in body and len(body["not_included"]) > 0


def test_data_export_includes_a_task_created_for_the_crop_cycle(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)).json()

    body = client.get("/api/v1/farmers/me/data-export", headers=auth_headers(tokens)).json()
    assert any(t["id"] == task["id"] for t in body["tasks"])


def test_cannot_export_without_authentication(client):
    response = client.get("/api/v1/farmers/me/data-export")
    assert response.status_code == 401


def test_data_export_covers_harvest_order_inventory_and_treatment_data(
    client, farmer_with_crop_cycle, verified_dealer, approved_product
):
    """Exercises the export branches test_data_export_includes_farm_and_crop_cycle
    never populates (empty lists execute no per-item serialization code) -
    this is what actually catches a wrong field name in those branches."""
    from tests.marketplace_factories import valid_dealer_listing_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    # Harvest + listing
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=headers).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "500"}, headers=headers)
    client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json={"quantity_available": "500", "unit": "kg", "delivery_option": "buyer_collection"},
        headers=headers,
    )

    # Dealer order
    dealer_tokens, _ = verified_dealer
    dealer_listing = client.post(
        "/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"]), headers=auth_headers(dealer_tokens)
    ).json()
    import uuid as uuid_mod

    cart = client.post("/api/v1/cart", json={"dealer_product_id": dealer_listing["id"], "quantity": 1}, headers=headers).json()
    checkout = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid_mod.uuid4())}, headers=headers)
    assert checkout.status_code in (200, 201), checkout.text

    # Input inventory
    client.post("/api/v1/input-inventory", json={"category": "fertilizer", "custom_name": "Urea", "quantity": "50", "unit": "kg"}, headers=headers)

    # Treatment
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=headers)

    body = client.get("/api/v1/farmers/me/data-export", headers=headers).json()
    assert len(body["harvests"]) >= 1
    assert len(body["harvest_listings"]) >= 1
    assert len(body["dealer_orders"]) >= 1
    assert len(body["input_inventory"]) >= 1
    assert len(body["treatments"]) >= 1
    assert len(body["notifications"]) >= 1  # confirm-ready above sends a HARVEST_ALERT


def test_data_export_covers_marketplace_sale_expert_case_and_ai_analysis(
    client, farmer_with_crop_cycle, verified_buyer, sample_crop_id
):
    import io

    from app.services.ai.model_provider import TopKPrediction
    from tests.fake_model_provider import FakeModelProvider
    from tests.harvest_factories import valid_offer_payload
    from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
    from tests.professional_factories import valid_case_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    # Marketplace sale
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=headers).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "500"}, headers=headers)
    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json={"quantity_available": "500", "unit": "kg", "delivery_option": "buyer_collection"},
        headers=headers,
    ).json()
    buyer_tokens, _ = verified_buyer
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)
    ).json()
    client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=headers)

    # Expert case (no verified_expert fixture requested here - status may
    # be waiting_for_assignment or assigned, either way a real row exists)
    client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=headers)

    # AI analysis with a farmer correction
    from tests.conftest import override_model_provider

    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=headers).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "export-test-photo", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=headers).json()
    with override_model_provider(FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.9)], supported_crops=["tomato"])):
        analysis = client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=headers).json()
    client.post(f"/api/v1/ai/analysis/{analysis['id']}/correction", json={"correction": "confirmed_correct"}, headers=headers)

    body = client.get("/api/v1/farmers/me/data-export", headers=headers).json()
    assert len(body["marketplace_sales"]) >= 1
    assert len(body["expert_cases"]) >= 1
    assert any(a["id"] == analysis["id"] and a["farmer_correction"] == "confirmed_correct" for a in body["ai_analyses"])
    assert len(body["crop_photos_metadata"]) >= 1


def test_account_deletion_deactivates_and_scrubs_pii(client, registered_farmer, db_session):
    import uuid as uuid_mod

    from app.core.jwt import decode_access_token
    from app.models.user import AccountStatus, User

    payload, tokens = registered_farmer
    farmer_id = decode_access_token(tokens["access_token"])["sub"]

    response = client.post("/api/v1/farmers/me/delete-account", headers=auth_headers(tokens))
    assert response.status_code == 204

    user = db_session.get(User, uuid_mod.UUID(farmer_id))
    assert user.status == AccountStatus.INACTIVE
    assert user.phone_number != f"+91{payload['phone_number']}"
    assert user.phone_number.startswith("deleted-")
    assert user.email is None
    assert user.farmer_profile.full_name == "Deleted Farmer"


def test_account_deletion_revokes_refresh_tokens(client, registered_farmer, db_session):
    import uuid as uuid_mod

    from app.core.jwt import decode_access_token
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import select

    _, tokens = registered_farmer
    farmer_id = decode_access_token(tokens["access_token"])["sub"]

    client.post("/api/v1/farmers/me/delete-account", headers=auth_headers(tokens))

    refresh_tokens = db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == uuid_mod.UUID(farmer_id))
    ).scalars().all()
    assert refresh_tokens  # registration issues at least one
    assert all(t.revoked_at is not None for t in refresh_tokens)


def test_cannot_delete_an_already_deactivated_account(client, registered_farmer):
    _, tokens = registered_farmer
    first = client.post("/api/v1/farmers/me/delete-account", headers=auth_headers(tokens))
    assert first.status_code == 204

    second = client.post("/api/v1/farmers/me/delete-account", headers=auth_headers(tokens))
    assert second.status_code == 409
