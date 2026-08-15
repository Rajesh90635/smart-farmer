from tests.conftest import auth_headers
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
