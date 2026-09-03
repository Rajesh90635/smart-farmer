import threading
import uuid

from tests.conftest import auth_headers
from tests.marketplace_factories import valid_dealer_listing_payload


def _listing(client, verified_dealer, approved_product, **overrides):
    tokens, _ = verified_dealer
    return client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"], **overrides), headers=auth_headers(tokens)).json()


def test_add_to_cart_creates_draft_order(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)

    response = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 2}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["items"][0]["quantity"] == 2
    assert body["final_amount"] is None


def test_adding_same_product_twice_increments_quantity(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)

    client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 2}, headers=auth_headers(farmer_tokens))
    response = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 3}, headers=auth_headers(farmer_tokens))
    assert response.json()["items"][0]["quantity"] == 5


def test_checkout_calculates_price_server_side_ignoring_client_values(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product, price="250.00")

    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 2}, headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["subtotal_amount"] == "500.00"
    assert body["final_amount"] == "500.00"
    assert body["items"][0]["unit_price"] == "250.00"


def test_checkout_uses_current_price_even_if_dealer_changed_it_after_cart_add(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product, price="250.00")

    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    client.put(f"/api/v1/dealer-products/{listing['id']}", json={"price": "400.00"}, headers=auth_headers(dealer_tokens))

    response = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens))
    assert response.json()["final_amount"] == "400.00"


def test_checkout_fails_on_insufficient_stock(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product, stock_quantity=1)

    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 5}, headers=auth_headers(farmer_tokens)).json()
    response = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def test_concurrent_checkout_never_oversells_stock(client, registered_farmer, another_farmer, verified_dealer, approved_product):
    """THE MANDATORY CONCURRENCY TEST for checkout, mirroring
    test_marketplace_offers.test_concurrent_offer_acceptance_never_oversells:
    a listing has 5 units in stock. Two different farmers each put 4 units
    in their own cart (separate DRAFT orders) and check out SIMULTANEOUSLY
    from two threads. Exactly one checkout must succeed and one must fail
    with insufficient-stock - the system must NEVER sell 8 units from a
    5-unit listing."""
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    listing = _listing(client, verified_dealer, approved_product, stock_quantity=5)

    cart_a = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 4}, headers=auth_headers(farmer_a_tokens)).json()
    cart_b = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 4}, headers=auth_headers(farmer_b_tokens)).json()

    results = {}

    def checkout(key, cart, tokens):
        resp = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(tokens))
        results[key] = resp.status_code

    t1 = threading.Thread(target=checkout, args=("a", cart_a, farmer_a_tokens))
    t2 = threading.Thread(target=checkout, args=("b", cart_b, farmer_b_tokens))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    statuses = sorted(results.values())
    assert statuses == [200, 422], f"Expected exactly one success and one failure, got: {results}"

    dealer_tokens, _ = verified_dealer
    listings = client.get("/api/v1/dealer-products/me", headers=auth_headers(dealer_tokens)).json()["items"]
    final_stock = next(item["stock_quantity"] for item in listings if item["id"] == listing["id"])
    assert final_stock == 1, f"Unexpected remaining stock: {final_stock} (would indicate an oversell)"


