import uuid
from decimal import Decimal

from tests.conftest import auth_headers


def _create_stage(db_session, crop_id, name="Land Preparation", seq=1):
    from app.models.crop_stage_definition import CropStageDefinition

    stage = CropStageDefinition(
        crop_id=uuid.UUID(crop_id),
        stage_code=f"test_stage_{uuid.uuid4().hex[:8]}",
        display_name=name,
        sequence_order=seq,
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage


def _create_estimate(client, tokens, crop_cycle_id, amount, category="seed", stage_id=None):
    body = {"category": category, "estimated_amount": amount}
    if stage_id:
        body["crop_stage_definition_id"] = str(stage_id)
    return client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates", json=body, headers=auth_headers(tokens))


def _create_ledger_expense(client, tokens, crop_cycle_id, amount, category="seed", stage_id=None):
    body = {"entry_type": "expense", "category": category, "amount": amount, "entry_date": "2026-01-01"}
    if stage_id:
        body["crop_stage_definition_id"] = str(stage_id)
    return client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries", json=body, headers=auth_headers(tokens))


def _create_ledger_revenue(client, tokens, crop_cycle_id, amount):
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "revenue", "category": "harvest_sale", "amount": amount, "entry_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )


def test_no_data_at_all_returns_honest_unavailable_estimate_and_zero_actual(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_cost"] is None
    assert Decimal(body["actual_cost"]) == Decimal("0")
    assert body["cost_variance"] is None
    assert body["expected_revenue"] is None
    assert body["estimated_profit"] is None
    assert body["has_any_actual_revenue"] is False


def test_estimated_cost_only_no_actual_yet(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "500.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["estimated_cost"]) == Decimal("500.00")
    assert Decimal(body["actual_cost"]) == Decimal("0")
    assert Decimal(body["cost_variance"]) == Decimal("500.00")


def test_actual_cost_only_no_estimate_entered(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_ledger_expense(client, tokens, crop_cycle_id, "300.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert body["estimated_cost"] is None
    assert Decimal(body["actual_cost"]) == Decimal("300.00")
    assert body["cost_variance"] is None


def test_estimated_and_actual_variance_is_correctly_signed(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "500.00")
    _create_ledger_expense(client, tokens, crop_cycle_id, "420.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["estimated_cost"]) == Decimal("500.00")
    assert Decimal(body["actual_cost"]) == Decimal("420.00")
    assert Decimal(body["cost_variance"]) == Decimal("80.00")
    assert Decimal(body["cost_variance_percent"]) == Decimal("16.00")


def test_actual_cost_exceeding_estimate_is_a_negative_variance(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "500.00")
    _create_ledger_expense(client, tokens, crop_cycle_id, "650.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["cost_variance"]) == Decimal("-150.00")


def test_revenue_available_produces_a_real_profit(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_ledger_expense(client, tokens, crop_cycle_id, "1000.00")
    _create_ledger_revenue(client, tokens, crop_cycle_id, "1500.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_revenue"]) == Decimal("1500.00")
    assert Decimal(body["actual_profit_loss"]) == Decimal("500.00")
    assert body["has_any_actual_revenue"] is True


def test_revenue_unavailable_still_shows_a_loss_figure_but_flagged_as_no_revenue_yet(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_ledger_expense(client, tokens, crop_cycle_id, "800.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_profit_loss"]) == Decimal("-800.00")
    assert body["has_any_actual_revenue"] is False


def test_loss_when_actual_cost_exceeds_actual_revenue(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_ledger_expense(client, tokens, crop_cycle_id, "1000.00")
    _create_ledger_revenue(client, tokens, crop_cycle_id, "700.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_profit_loss"]) == Decimal("-300.00")
    assert body["has_any_actual_revenue"] is True


def test_zero_actual_cost_avoids_division_by_zero_for_percent_and_ratio(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_ledger_revenue(client, tokens, crop_cycle_id, "500.00")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["actual_cost"]) == Decimal("0")
    assert body["profit_loss_percent"] is None
    assert body["revenue_to_cost_ratio"] is None


def test_multiple_ledger_entries_and_estimates_sum_correctly(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_estimate(client, tokens, crop_cycle_id, "300.00", category="seed")
    _create_estimate(client, tokens, crop_cycle_id, "200.00", category="fertilizer")
    _create_ledger_expense(client, tokens, crop_cycle_id, "150.00", category="seed")
    _create_ledger_expense(client, tokens, crop_cycle_id, "180.00", category="fertilizer")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert Decimal(body["estimated_cost"]) == Decimal("500.00")
    assert Decimal(body["actual_cost"]) == Decimal("330.00")


def test_stage_wise_summary_uses_real_crop_stage_definitions(client, farmer_with_crop_cycle, sample_crop_id, db_session):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    stage = _create_stage(db_session, sample_crop_id, name="Land Preparation")

    _create_estimate(client, tokens, crop_cycle_id, "200.00", stage_id=stage.id)
    _create_ledger_expense(client, tokens, crop_cycle_id, "180.00", stage_id=stage.id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert len(body["stage_summaries"]) == 1
    stage_summary = body["stage_summaries"][0]
    assert stage_summary["stage_display_name"] == "Land Preparation"
    assert Decimal(stage_summary["estimated_amount"]) == Decimal("200.00")
    assert Decimal(stage_summary["actual_amount"]) == Decimal("180.00")
    assert Decimal(stage_summary["variance"]) == Decimal("20.00")


def test_stage_with_no_data_is_omitted_not_shown_as_zero(client, farmer_with_crop_cycle, sample_crop_id, db_session):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _create_stage(db_session, sample_crop_id, name="Unused Stage")

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens))
    body = response.json()
    assert body["stage_summaries"] == []


def test_multiple_crop_cycles_never_combine_financial_data(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    _create_estimate(client, tokens, crop_cycle_id_1, "500.00")
    _create_estimate(client, tokens, crop_cycle_id_2, "999.00")

    summary_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/financial-summary", headers=headers).json()
    summary_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/financial-summary", headers=headers).json()
    assert Decimal(summary_1["estimated_cost"]) == Decimal("500.00")
    assert Decimal(summary_2["estimated_cost"]) == Decimal("999.00")


def test_cannot_access_another_farmers_financial_summary(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_cannot_create_estimate_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _create_estimate(client, tokens_b, crop_cycle_id, "100.00")
    assert response.status_code == 404


def test_unauthenticated_financial_summary_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary")
    assert response.status_code == 401


def test_invalid_crop_cycle_id_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{uuid.uuid4()}/financial-summary", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_delete_cost_estimate(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    estimate = _create_estimate(client, tokens, crop_cycle_id, "100.00").json()

    response = client.delete(f"/api/v1/cost-estimates/{estimate['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204

    summary = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=auth_headers(tokens)).json()
    assert summary["estimated_cost"] is None
