import uuid
from decimal import Decimal

from tests.conftest import auth_headers
from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload


def _create_estimate(client, tokens, crop_cycle_id, amount):
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates",
        json={"category": "seed", "estimated_amount": amount},
        headers=auth_headers(tokens),
    )


def _create_ledger_expense(client, tokens, crop_cycle_id, amount):
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": amount, "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )


def _create_harvest_with_estimated_quantity(client, tokens, crop_cycle_id, quantity):
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": quantity}, headers=auth_headers(tokens))
    return harvest


def test_no_data_at_all_returns_honest_unavailable_forecast(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_cost"] is None
    assert Decimal(body["actual_cost"]) == Decimal("0")
    assert body["projected_total_cost"] is None
    assert body["potential_additional_revenue"] is None
    assert body["revenue_projection_is_partial"] is True
    assert body["projected_profit_loss"] is None
    assert len(body["data_completeness_notes"]) > 0


def test_projected_cost_uses_remaining_estimate_not_full_estimate_again(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "1000.00")
    _create_ledger_expense(client, tokens, crop_cycle_id, "400.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["remaining_estimated_cost"]) == Decimal("600.00")
    assert Decimal(body["projected_total_cost"]) == Decimal("1000.00")


def test_overspending_floors_remaining_cost_at_zero_not_negative(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "500.00")
    _create_ledger_expense(client, tokens, crop_cycle_id, "700.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["remaining_estimated_cost"]) == Decimal("0")
    assert Decimal(body["projected_total_cost"]) == Decimal("700.00")
    assert any("exceeded" in note for note in body["data_completeness_notes"])


def test_potential_additional_revenue_uses_farmers_own_listing_price_and_yield(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_harvest_with_estimated_quantity(client, tokens, crop_cycle_id, "1000.00")
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(preferred_price="25.00"),
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["potential_additional_revenue"]) == Decimal("25000.00")
    assert body["revenue_projection_is_partial"] is False
    assert "1000.00" in body["potential_additional_revenue_basis"]
    assert "25.00" in body["potential_additional_revenue_basis"]


def test_no_active_listing_means_potential_revenue_is_unavailable_not_zero(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_harvest_with_estimated_quantity(client, tokens, crop_cycle_id, "1000.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert body["potential_additional_revenue"] is None
    assert body["revenue_projection_is_partial"] is True
    assert any("listing" in note.lower() for note in body["data_completeness_notes"])


def test_listing_without_a_preferred_price_means_potential_revenue_is_unavailable(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_harvest_with_estimated_quantity(client, tokens, crop_cycle_id, "1000.00")
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    listing_payload = valid_harvest_listing_payload()
    listing_payload.pop("preferred_price", None)
    client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=listing_payload, headers=auth_headers(tokens))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert body["potential_additional_revenue"] is None


def test_committed_revenue_from_accepted_but_not_completed_sale_is_real_not_zero(client, farmer_with_crop_cycle, verified_buyer):
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

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_revenue"]) == Decimal("0")
    assert Decimal(body["committed_revenue"]) == Decimal(sale["net_value"])


def test_completed_sale_counts_as_actual_not_committed(client, farmer_with_crop_cycle, verified_buyer, db_session):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer

    from app.models.sale_order import SaleOrder, SaleOrderStatus

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
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=auth_headers(tokens))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_revenue"]) == Decimal(sale["net_value"])
    assert Decimal(body["committed_revenue"]) == Decimal("0")


def test_full_projection_with_all_data_available_computes_correct_profit(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "1000.00")
    _create_ledger_expense(client, tokens, crop_cycle_id, "600.00")
    _create_harvest_with_estimated_quantity(client, tokens, crop_cycle_id, "100.00")
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(preferred_price="20.00"),
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["projected_total_cost"]) == Decimal("1000.00")
    assert Decimal(body["projected_total_revenue"]) == Decimal("2000.00")
    assert Decimal(body["projected_profit_loss"]) == Decimal("1000.00")
    assert Decimal(body["projected_profit_loss_percent"]) == Decimal("100.00")


def test_multiple_crop_cycles_never_combine_forecast_data(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    _create_estimate(client, tokens, crop_cycle_id_1, "500.00")
    _create_estimate(client, tokens, crop_cycle_id_2, "999.00")

    forecast_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/profit-forecast", headers=headers).json()
    forecast_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/profit-forecast", headers=headers).json()
    assert Decimal(forecast_1["estimated_cost"]) == Decimal("500.00")
    assert Decimal(forecast_2["estimated_cost"]) == Decimal("999.00")


def test_cannot_access_another_farmers_forecast(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_invalid_crop_cycle_id_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{uuid.uuid4()}/profit-forecast", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_unauthenticated_forecast_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast")
    assert response.status_code == 401


def test_forecast_uses_estimated_yield_label_when_only_estimate_exists(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(
        f"/api/v1/harvests/{harvest['id']}/confirm-ready",
        json={"estimated_quantity": "1000.00", "actual_harvest_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(preferred_price="10.00"), headers=auth_headers(tokens))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=auth_headers(tokens))
    body = response.json()
    assert "estimated yield" in body["potential_additional_revenue_basis"]
