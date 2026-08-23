from decimal import Decimal

from tests.conftest import auth_headers


def test_create_manual_expense_entry(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01", "description": "Tomato seeds"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["entry_type"] == "expense"
    assert body["amount"] == "500.00"
    assert body["source"] == "manual"


def test_create_manual_revenue_entry(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "revenue", "category": "other", "amount": "1200.00", "entry_date": "2026-01-05"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["entry_type"] == "revenue"


def test_cannot_create_entry_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "100.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens_b),
    )
    assert response.status_code == 404


def test_ledger_summary_computes_correct_totals(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "fertilizer", "amount": "300.00", "entry_date": "2026-01-02"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "revenue", "category": "other", "amount": "1200.00", "entry_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["total_expense"]) == Decimal("800.00")
    assert Decimal(body["total_revenue"]) == Decimal("1200.00")
    assert Decimal(body["net"]) == Decimal("400.00")
    assert len(body["entries"]) == 3


def test_ledger_summary_with_no_entries_is_zero_not_missing(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["total_expense"]) == Decimal("0")
    assert Decimal(body["total_revenue"]) == Decimal("0")
    assert Decimal(body["net"]) == Decimal("0")
    assert body["entries"] == []


def test_delete_manual_entry(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    entry = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "labor", "amount": "200.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()

    response = client.delete(f"/api/v1/ledger/entries/{entry['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204

    summary = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens)).json()
    assert summary["entries"] == []


def test_cannot_delete_another_farmers_entry(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    entry = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "labor", "amount": "200.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()

    response = client.delete(f"/api/v1/ledger/entries/{entry['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_import_sales_with_no_completed_sales_imports_nothing(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["imported_count"] == 0


def test_import_completed_sale_creates_a_real_revenue_entry_with_the_exact_sale_value(
    client, farmer_with_crop_cycle, verified_buyer, db_session
):
    from app.models.sale_order import SaleOrder, SaleOrderStatus
    from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload
    import uuid

    tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer

    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)
    ).json()
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)
    ).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(tokens)).json()

    # No existing endpoint transitions a sale all the way to COMPLETED (a
    # real, pre-existing gap in the marketplace lifecycle, unrelated to
    # this phase) - set it directly, the same established pattern
    # already used in tests/test_tasks.py for due-date manipulation.
    sale_row = db_session.get(SaleOrder, uuid.UUID(sale["id"]))
    sale_row.status = SaleOrderStatus.COMPLETED
    db_session.commit()

    response = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] == 1
    assert body["entries"][0]["source"] == "sale_linked"
    assert Decimal(body["entries"][0]["amount"]) == Decimal(sale["net_value"])


def test_importing_sales_twice_never_creates_a_duplicate_entry(client, farmer_with_crop_cycle, verified_buyer, db_session):
    from app.models.sale_order import SaleOrder, SaleOrderStatus
    from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload
    import uuid

    tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer

    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)
    ).json()
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)
    ).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(tokens)).json()

    sale_row = db_session.get(SaleOrder, uuid.UUID(sale["id"]))
    sale_row.status = SaleOrderStatus.COMPLETED
    db_session.commit()

    first = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens))
    assert first.json()["imported_count"] == 1

    second = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens))
    assert second.json()["imported_count"] == 0

    summary = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=auth_headers(tokens)).json()
    sale_linked_entries = [e for e in summary["entries"] if e["source"] == "sale_linked"]
    assert len(sale_linked_entries) == 1


def test_sale_linked_entry_cannot_be_deleted(client, farmer_with_crop_cycle, verified_buyer, db_session):
    from app.models.sale_order import SaleOrder, SaleOrderStatus
    from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload
    import uuid

    tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer

    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)
    ).json()
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)
    ).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(tokens)).json()

    sale_row = db_session.get(SaleOrder, uuid.UUID(sale["id"]))
    sale_row.status = SaleOrderStatus.COMPLETED
    db_session.commit()

    imported = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens)).json()
    entry_id = imported["entries"][0]["id"]

    response = client.delete(f"/api/v1/ledger/entries/{entry_id}", headers=auth_headers(tokens))
    assert response.status_code == 409


def test_invalid_negative_amount_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "-50.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422
