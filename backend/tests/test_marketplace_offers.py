import threading

from tests.conftest import auth_headers
from tests.harvest_factories import valid_buyer_payload, valid_harvest_listing_payload, valid_offer_payload


def _create_listing(client, tokens, crop_cycle_id, **overrides):
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    return client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(**overrides), headers=auth_headers(tokens)).json()


def test_buyer_registration_starts_pending(client):
    from tests.test_professionals import _register_professional_user

    tokens, _ = _register_professional_user(client, role="buyer")
    response = client.post("/api/v1/marketplace/buyers", json=valid_buyer_payload(), headers=auth_headers(tokens))
    assert response.status_code == 201
    assert response.json()["verification_status"] == "pending"


def test_verified_buyer_can_browse_listings(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)

    response = client.get("/api/v1/marketplace/listings", headers=auth_headers(buyer_tokens))
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert listing["id"] in ids


def test_offer_and_counter_offer_negotiation_history_is_never_overwritten(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)

    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(price_per_unit="30.00"), headers=auth_headers(buyer_tokens)).json()

    farmer_counter = client.post(f"/api/v1/marketplace/offers/{offer['id']}/counter", json={"price_per_unit": "34.00", "quantity": "500.00"}, headers=auth_headers(farmer_tokens))
    assert farmer_counter.status_code == 201
    assert farmer_counter.json()["proposed_by"] == "farmer"

    buyer_counter = client.post(f"/api/v1/marketplace/offers/{offer['id']}/counter-as-buyer", json={"price_per_unit": "32.00", "quantity": "500.00"}, headers=auth_headers(buyer_tokens))
    assert buyer_counter.status_code == 201
    assert buyer_counter.json()["proposed_by"] == "buyer"

    accepted = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens))
    assert accepted.status_code == 200
    assert accepted.json()["price_per_unit"] == "32.00"


def test_accepting_offer_decrements_listing_quantity(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="1000.00")

    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(quantity="400.00"), headers=auth_headers(buyer_tokens)).json()
    client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens))

    listings_after = client.get("/api/v1/harvests/listings/me", headers=auth_headers(farmer_tokens)).json()
    assert listings_after["items"][0]["quantity_available"] == "600.00"


def test_cannot_accept_offer_exceeding_available_quantity(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="100.00")

    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(quantity="500.00"), headers=auth_headers(buyer_tokens)).json()
    response = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens))
    assert response.status_code == 409


def test_concurrent_offer_acceptance_never_oversells(client, farmer_with_crop_cycle, verified_buyer):
    """THE MANDATORY CONCURRENCY TEST: farmer has 1000 kg. Two offers for
    700kg and 600kg (total 1300kg, exceeding availability) are accepted
    SIMULTANEOUSLY from two threads. Exactly one must succeed and one
    must fail with insufficient-quantity - the system must NEVER sell
    1300kg from a 1000kg listing."""
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="1000.00")

    offer_a = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(quantity="700.00"), headers=auth_headers(buyer_tokens)).json()
    offer_b = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(quantity="600.00"), headers=auth_headers(buyer_tokens)).json()

    results = {}

    def accept(key, offer_id):
        resp = client.post(f"/api/v1/marketplace/offers/{offer_id}/accept", headers=auth_headers(farmer_tokens))
        results[key] = resp.status_code

    t1 = threading.Thread(target=accept, args=("a", offer_a["id"]))
    t2 = threading.Thread(target=accept, args=("b", offer_b["id"]))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    statuses = sorted(results.values())
    assert statuses == [200, 409], f"Expected exactly one success and one failure, got: {results}"

    final_listing = client.get("/api/v1/harvests/listings/me", headers=auth_headers(farmer_tokens)).json()["items"][0]
    remaining = float(final_listing["quantity_available"])
    assert remaining in (300.0, 400.0), f"Unexpected remaining quantity: {remaining} (would indicate an oversell or double-processing)"


def test_full_sale_lifecycle_to_completion(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)

    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens)).json()

    client.post(f"/api/v1/marketplace/sales/{sale['id']}/accept", headers=auth_headers(farmer_tokens))
    for status in ["preparing", "ready_for_collection", "collected", "in_transit", "delivered"]:
        resp = client.post(f"/api/v1/marketplace/sales/{sale['id']}/advance?target_status={status}", headers=auth_headers(farmer_tokens))
        assert resp.status_code == 200, f"failed advancing to {status}: {resp.text}"

    confirm = client.post(f"/api/v1/marketplace/purchases/{sale['id']}/confirm-delivery", headers=auth_headers(buyer_tokens))
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "payment_pending"

    client.post(f"/api/v1/marketplace/purchases/{sale['id']}/pay", headers=auth_headers(buyer_tokens))
    paid = client.post(f"/api/v1/marketplace/purchases/{sale['id']}/pay/complete?succeed=true", headers=auth_headers(buyer_tokens))
    assert paid.status_code == 200
    assert paid.json()["status"] == "success"

    sale_after = client.get(f"/api/v1/marketplace/sales/{sale['id']}", headers=auth_headers(farmer_tokens)).json()
    assert sale_after["status"] == "paid"


