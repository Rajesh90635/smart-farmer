"""
D20-01..12 (docs/audit/FINAL_CANONICAL_group_A.md): Soil Testing domain -
previously entirely missing (confirmed by exhaustive search before this
session).
"""
import io

from tests.conftest import auth_headers
from tests.photo_factories import make_test_jpeg


def _create_plot_and_sample(client, tokens, **overrides):
    from tests.farm_factories import valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    payload = {"collection_date": "2026-06-01"}
    payload.update(overrides)
    sample = client.post(f"/api/v1/plots/{plot['id']}/soil-samples", json=payload, headers=headers).json()
    return plot, sample


def test_create_soil_sample_record(client, registered_farmer):
    """D20-01."""
    _, tokens = registered_farmer
    plot, sample = _create_plot_and_sample(client, tokens)
    assert sample["plot_id"] == plot["id"]
    assert sample["collection_date"] == "2026-06-01"
    assert sample["self_tested"] is True  # no lab_name given


def test_soil_sample_with_lab_name_is_not_self_tested(client, registered_farmer):
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens, lab_name="State Agricultural Lab")
    assert sample["lab_name"] == "State Agricultural Lab"
    assert sample["self_tested"] is False


def test_cannot_create_soil_sample_under_another_farmers_plot(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    plot, _ = _create_plot_and_sample(client, tokens)
    _, tokens_b = another_farmer

    response = client.post(
        f"/api/v1/plots/{plot['id']}/soil-samples", json={"collection_date": "2026-06-01"}, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_create_soil_test_result_linked_to_sample(client, registered_farmer):
    """D20-02."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)

    response = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results",
        json={"test_date": "2026-06-05", "ph_value": "6.5"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["soil_sample_id"] == sample["id"]
    assert body["ph_value"] == "6.50"


def test_ph_value_rejected_outside_0_to_14_range(client, registered_farmer):
    """D20-03."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)

    response = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results",
        json={"test_date": "2026-06-05", "ph_value": "15.0"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_create_soil_test_result_with_npk_and_organic_carbon_and_ec_values(client, registered_farmer):
    """D20-04/D20-05/D20-06/D20-07/D20-08."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)

    response = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results",
        json={
            "test_date": "2026-06-05",
            "nitrogen_kg_per_ha": "280.50",
            "phosphorus_kg_per_ha": "45.25",
            "potassium_kg_per_ha": "310.00",
            "organic_carbon_percent": "0.75",
            "ec_ds_per_m": "0.450",
        },
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nitrogen_kg_per_ha"] == "280.50"
    assert body["phosphorus_kg_per_ha"] == "45.25"
    assert body["potassium_kg_per_ha"] == "310.00"
    assert body["organic_carbon_percent"] == "0.75"
    assert body["ec_ds_per_m"] == "0.450"


def test_create_soil_test_result_with_micronutrient_json(client, registered_farmer):
    """D20-09."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)

    response = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results",
        json={"test_date": "2026-06-05", "micronutrients": {"zinc": "1.2", "boron": "0.5"}},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["micronutrients"] == {"zinc": "1.2", "boron": "0.5"}


def test_soil_test_result_requires_test_date(client, registered_farmer):
    """D20-11."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)

    response = client.post(f"/api/v1/soil-samples/{sample['id']}/results", json={}, headers=auth_headers(tokens))
    assert response.status_code == 422


def test_soil_test_result_is_stale_after_max_age(client, registered_farmer, db_session):
    """D20-12."""
    import uuid as uuid_mod
    from datetime import datetime, timedelta, timezone

    from app.core.config import get_settings
    from app.models.soil_test_result import SoilTestResult

    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)
    result = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results", json={"test_date": "2026-06-05"}, headers=auth_headers(tokens)
    ).json()
    assert result["is_stale"] is False

    settings = get_settings()
    stored = db_session.get(SoilTestResult, uuid_mod.UUID(result["id"]))
    # Matches is_stale()'s own UTC-based "today" exactly - using the local
    # system date here would be off by one whenever local time and UTC
    # straddle midnight on different calendar days.
    stored.test_date = datetime.now(timezone.utc).date() - timedelta(days=settings.soil_test_max_age_days + 1)
    db_session.commit()

    stale_result = client.get(f"/api/v1/soil-samples/{sample['id']}/results", headers=auth_headers(tokens)).json()
    assert stale_result["items"][0]["is_stale"] is True


def test_upload_soil_report_document(client, registered_farmer):
    """D20-10."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)
    result = client.post(
        f"/api/v1/soil-samples/{sample['id']}/results", json={"test_date": "2026-06-05"}, headers=auth_headers(tokens)
    ).json()

    files = {"file": ("soil_report.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    response = client.post(f"/api/v1/soil-test-results/{result['id']}/report", files=files, headers=auth_headers(tokens))
    assert response.status_code == 201
    assert response.json()["report_storage_key"] is not None


def test_list_soil_samples_for_plot(client, registered_farmer):
    _, tokens = registered_farmer
    plot, _ = _create_plot_and_sample(client, tokens)
    client.post(
        f"/api/v1/plots/{plot['id']}/soil-samples", json={"collection_date": "2026-07-01"}, headers=auth_headers(tokens)
    )

    response = client.get(f"/api/v1/plots/{plot['id']}/soil-samples", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["total"] == 2
