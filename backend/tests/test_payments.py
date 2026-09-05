import uuid

from tests.conftest import auth_headers
from tests.marketplace_factories import valid_dealer_listing_payload


def _confirmed_order(client, registered_farmer, verified_dealer, approved_product, **overrides):
    _, farmer_tokens = registered_farmer
    dealer_tokens, _ = verified_dealer
    listing = client.post(
        "/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"], **overrides), headers=auth_headers(dealer_tokens)
    ).json()
    cart = client.post("/api/v1/cart", json={"dealer_product_id": listing["id"], "quantity": 1}, headers=auth_headers(farmer_tokens)).json()
    order = client.post(f"/api/v1/orders/{cart['id']}/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=auth_headers(farmer_tokens)).json()
    return farmer_tokens, order


def test_initiate_payment_moves_order_to_payment_pending(client, registered_farmer, verified_dealer, approved_product):
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)

    response = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_completing_payment_as_success_marks_order_paid(client, registered_farmer, verified_dealer, approved_product):
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    response = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    order_after = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after["status"] == "paid"


def test_farmer_can_retry_payment_after_a_failure(client, registered_farmer, verified_dealer, approved_product):
    """Real bug fix: a second /pay call after a failed payment used to
    409 because the order was already sitting in PAYMENT_PENDING and
    apply_transition required an actual state change (PAYMENT_PENDING has
    no allowed self-transition). This must now succeed."""
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    failed = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": False}, headers=auth_headers(farmer_tokens))
    assert failed.json()["status"] == "failed"

    retry = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    assert retry.status_code == 200
    assert retry.json()["status"] == "pending"

    succeeded = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    assert succeeded.status_code == 200
    assert succeeded.json()["status"] == "success"

    order_after = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after["status"] == "paid"


def test_cannot_initiate_a_second_payment_while_one_is_already_pending(client, registered_farmer, verified_dealer, approved_product):
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    second_attempt = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    assert second_attempt.status_code == 409