def test_cancellation_restores_listing_quantity(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="1000.00")

    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(quantity="400.00"), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens)).json()

    cancel = client.post(f"/api/v1/marketplace/sales/{sale['id']}/cancel", json={"reason": "buyer_cancelled"}, headers=auth_headers(farmer_tokens))
    assert cancel.status_code == 200

    listings_after = client.get("/api/v1/harvests/listings/me", headers=auth_headers(farmer_tokens)).json()
    assert listings_after["items"][0]["quantity_available"] == "1000.00"
    assert listings_after["items"][0]["is_active"] is True


def test_invalid_cancellation_reason_rejected(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)
    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/marketplace/sales/{sale['id']}/cancel", json={"reason": "not_a_real_reason"}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def test_dispute_requires_delivery_stage(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)
    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/marketplace/sales/{sale['id']}/dispute", json={"reason": "wrong_quantity"}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def _create_sale_and_dispute_it(client, farmer_tokens, buyer_tokens, crop_cycle_id):
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)
    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens)).json()

    client.post(f"/api/v1/marketplace/sales/{sale['id']}/accept", headers=auth_headers(farmer_tokens))
    for status in ["preparing", "ready_for_collection", "collected", "in_transit", "delivered"]:
        client.post(f"/api/v1/marketplace/sales/{sale['id']}/advance?target_status={status}", headers=auth_headers(farmer_tokens))

    dispute = client.post(f"/api/v1/marketplace/sales/{sale['id']}/dispute", json={"reason": "damaged_crop"}, headers=auth_headers(farmer_tokens)).json()
    return sale, dispute


def test_dispute_resolution_cancelling_the_sale_restores_listing_quantity(client, farmer_with_crop_cycle, verified_buyer, admin_tokens):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    sale, dispute = _create_sale_and_dispute_it(client, farmer_tokens, buyer_tokens, crop_cycle_id)
    assert dispute["status"] == "open"

    resolved = client.post(
        f"/api/v1/marketplace/disputes/{dispute['id']}/resolve",
        json={"status": "resolved", "resulting_sale_status": "cancelled", "resolution_note": "Buyer's claim upheld; sale cancelled."},
        headers=auth_headers(admin_tokens),
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None

    sale_after = client.get(f"/api/v1/marketplace/sales/{sale['id']}", headers=auth_headers(farmer_tokens)).json()
    assert sale_after["status"] == "cancelled"

    listings_after = client.get("/api/v1/harvests/listings/me", headers=auth_headers(farmer_tokens)).json()
    assert listings_after["items"][0]["is_active"] is True


def test_dispute_can_be_escalated_without_touching_sale_status(client, farmer_with_crop_cycle, verified_buyer, admin_tokens):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    sale, dispute = _create_sale_and_dispute_it(client, farmer_tokens, buyer_tokens, crop_cycle_id)

    escalated = client.post(
        f"/api/v1/marketplace/disputes/{dispute['id']}/resolve",
        json={"status": "escalated"},
        headers=auth_headers(admin_tokens),
    )
    assert escalated.status_code == 200
    assert escalated.json()["status"] == "escalated"
    assert escalated.json()["resolved_at"] is None

    sale_after = client.get(f"/api/v1/marketplace/sales/{sale['id']}", headers=auth_headers(farmer_tokens)).json()
    assert sale_after["status"] == "disputed"


def test_sale_status_change_rejected_unless_resolving_or_closing(client, farmer_with_crop_cycle, verified_buyer, admin_tokens):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    _, dispute = _create_sale_and_dispute_it(client, farmer_tokens, buyer_tokens, crop_cycle_id)

    response = client.post(
        f"/api/v1/marketplace/disputes/{dispute['id']}/resolve",
        json={"status": "under_review", "resulting_sale_status": "completed"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 422


def test_farmer_a_cannot_see_farmer_bs_sale(client, farmer_with_crop_cycle, verified_buyer, another_farmer):
    farmer_a_tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    _, farmer_b_tokens = another_farmer
    listing = _create_listing(client, farmer_a_tokens, crop_cycle_id)
    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_a_tokens)).json()

    response = client.get(f"/api/v1/marketplace/sales/{sale['id']}", headers=auth_headers(farmer_b_tokens))
    assert response.status_code == 404


def test_unverified_buyer_cannot_make_an_offer(client, farmer_with_crop_cycle):
    from tests.test_professionals import _register_professional_user

    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    listing = _create_listing(client, farmer_tokens, crop_cycle_id)

    tokens, _ = _register_professional_user(client, role="buyer")
    client.post("/api/v1/marketplace/buyers", json=valid_buyer_payload(), headers=auth_headers(tokens))

    response = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(tokens))
    assert response.status_code == 404
