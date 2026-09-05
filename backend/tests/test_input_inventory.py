"""
Farmer input inventory (Domains 21-24, docs/audit/c04_inputs.md) -
previously entirely missing (no model/API existed for the farmer's own
on-farm stock, as distinct from DealerProduct.stock_quantity).
"""
import uuid
from datetime import date, timedelta

from app.core.config import get_settings
from app.services.input_inventory_service import run_expiry_check_sweep
from tests.conftest import auth_headers


def _valid_payload(**overrides):
    payload = {
        "category": "fertilizer",
        "custom_name": "Urea",
        "quantity": "50",
        "unit": "kg",
    }
    payload.update(overrides)
    return payload


def test_create_item_with_custom_name_no_product(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post("/api/v1/input-inventory", json=_valid_payload(), headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] is None
    assert body["product_name"] is None
    assert body["custom_name"] == "Urea"
    assert body["quantity"] == "50.00"
    assert body["is_low_stock"] is False


def test_create_item_linked_to_catalog_product_resolves_product_name(client, registered_farmer, approved_product):
    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/input-inventory",
        json=_valid_payload(product_id=approved_product["id"], custom_name=None, category=approved_product["category"]),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == approved_product["id"]
    assert body["product_name"] == approved_product["name"]


def test_create_item_without_product_or_custom_name_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    payload = _valid_payload(custom_name=None)
    response = client.post("/api/v1/input-inventory", json=payload, headers=auth_headers(tokens))
    assert response.status_code == 422


def test_list_only_shows_the_farmers_own_items(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    client.post("/api/v1/input-inventory", json=_valid_payload(), headers=auth_headers(tokens_a))

    response = client.get("/api/v1/input-inventory", headers=auth_headers(tokens_b))
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_cannot_access_another_farmers_item(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    item = client.post("/api/v1/input-inventory", json=_valid_payload(), headers=auth_headers(tokens_a)).json()

    response = client.get(f"/api/v1/input-inventory/{item['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_record_usage_decreases_quantity(client, registered_farmer):
    _, tokens = registered_farmer
    item = client.post("/api/v1/input-inventory", json=_valid_payload(quantity="50"), headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "20"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["quantity"] == "30.00"


def test_record_usage_greater_than_remaining_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    item = client.post("/api/v1/input-inventory", json=_valid_payload(quantity="10"), headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "20"}, headers=auth_headers(tokens))
    assert response.status_code == 422


def test_low_stock_alert_fires_once_then_stays_quiet_until_restocked(client, registered_farmer):
    """D22-06/D24-08: crossing the threshold notifies once; repeated
    usage calls while still low must not spam a second notification;
    restocking above the threshold and dropping low again DOES re-alert."""
    _, tokens = registered_farmer
    item = client.post(
        "/api/v1/input-inventory", json=_valid_payload(quantity="50", low_stock_threshold="10"), headers=auth_headers(tokens)
    ).json()

    first = client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "45"}, headers=auth_headers(tokens))
    assert first.json()["is_low_stock"] is True

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    stock_alerts = [n for n in notifications if n["category"] == "stock_alert"]
    assert len(stock_alerts) == 1

    # Still low - a second usage call must not duplicate the alert.
    client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "1"}, headers=auth_headers(tokens))
    notifications_after = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    assert len([n for n in notifications_after if n["category"] == "stock_alert"]) == 1

    # Restock above threshold, then drop low again - must re-alert.
    client.post(f"/api/v1/input-inventory/{item['id']}/restock", json={"quantity_added": "40"}, headers=auth_headers(tokens))
    client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "40"}, headers=auth_headers(tokens))
    notifications_final = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    assert len([n for n in notifications_final if n["category"] == "stock_alert"]) == 2


def test_restock_increases_quantity(client, registered_farmer):
    _, tokens = registered_farmer
    item = client.post("/api/v1/input-inventory", json=_valid_payload(quantity="10"), headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/input-inventory/{item['id']}/restock", json={"quantity_added": "15"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["quantity"] == "25.00"


def test_correct_quantity_sets_value_directly_with_audited_reason(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    item = client.post("/api/v1/input-inventory", json=_valid_payload(quantity="10"), headers=auth_headers(tokens)).json()

    response = client.post(
        f"/api/v1/input-inventory/{item['id']}/correct",
        json={"new_quantity": "42", "reason": "Recounted physical stock"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == "42.00"

    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    entries = db_session.execute(
        select(AuditLog).where(AuditLog.entity == "input_inventory_item", AuditLog.entity_id == item["id"])
    ).scalars().all()
    assert any("INPUT_INVENTORY_CORRECTED" in e.action and "Recounted physical stock" in e.action for e in entries)


def test_expiry_sweep_alerts_once_for_soon_expiring_stock(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    item = client.post(
        "/api/v1/input-inventory",
        json=_valid_payload(quantity="10", expiry_date=(date.today() + timedelta(days=3)).isoformat()),
        headers=auth_headers(tokens),
    ).json()

    settings = get_settings()
    alerted_first = run_expiry_check_sweep(db_session, settings)
    assert alerted_first == 1

    alerted_second = run_expiry_check_sweep(db_session, settings)
    assert alerted_second == 0  # already alerted for this item - no duplicate

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    stock_alerts = [n for n in notifications if n["category"] == "stock_alert"]
    assert len(stock_alerts) == 1
    assert "Urea" in stock_alerts[0]["body"]


def test_expiry_sweep_ignores_a_fully_consumed_item(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    item = client.post(
        "/api/v1/input-inventory",
        json=_valid_payload(quantity="10", expiry_date=(date.today() + timedelta(days=3)).isoformat()),
        headers=auth_headers(tokens),
    ).json()
    client.post(f"/api/v1/input-inventory/{item['id']}/usage", json={"quantity_used": "10"}, headers=auth_headers(tokens))

    settings = get_settings()
    alerted = run_expiry_check_sweep(db_session, settings)
    assert alerted == 0


def test_expiry_sweep_ignores_stock_expiring_far_in_the_future(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    client.post(
        "/api/v1/input-inventory",
        json=_valid_payload(quantity="10", expiry_date=(date.today() + timedelta(days=365)).isoformat()),
        headers=auth_headers(tokens),
    )

    settings = get_settings()
    alerted = run_expiry_check_sweep(db_session, settings)
    assert alerted == 0


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/input-inventory")
    assert response.status_code == 401
