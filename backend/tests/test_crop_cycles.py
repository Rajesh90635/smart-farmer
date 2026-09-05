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


def test_close_crop_cycle_records_lessons_learned(client, registered_farmer, sample_crop_id):
    """D97-10 (docs/FINAL_GAP_REPORT.md): only settable at the moment of
    closing the cycle, never editable afterward."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/close",
        json={"actual_harvest_date": "2026-09-05", "lessons_learned": "Should have staked the plants earlier."},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    assert response.json()["lessons_learned"] == "Should have staked the plants earlier."


def test_close_crop_cycle_without_lessons_learned_leaves_it_none(client, registered_farmer, sample_crop_id):
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
    assert response.json()["lessons_learned"] is None


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


# --- Crop failure / re-sowing (D10-01/D10-02/D10-09/D10-10/D11-01) ---

def test_report_crop_failure_captures_reason_and_recommendation(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "disease"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cultivation_status"] == "cancelled"
    assert body["failure_reason"] == "disease"
    assert body["recommended_next_action"] is not None
    assert "resistant" in body["recommended_next_action"].lower()


def test_report_crop_failure_is_distinguishable_from_a_plain_cancel(client, registered_farmer, sample_crop_id):
    """A plain PUT cancel (farmer changed their mind) must leave
    failure_reason unset - only report-failure sets it."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    response = client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "cancelled"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["cultivation_status"] == "cancelled"
    assert response.json()["failure_reason"] is None


def test_cannot_report_failure_on_an_already_terminal_crop_cycle(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "pest"}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "drought"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_resowing_links_new_cycle_to_the_failed_one(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    failed = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/crops/{failed['id']}/report-failure", json={"failure_reason": "flood"}, headers=auth_headers(tokens))

    resown = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, resown_from_crop_cycle_id=failed["id"]),
        headers=auth_headers(tokens),
    )
    assert resown.status_code == 201
    assert resown.json()["resown_from_crop_cycle_id"] == failed["id"]


def test_resowing_rejects_a_source_cycle_that_is_not_cancelled(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    active = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, resown_from_crop_cycle_id=active["id"]),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_resowing_rejects_a_source_cycle_from_a_different_plot(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot_1 = _create_plot(client, tokens)
    plot_2 = _create_plot(client, tokens)
    failed = client.post(
        f"/api/v1/plots/{plot_1['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/crops/{failed['id']}/report-failure", json={"failure_reason": "pest"}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/plots/{plot_2['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, resown_from_crop_cycle_id=failed["id"]),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_reporting_failure_auto_cancels_pending_tasks(client, registered_farmer, sample_crop_id):
    """D9-15: a task still PENDING for a crop cycle that just ended must
    not stay open/overdue forever with no crop cycle left to act on."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    task = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()

    client.post(f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "drought"}, headers=auth_headers(tokens))

    task_after = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens)).json()
    assert task_after["status"] == "cancelled"


def test_closing_crop_cycle_auto_cancels_pending_tasks(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    task = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-01"}, headers=auth_headers(tokens)
    )

    task_after = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens)).json()
    assert task_after["status"] == "cancelled"


def test_auto_cancel_never_touches_an_already_completed_task(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    task = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    client.post(f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "other"}, headers=auth_headers(tokens))

    task_after = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens)).json()
    assert task_after["status"] == "completed"
