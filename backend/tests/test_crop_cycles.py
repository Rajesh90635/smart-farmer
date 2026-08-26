from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload


def _create_plot(client, tokens):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()


def test_crop_master_search(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/crops/master?query=Tom", headers=auth_headers(tokens))
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Tomato" in names


def test_create_crop_cycle(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cultivation_status"] == "planned"
    assert body["crop"]["name"] == "Tomato"


def test_list_crop_cycles_for_plot(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )

    response = client.get(f"/api/v1/plots/{plot['id']}/crops", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_my_crop_cycles_spans_every_farm_and_plot(client, registered_farmer, sample_crop_id):
    """The farmer-wide picker endpoint (added for the Camera tab) - unlike
    /plots/{plot_id}/crops, this must return crop cycles across multiple
    plots without being told which plot to look in."""
    _, tokens = registered_farmer
    plot_a = _create_plot(client, tokens)
    plot_b = _create_plot(client, tokens)
    cycle_a = client.post(
        f"/api/v1/plots/{plot_a['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    cycle_b = client.post(
        f"/api/v1/plots/{plot_b['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    response = client.get("/api/v1/crops", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    ids = [c["id"] for c in body["items"]]
    assert cycle_a["id"] in ids
    assert cycle_b["id"] in ids
    assert body["items"][0]["crop"]["name"] == "Tomato"


def test_list_my_crop_cycles_never_leaks_another_farmers(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens_a = registered_farmer
    plot = _create_plot(client, tokens_a)
    client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens_a))

    _, tokens_b = another_farmer
    response = client.get("/api/v1/crops", headers=auth_headers(tokens_b))
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_plot_can_have_sequential_crop_cycles_preserving_history(client, registered_farmer, sample_crop_id, db_session):
    from sqlalchemy import select

    from app.models.crop_master import CropMaster

    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    onion_id = str(db_session.execute(select(CropMaster).where(CropMaster.name == "Onion")).scalar_one().id)

    tomato_cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    # Close (harvest) the tomato cycle before starting onion, matching the
    # real farmer workflow (Plot A -> Tomato -> harvested -> Onion).
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(
            f"/api/v1/crops/{tomato_cycle['id']}",
            json={"cultivation_status": target_status},
            headers=auth_headers(tokens),
        )
    client.post(
        f"/api/v1/crops/{tomato_cycle['id']}/close",
        json={"actual_harvest_date": "2026-09-05"},
        headers=auth_headers(tokens),
    )

    onion_cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(onion_id, sowing_date="2026-09-10", expected_harvest_date="2026-12-10"),
        headers=auth_headers(tokens),
    )
    assert onion_cycle.status_code == 201

    history = client.get(f"/api/v1/plots/{plot['id']}/crops", headers=auth_headers(tokens)).json()
    assert history["total"] == 2
    statuses = {c["crop"]["name"]: c["cultivation_status"] for c in history["items"]}
    assert statuses["Tomato"] == "harvested"
    assert statuses["Onion"] == "planned"


def test_valid_status_transition_sequence(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        response = client.put(
            f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens)
        )
        assert response.status_code == 200, response.text
        assert response.json()["cultivation_status"] == target_status


def test_invalid_status_transition_is_rejected(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    # PLANNED -> FLOWERING skips SOWN and GROWING - must be rejected.
    response = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "flowering"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_backward_transition_is_rejected(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens))

    response = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "planned"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_cannot_transition_out_of_terminal_status(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "cancelled"}, headers=auth_headers(tokens))

    response = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_cancellation_allowed_from_any_active_status(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens))
    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "growing"}, headers=auth_headers(tokens))

    response = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "cancelled"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["cultivation_status"] == "cancelled"


def test_expected_harvest_before_sowing_is_rejected(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, sowing_date="2026-06-01", expected_harvest_date="2026-05-01"),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_close_crop_cycle_requires_ready_for_harvest_status(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    # Still PLANNED - closing must be rejected.
    response = client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-01"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_close_crop_cycle_success(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cultivation_status"] == "harvested"
    assert body["actual_harvest_date"] == "2026-09-05"


def test_unauthorized_crop_cycle_access_is_rejected(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    plot_a = _create_plot(client, tokens_a)
    cycle_a = client.post(
        f"/api/v1/plots/{plot_a['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens_a)
    ).json()

    get_resp = client.get(f"/api/v1/crops/{cycle_a['id']}", headers=auth_headers(tokens_b))
    assert get_resp.status_code == 404

    put_resp = client.put(
        f"/api/v1/crops/{cycle_a['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens_b)
    )
    assert put_resp.status_code == 404

    close_resp = client.post(
        f"/api/v1/crops/{cycle_a['id']}/close", json={"actual_harvest_date": "2026-09-01"}, headers=auth_headers(tokens_b)
    )
    assert close_resp.status_code == 404


def test_cannot_create_crop_cycle_under_another_farmers_plot(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    plot_a = _create_plot(client, tokens_a)

    response = client.post(
        f"/api/v1/plots/{plot_a['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404