def test_checkout_fails_if_product_suspended_after_listing_created(client, registered_farmer, verified_dealer, approved_product, admin_tokens):
    """A real safety gap found while writing docs: checkout originally
    never re-checked the underlying Product's status at all, only the
    DealerProduct listing's own is_available flag. A product suspended
    or recalled AFTER a dealer listed it must still block checkout."""
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()

    client.post(f"/api/v1/products/{approved_product['id']}/suspend", headers=auth_headers(admin_tokens))

    response = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def test_checkout_fails_on_expired_listing(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    tokens, _ = verified_dealer
    listing = client.post(
        "/api/v1/dealer-products",
        json={"product_id": approved_product["id"], "price": "250.00", "stock_quantity": 10, "expiry_date": "2020-01-01"},
        headers=auth_headers(tokens),
    ).json()
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def test_duplicate_checkout_with_same_idempotency_key_does_not_create_two_orders(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()

    key = str(uuid.uuid4())
    first = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": key}, headers=auth_headers(farmer_tokens)).json()
    second = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": key}, headers=auth_headers(farmer_tokens)).json()
    assert first["id"] == second["id"]

    orders = client.get("/api/v1/orders", headers=auth_headers(farmer_tokens)).json()
    matching = [o for o in orders["items"] if o["id"] == first["id"]]
    assert len(matching) == 1


def test_full_order_lifecycle_to_delivery(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()

    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    paid = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens)).json()
    assert paid["status"] == "success"

    order_after_pay = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after_pay["status"] == "paid"

    client.post(f"/api/v1/dealer/orders/{order['id']}/accept", headers=auth_headers(dealer_tokens))
    for status in ["preparing", "ready_for_dispatch", "dispatched", "out_for_delivery", "delivered"]:
        response = client.post(f"/api/v1/dealer/orders/{order['id']}/advance?target_status={status}", headers=auth_headers(dealer_tokens))
        assert response.status_code == 200, f"failed to advance to {status}: {response.text}"
        assert response.json()["status"] == status

    confirm = client.post(f"/api/v1/orders/{order['id']}/confirm-delivery", headers=auth_headers(farmer_tokens))
    assert confirm.status_code == 200


def test_payment_failure_does_not_mark_order_paid(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()

    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    failed = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": False}, headers=auth_headers(farmer_tokens)).json()
    assert failed["status"] == "failed"

    order_after = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after["status"] != "paid"
    assert order_after["status"] == "payment_pending"


def test_dealer_rejection_requires_reason_and_restocks(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product, stock_quantity=10)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 3}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))

    response = client.post(f"/api/v1/dealer/orders/{order['id']}/reject", json={"reason": "out_of_stock"}, headers=auth_headers(dealer_tokens))
    assert response.status_code == 200
    assert response.json()["rejection_reason"] == "out_of_stock"


