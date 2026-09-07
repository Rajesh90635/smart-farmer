"""
Missing Backlog Batch 8 (group 1): D13-02, D17-02, D17-03, D17-06,
D19-04, D51-06 (docs/audit/FINAL_CANONICAL_group_A.md,
docs/audit/FINAL_CANONICAL_group_C.md).
"""
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.harvest_factories import valid_harvest_listing_payload


def _create_plot(client, tokens, **overrides):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(**overrides), headers=auth_headers(tokens)
    ).json()


# --- D13-02: crop cycle season history ---

def test_season_change_creates_a_history_entry(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    assert cycle["season"] == "kharif"

    resp = client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "rabi"}, headers=auth_headers(tokens))
    assert resp.status_code == 200
    assert resp.json()["season"] == "rabi"

    history = client.get(f"/api/v1/crops/{cycle['id']}/season-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert history["items"][0]["season"] == "rabi"
    assert history["items"][0]["crop_cycle_id"] == cycle["id"]


def test_multiple_season_changes_each_create_a_history_entry(client, registered_farmer, sample_crop_id):
    """Perennial crops spanning kharif -> rabi -> zaid over one long-running
    cycle - every change is retained, none overwritten."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "rabi"}, headers=auth_headers(tokens))
    client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "zaid"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/crops/{cycle['id']}/season-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 2
    assert [i["season"] for i in history["items"]] == ["rabi", "zaid"]


def test_updating_to_the_same_season_does_not_create_a_history_entry(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "kharif"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/crops/{cycle['id']}/season-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


def test_season_history_is_isolated_per_farmer(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "rabi"}, headers=auth_headers(tokens))

    _, other_tokens = another_farmer
    resp = client.get(f"/api/v1/crops/{cycle['id']}/season-history", headers=auth_headers(other_tokens))
    assert resp.status_code == 404


# --- D19-04: plot soil history ---

def test_soil_type_change_creates_a_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens, soil_type="loamy")

    resp = client.put(f"/api/v1/plots/{plot['id']}", json={"soil_type": "clayey"}, headers=auth_headers(tokens))
    assert resp.status_code == 200
    assert resp.json()["soil_type"] == "clayey"

    history = client.get(f"/api/v1/plots/{plot['id']}/soil-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert history["items"][0]["soil_type"] == "clayey"
    assert history["items"][0]["plot_id"] == plot["id"]


def test_soil_category_change_alone_also_creates_a_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    resp = client.put(f"/api/v1/plots/{plot['id']}", json={"soil_category": "sandy"}, headers=auth_headers(tokens))
    assert resp.status_code == 200

    history = client.get(f"/api/v1/plots/{plot['id']}/soil-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert history["items"][0]["soil_category"] == "sandy"


def test_updating_to_the_same_soil_type_does_not_create_a_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens, soil_type="loamy")

    client.put(f"/api/v1/plots/{plot['id']}", json={"soil_type": "loamy"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/plots/{plot['id']}/soil-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


def test_unrelated_plot_update_does_not_create_a_soil_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    client.put(f"/api/v1/plots/{plot['id']}", json={"plot_name": "Renamed Plot"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/plots/{plot['id']}/soil-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


# --- D17-02/D17-03/D17-06: plot water availability, shortage, history ---

def test_new_plot_has_no_water_availability_reported(client, registered_farmer):
    """No fabricated default - honestly None until the farmer reports one."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    assert plot["water_availability"] is None
    assert plot["water_shortage"] is None


def test_water_availability_change_creates_a_history_entry_and_is_readable(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    resp = client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "scarce"}, headers=auth_headers(tokens))
    assert resp.status_code == 200
    assert resp.json()["water_availability"] == "scarce"
    assert resp.json()["water_shortage"] is True

    history = client.get(f"/api/v1/plots/{plot['id']}/water-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert history["items"][0]["water_availability"] == "scarce"


def test_adequate_water_availability_is_not_a_shortage(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    resp = client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "adequate"}, headers=auth_headers(tokens))
    assert resp.json()["water_shortage"] is False


def test_updating_to_the_same_water_availability_does_not_create_a_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "limited"}, headers=auth_headers(tokens))

    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "limited"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/plots/{plot['id']}/water-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1


def test_multiple_water_availability_changes_each_create_a_history_entry(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "adequate"}, headers=auth_headers(tokens))
    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "limited"}, headers=auth_headers(tokens))
    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "scarce"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/plots/{plot['id']}/water-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 3
    assert [i["water_availability"] for i in history["items"]] == ["adequate", "limited", "scarce"]


def test_water_history_is_isolated_per_farmer(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    client.put(f"/api/v1/plots/{plot['id']}", json={"water_availability": "scarce"}, headers=auth_headers(tokens))

    _, other_tokens = another_farmer
    resp = client.get(f"/api/v1/plots/{plot['id']}/water-history", headers=auth_headers(other_tokens))
    assert resp.status_code == 404


def test_water_availability_can_be_set_at_plot_creation(client, registered_farmer):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens, water_availability="adequate")
    assert plot["water_availability"] == "adequate"
    assert plot["water_shortage"] is False

    # Creation itself is not a "change" - no prior value existed to change
    # from, mirroring stage/season history's own creation-time convention.
    history = client.get(f"/api/v1/plots/{plot['id']}/water-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


# --- D51-06: harvest listing certificate reference ---

def test_certificate_reference_defaults_to_null(client, farmer_with_crop_cycle):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(
        f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(farmer_tokens)
    ).json()

    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(),
        headers=auth_headers(farmer_tokens),
    ).json()
    assert listing["certificate_reference"] is None


def test_certificate_reference_persists_when_provided(client, farmer_with_crop_cycle):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(
        f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(farmer_tokens)
    ).json()

    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(certificate_reference="ORGANIC-IN-2026-00042"),
        headers=auth_headers(farmer_tokens),
    ).json()
    assert listing["certificate_reference"] == "ORGANIC-IN-2026-00042"
