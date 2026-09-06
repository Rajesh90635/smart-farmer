import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.models.payment import Payment, PaymentStatus
from app.services.payment_service import run_payment_timeout_sweep
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


def test_payment_failure_notifies_the_farmer(client, registered_farmer, verified_dealer, approved_product):
    """D78-07 (docs/audit/FINAL_CANONICAL_group_D.md): payment_service._notify_payment_failed
    already fires a PAYMENT_ALERT/PAYMENT_FAILED notification (added for D64-06/D66-04) but no
    test asserted it - this closes that verification gap."""
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    failed = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": False}, headers=auth_headers(farmer_tokens))
    assert failed.json()["status"] == "failed"

    notifications = client.get("/api/v1/notifications", headers=auth_headers(farmer_tokens)).json()["items"]
    payment_alerts = [n for n in notifications if n["category"] == "payment_alert"]
    assert len(payment_alerts) == 1


def test_payment_response_includes_created_and_completed_dates(client, registered_farmer, verified_dealer, approved_product):
    """D64-05 (docs/audit/FINAL_CANONICAL_group_C.md): PaymentInitiateResponse
    had no date field at all - a farmer couldn't see "when" a payment
    happened without a direct DB query."""
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    initiated = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens)).json()
    assert initiated["created_at"] is not None
    assert initiated["completed_at"] is None

    completed = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens)).json()
    assert completed["completed_at"] is not None


def test_payment_timeout_sweep_marks_stale_pending_payments_timed_out(client, registered_farmer, verified_dealer, approved_product, db_session):
    """D66-03 (docs/audit/FINAL_CANONICAL_group_C.md): PaymentStatus.TIMEOUT
    existed but nothing ever assigned it - a payment could sit PENDING
    forever with no resolution."""
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    settings = get_settings()
    payment = db_session.execute(select(Payment).where(Payment.order_id == uuid.UUID(order["id"]))).scalar_one()
    payment.created_at = datetime.now(timezone.utc) - timedelta(minutes=settings.payment_timeout_minutes + 1)
    db_session.commit()

    # Scoped assertions, not a global count - the shared test DB persists
    # across runs, so other leftover PENDING payments may genuinely exist.
    run_payment_timeout_sweep(db_session, settings)

    db_session.refresh(payment)
    assert payment.status == PaymentStatus.TIMEOUT

    notifications = client.get("/api/v1/notifications", headers=auth_headers(farmer_tokens)).json()["items"]
    payment_alerts = [n for n in notifications if n["category"] == "payment_alert" and n["related_entity_id"] == str(payment.id)]
    assert len(payment_alerts) == 1


def test_payment_timeout_sweep_never_touches_a_fresh_pending_payment(client, registered_farmer, verified_dealer, approved_product, db_session):
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    settings = get_settings()
    run_payment_timeout_sweep(db_session, settings)

    payment = db_session.execute(select(Payment).where(Payment.order_id == uuid.UUID(order["id"]))).scalar_one()
    assert payment.status == PaymentStatus.PENDING

    still_pending = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    assert still_pending.status_code == 200
    assert still_pending.json()["status"] == "success"


def test_cannot_initiate_a_second_payment_while_one_is_already_pending(client, registered_farmer, verified_dealer, approved_product):
    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    second_attempt = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    assert second_attempt.status_code == 409


# --- D90-10: payment gateway provider abstraction ---

def test_initiate_payment_fails_honestly_when_no_gateway_is_configured(client, registered_farmer, verified_dealer, approved_product):
    from app.services.payment.not_configured_payment_gateway_provider import NotConfiguredPaymentGatewayProvider
    from tests.conftest import override_payment_gateway_provider

    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    with override_payment_gateway_provider(NotConfiguredPaymentGatewayProvider()):
        response = client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))
    assert response.status_code == 503

    order_after = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after["status"] != "payment_pending"  # never silently entered a payment state with no real payment


def test_sandbox_completion_is_refused_when_provider_is_not_sandbox_completable(
    client, registered_farmer, verified_dealer, approved_product
):
    """A real gateway's completion must arrive via its own webhook, never
    a farmer-callable endpoint - this must be refused, not silently
    treated as a real confirmation."""
    from app.services.payment.not_configured_payment_gateway_provider import NotConfiguredPaymentGatewayProvider
    from tests.conftest import override_payment_gateway_provider

    farmer_tokens, order = _confirmed_order(client, registered_farmer, verified_dealer, approved_product)
    client.post(f"/api/v1/orders/{order['id']}/pay", headers=auth_headers(farmer_tokens))

    with override_payment_gateway_provider(NotConfiguredPaymentGatewayProvider()):
        response = client.post(f"/api/v1/orders/{order['id']}/pay/complete", json={"succeed": True}, headers=auth_headers(farmer_tokens))
    assert response.status_code == 409

    order_after = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(farmer_tokens)).json()
    assert order_after["status"] != "paid"