def test_concurrent_rejections_never_lose_a_restock(client, registered_farmer, another_farmer, verified_dealer, approved_product):
    """THE MANDATORY CONCURRENCY TEST for restock, mirroring
    test_concurrent_checkout_never_oversells_stock: this is the mirror-image
    bug - an unlocked restock (`stock_quantity += item.quantity`) can lose
    an update instead of overselling. Two DIFFERENT orders against the same
    listing (2 units and 3 units, out of a stock of 5 remaining after both
    checkouts) are rejected SIMULTANEOUSLY from two threads. Both
    restocks must land - the system must NEVER silently drop one of them."""
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product, stock_quantity=10)

    cart_a = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 2}, headers=auth_headers(farmer_a_tokens)).json()
    order_a = client.post(f"/api/v1/orders/{cart_a['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_a_tokens)).json()
    client.post(f"/api/v1/orders/{order_a['id']}/pay", headers=auth_headers(farmer_a_tokens))
    client.post(f"/api/v1/orders/{order_a['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_a_tokens))

    cart_b = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 3}, headers=auth_headers(farmer_b_tokens)).json()
    order_b = client.post(f"/api/v1/orders/{cart_b['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_b_tokens)).json()
    client.post(f"/api/v1/orders/{order_b['id']}/pay", headers=auth_headers(farmer_b_tokens))
    client.post(f"/api/v1/orders/{order_b['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_b_tokens))

    results = {}

    def reject(key, order):
        resp = client.post(f"/api/v1/dealer/orders/{order['id']}/reject", json={"reason": "out_of_stock"}, headers=auth_headers(dealer_tokens))
        results[key] = resp.status_code

    t1 = threading.Thread(target=reject, args=("a", order_a))
    t2 = threading.Thread(target=reject, args=("b", order_b))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results == {"a": 200, "b": 200}, f"Expected both rejections to succeed, got: {results}"

    listings = client.get("/api/v1/dealer-products/me", headers=auth_headers(dealer_tokens)).json()["items"]
    final_stock = next(item["stock_quantity"] for item in listings if item["id"] == listing["id"])
    assert final_stock == 10, f"Unexpected final stock: {final_stock} (would indicate a lost restock update)"


def test_dispute_can_only_be_filed_after_delivery(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()

    response = client.post(f"/api/v1/orders/{order['id']}/dispute", json={"reason": "wrong_product"}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 422


def test_dispute_and_admin_resolution_with_refund(client, registered_farmer, verified_dealer, approved_product, admin_tokens):
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/dealer/orders/{order['id']}/accept", headers=auth_headers(dealer_tokens))
    for status in ["preparing", "ready_for_dispatch", "dispatched", "out_for_delivery", "delivered"]:
        client.post(f"/api/v1/dealer/orders/{order['id']}/advance?target_status={status}", headers=auth_headers(dealer_tokens))

    dispute = client.post(f"/api/v1/orders/{order['id']}/dispute", json={"reason": "damaged_product"}, headers=auth_headers(farmer_tokens)).json()
    assert dispute["status"] == "open"

    resolved = client.post(
        f"/api/v1/disputes/{dispute['id']}/resolve",
        json={"status": "resolved", "refund_type": "full_refund", "refund_amount": order["final_amount"]},
        headers=auth_headers(admin_tokens),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    refund_complete = client.post(f"/api/v1/orders/{order['id']}/refund/complete", headers=auth_headers(admin_tokens))
    assert refund_complete.status_code == 200
    assert refund_complete.json()["status"] == "completed"


def test_admin_can_list_open_disputes_to_discover_what_needs_resolution(client, registered_farmer, verified_dealer, approved_product, admin_tokens):
    """The admin discovery gap: resolve_dispute already existed, but there
    was no way to find a dispute_id to resolve except being told one
    directly."""
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/dealer/orders/{order['id']}/accept", headers=auth_headers(dealer_tokens))
    for status in ["preparing", "ready_for_dispatch", "dispatched", "out_for_delivery", "delivered"]:
        client.post(f"/api/v1/dealer/orders/{order['id']}/advance?target_status={status}", headers=auth_headers(dealer_tokens))
    dispute = client.post(f"/api/v1/orders/{order['id']}/dispute", json={"reason": "damaged_product"}, headers=auth_headers(farmer_tokens)).json()

    open_list = client.get("/api/v1/disputes", headers=auth_headers(admin_tokens))
    assert open_list.status_code == 200
    ids = [d["id"] for d in open_list.json()["items"]]
    assert dispute["id"] in ids

    client.post(
        f"/api/v1/disputes/{dispute['id']}/resolve",
        json={"status": "resolved", "refund_type": "no_refund"},
        headers=auth_headers(admin_tokens),
    )

    after_resolve = client.get("/api/v1/disputes", headers=auth_headers(admin_tokens))
    assert dispute["id"] not in [d["id"] for d in after_resolve.json()["items"]]


def test_farmer_cannot_list_open_disputes(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/disputes", headers=auth_headers(tokens))
    assert response.status_code == 403


def test_farmer_a_cannot_see_farmer_bs_order(client, registered_farmer, another_farmer, verified_dealer, approved_product):
    _, farmer_a_tokens = registered_farmer
    _, farmer_b_tokens = another_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_a_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_a_tokens)).json()

    response = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_b_tokens))
    assert response.status_code == 404


def test_dealer_cannot_see_another_dealers_orders(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    listing = _listing(client, verified_dealer, approved_product)
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))

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

    response = client.post(f"/api/v1/dealer/orders/{order['id']}/accept", headers=auth_headers({"access_token": token_b, "refresh_token": "n/a"}))
    assert response.status_code == 404
