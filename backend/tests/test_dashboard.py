from datetime import date, timedelta

from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload


def test_dashboard_reflects_farm_plot_and_crop_counts(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer

    empty_dashboard = client.get("/api/v1/farmers/me/dashboard", headers=auth_headers(tokens)).json()
    assert empty_dashboard["farm_count"] == 0
    assert empty_dashboard["plot_count"] == 0
    assert empty_dashboard["active_crop_cycle_count"] == 0

    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()
    client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )

    dashboard = client.get("/api/v1/farmers/me/dashboard", headers=auth_headers(tokens)).json()
    assert dashboard["farm_count"] == 1
    assert dashboard["plot_count"] == 1
    assert dashboard["active_crop_cycle_count"] == 1


def test_dashboard_lists_crops_nearing_harvest_within_horizon(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()

    near_date = (date.today() + timedelta(days=5)).isoformat()
    far_date = (date.today() + timedelta(days=120)).isoformat()

    client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, sowing_date=date.today().isoformat(), expected_harvest_date=near_date),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, sowing_date=date.today().isoformat(), expected_harvest_date=far_date),
        headers=auth_headers(tokens),
    )

    dashboard = client.get("/api/v1/farmers/me/dashboard", headers=auth_headers(tokens)).json()
    assert len(dashboard["crops_nearing_harvest"]) == 1
    assert dashboard["crops_nearing_harvest"][0]["expected_harvest_date"] == near_date


def test_dashboard_excludes_another_farmers_data(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer

    client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens_a))

    dashboard_b = client.get("/api/v1/farmers/me/dashboard", headers=auth_headers(tokens_b)).json()
    assert dashboard_b["farm_count"] == 0
