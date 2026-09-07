"""D53-01/02/03/04/05/07, D52-04, D48-04 (docs/audit/FINAL_CANONICAL_group_C.md):
Storage domain - a farmer-owned physical storage facility, and the
episodes of harvest moved into/out of it."""
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload


def _create_storage(client, tokens, **overrides):
    payload = {"location": "North-side godown", "storage_type": "godown", "capacity": "500", "unit": "quintal", "cost_per_unit_per_day": "2.50"}
    payload.update(overrides)
    return client.post("/api/v1/storages", json=payload, headers=auth_headers(tokens)).json()


def _create_harvest(client, tokens, sample_crop_id):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)).json()
    return client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()


def test_farmer_can_create_and_list_storage(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post(
        "/api/v1/storages",
        json={"location": "North-side godown", "storage_type": "godown", "capacity": "500", "unit": "quintal", "cost_per_unit_per_day": "2.50"},
        headers=auth_headers(tokens),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["location"] == "North-side godown"
    assert body["storage_type"] == "godown"
    assert body["capacity"] == "500.00"
    assert body["unit"] == "quintal"
    assert body["cost_per_unit_per_day"] == "2.50"

    listed = client.get("/api/v1/storages", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == body["id"]


def test_storage_capacity_cost_and_unit_are_optional(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/storages", json={"location": "On-farm shed", "storage_type": "on_farm"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["capacity"] is None
    assert body["unit"] is None
    assert body["cost_per_unit_per_day"] is None


def test_farmer_can_delete_their_own_storage(client, registered_farmer):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)

    response = client.delete(f"/api/v1/storages/{storage['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204

    listed = client.get("/api/v1/storages", headers=auth_headers(tokens)).json()
    assert listed["total"] == 0


def test_cannot_delete_another_farmers_storage(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    _, other_tokens = another_farmer

    response = client.delete(f"/api/v1/storages/{storage['id']}", headers=auth_headers(other_tokens))
    assert response.status_code == 404


def test_cannot_list_or_create_usage_for_another_farmers_storage(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    _, other_tokens = another_farmer

    response = client.get(f"/api/v1/storages/{storage['id']}/usages", headers=auth_headers(other_tokens))
    assert response.status_code == 404


def test_farmer_can_record_and_list_storage_usage(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    harvest = _create_harvest(client, tokens, sample_crop_id)

    usage = client.post(
        f"/api/v1/storages/{storage['id']}/usages",
        json={"harvest_record_id": harvest["id"], "quantity": "120", "unit": "kg"},
        headers=auth_headers(tokens),
    )
    assert usage.status_code == 201
    body = usage.json()
    assert body["storage_id"] == storage["id"]
    assert body["harvest_record_id"] == harvest["id"]
    assert body["quantity"] == "120.00"
    assert body["released_at"] is None

    listed = client.get(f"/api/v1/storages/{storage['id']}/usages", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == body["id"]


def test_recording_usage_rejects_another_farmers_harvest_record(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    _, other_tokens = another_farmer
    other_harvest = _create_harvest(client, other_tokens, sample_crop_id)

    response = client.post(
        f"/api/v1/storages/{storage['id']}/usages",
        json={"harvest_record_id": other_harvest["id"], "quantity": "10", "unit": "kg"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


def test_farmer_can_release_storage_usage(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    harvest = _create_harvest(client, tokens, sample_crop_id)
    usage = client.post(
        f"/api/v1/storages/{storage['id']}/usages",
        json={"harvest_record_id": harvest["id"], "quantity": "120", "unit": "kg"},
        headers=auth_headers(tokens),
    ).json()

    released = client.post(f"/api/v1/storages/{storage['id']}/usages/{usage['id']}/release", headers=auth_headers(tokens))
    assert released.status_code == 200
    body = released.json()
    assert body["released_at"] is not None


def test_releasing_storage_usage_is_idempotent(client, registered_farmer, sample_crop_id):
    """A second release call must not overwrite the original release
    timestamp - same idempotency convention as case_service.acknowledge_review (D36-04)."""
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    harvest = _create_harvest(client, tokens, sample_crop_id)
    usage = client.post(
        f"/api/v1/storages/{storage['id']}/usages",
        json={"harvest_record_id": harvest["id"], "quantity": "120", "unit": "kg"},
        headers=auth_headers(tokens),
    ).json()

    first = client.post(f"/api/v1/storages/{storage['id']}/usages/{usage['id']}/release", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/storages/{storage['id']}/usages/{usage['id']}/release", headers=auth_headers(tokens)).json()
    assert first["released_at"] == second["released_at"]


def test_cannot_release_usage_for_another_farmers_storage(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens = registered_farmer
    storage = _create_storage(client, tokens)
    harvest = _create_harvest(client, tokens, sample_crop_id)
    usage = client.post(
        f"/api/v1/storages/{storage['id']}/usages",
        json={"harvest_record_id": harvest["id"], "quantity": "120", "unit": "kg"},
        headers=auth_headers(tokens),
    ).json()
    _, other_tokens = another_farmer

    response = client.post(f"/api/v1/storages/{storage['id']}/usages/{usage['id']}/release", headers=auth_headers(other_tokens))
    assert response.status_code == 404
