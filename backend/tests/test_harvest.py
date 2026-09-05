from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.harvest_factories import valid_harvest_listing_payload


def test_harvest_created_from_crop_cycle_prefills_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["crop_cycle_id"] == crop_cycle_id
    assert body["status"] == "planned"


def test_calling_get_or_create_twice_returns_same_harvest(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert first["id"] == second["id"]


def test_harvest_never_reaches_ready_without_explicit_farmer_confirmation(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert harvest["status"] == "planned"

    client.post(f"/api/v1/harvests/{harvest['id']}/approaching", headers=auth_headers(tokens))
    still_not_ready = client.get("/api/v1/harvests", headers=auth_headers(tokens)).json()
    assert still_not_ready["items"][0]["status"] == "approaching"

    confirmed = client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1000.00"}, headers=auth_headers(tokens))
    assert confirmed.json()["status"] == "ready"


# --- D47-05: HARVEST_ALERT notification wiring (previously registered but never dispatched) ---

def test_marking_approaching_sends_a_harvest_alert_notification(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    client.post(f"/api/v1/harvests/{harvest['id']}/approaching", headers=auth_headers(tokens))

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    harvest_alerts = [n for n in notifications if n["category"] == "harvest_alert"]
    assert len(harvest_alerts) == 1


def test_confirming_ready_sends_a_harvest_alert_notification(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1000.00"}, headers=auth_headers(tokens))

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    harvest_alerts = [n for n in notifications if n["category"] == "harvest_alert"]
    assert len(harvest_alerts) == 1


def test_correcting_quantity_while_already_ready_does_not_resend_the_notification(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1000.00"}, headers=auth_headers(tokens))

    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1050.00"}, headers=auth_headers(tokens))

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    harvest_alerts = [n for n in notifications if n["category"] == "harvest_alert"]
    assert len(harvest_alerts) == 1


def test_confirm_ready_rejects_regressing_a_harvest_already_past_ready(client, farmer_with_crop_cycle):
    """Real bug fix: confirm-ready used to unconditionally set status back
    to READY, so calling it again to correct a quantity after the harvest
    had already been listed would silently regress LISTED -> READY."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1000.00"}, headers=auth_headers(tokens))
    client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens))

    regression_attempt = client.post(
        f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1200.00"}, headers=auth_headers(tokens)
    )
    assert regression_attempt.status_code == 409

    unchanged = client.get("/api/v1/harvests", headers=auth_headers(tokens)).json()
    assert unchanged["items"][0]["status"] == "listed"


def test_confirm_ready_is_idempotent_while_still_in_ready(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1000.00"}, headers=auth_headers(tokens))

    corrected = client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "1050.00"}, headers=auth_headers(tokens))
    assert corrected.status_code == 200
    assert corrected.json()["status"] == "ready"
    assert corrected.json()["estimated_quantity"] == "1050.00"


def test_create_listing(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens))
    assert response.status_code == 201
    assert response.json()["quantity_available"] == "1000.00"

    harvest_after = client.get("/api/v1/harvests", headers=auth_headers(tokens)).json()
    assert harvest_after["items"][0]["status"] == "listed"


def test_duplicate_active_listing_is_warned_not_silently_created(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens))

    second = client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens))
    assert second.status_code == 409

    forced = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(confirm_duplicate=True), headers=auth_headers(tokens)
    )
    assert forced.status_code == 201


def test_listing_service_area_never_contains_exact_coordinates_by_construction(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    listing = client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)).json()
    assert set(listing["service_area"].keys()) == {"state", "district"}
    assert "latitude" not in listing["service_area"]
    assert "longitude" not in listing["service_area"]


# --- Phase 0: multi-harvest support (tomato/chilli/okra/brinjal/beans/cucumber style repeated picking) ---

def test_one_crop_cycle_can_create_one_harvest_record(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens))
    assert response.status_code == 201
    assert response.json()["crop_cycle_id"] == crop_cycle_id


def test_same_crop_cycle_can_create_a_second_harvest_record(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens)).json()
    assert first["id"] != second["id"]
    assert first["crop_cycle_id"] == second["crop_cycle_id"] == crop_cycle_id


def test_same_crop_cycle_can_create_multiple_independent_harvest_records(client, farmer_with_crop_cycle):
    """Tomato / 2 acres: three separate picking rounds, each an
    independent record - confirming/updating one must never affect the
    others."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    h1 = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=headers).json()
    h2 = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=headers).json()
    h3 = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=headers).json()

    ids = {h1["id"], h2["id"], h3["id"]}
    assert len(ids) == 3

    client.post(f"/api/v1/harvests/{h1['id']}/confirm-ready", json={"actual_harvest_date": "2026-11-01", "estimated_quantity": "500.00"}, headers=headers)
    client.post(f"/api/v1/harvests/{h2['id']}/confirm-ready", json={"actual_harvest_date": "2026-11-08", "estimated_quantity": "350.00"}, headers=headers)
    client.post(f"/api/v1/harvests/{h3['id']}/confirm-ready", json={"actual_harvest_date": "2026-11-15", "estimated_quantity": "275.00"}, headers=headers)

    listed = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=headers).json()
    assert listed["total"] == 3
    quantities = {item["estimated_quantity"] for item in listed["items"]}
    assert quantities == {"500.00", "350.00", "275.00"}
    assert all(item["status"] == "ready" for item in listed["items"])


def test_harvests_from_one_crop_cycle_are_not_returned_for_another(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_a = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_b = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_b = cycle_b["id"]

    client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id_a}/new-harvest", headers=headers)
    client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id_a}/new-harvest", headers=headers)
    client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id_b}/new-harvest", headers=headers)

    for_a = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id_a}", headers=headers).json()
    for_b = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id_b}", headers=headers).json()
    assert for_a["total"] == 2
    assert for_b["total"] == 1
    assert {h["crop_cycle_id"] for h in for_a["items"]} == {crop_cycle_id_a}
    assert {h["crop_cycle_id"] for h in for_b["items"]} == {crop_cycle_id_b}


def test_ownership_still_enforced_for_multi_harvest_endpoints(client, farmer_with_crop_cycle, another_farmer):
    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer

    response = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens_b))
    assert response.status_code == 404

    client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens_a))
    listed_by_b = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens_b))
    assert listed_by_b.status_code == 404


def test_existing_single_harvest_get_or_create_behavior_is_unchanged(client, farmer_with_crop_cycle):
    """Guards the pre-existing idempotency contract: a crop with only one
    harvest must keep working exactly as before Phase 0."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert first["id"] == second["id"]

    listed = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1
