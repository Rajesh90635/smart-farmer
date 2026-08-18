import uuid

from app.models.crop_stage_definition import CropStageDefinition
from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload


def _create_plot(client, tokens):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()


# --- CropStageDefinition timing fields (infrastructure only) ---

def test_stage_timing_fields_default_to_null(db_session, sample_crop_id):
    """No agronomic dataset exists in this repository - a freshly created
    stage definition must never have a guessed timing value."""
    stage = CropStageDefinition(
        crop_id=uuid.UUID(sample_crop_id),
        stage_code=f"test_stage_{uuid.uuid4().hex[:8]}",
        display_name="Test Stage",
        sequence_order=99,
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)

    assert stage.typical_days_from_sowing_start is None
    assert stage.typical_days_from_sowing_end is None
    assert stage.sequence_order == 99  # unaffected by the new columns


def test_stage_timing_fields_persist_when_explicitly_supplied(db_session, sample_crop_id):
    stage = CropStageDefinition(
        crop_id=uuid.UUID(sample_crop_id),
        stage_code=f"test_stage_{uuid.uuid4().hex[:8]}",
        display_name="Test Stage 2",
        sequence_order=98,
        typical_days_from_sowing_start=10,
        typical_days_from_sowing_end=20,
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)

    assert stage.typical_days_from_sowing_start == 10
    assert stage.typical_days_from_sowing_end == 20


# --- CropCycleStageHistory ---

def test_status_transition_creates_history_entry(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens))

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert history["items"][0]["status"] == "sown"
    assert history["items"][0]["crop_cycle_id"] == cycle["id"]


def test_multiple_status_transitions_each_create_a_history_entry(client, registered_farmer, sample_crop_id):
    """A crop cycle can have multiple history records - never a
    one-to-one assumption, same reasoning as Phase 0's harvest fix."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    for target_status in ["sown", "growing", "flowering"]:
        response = client.put(
            f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens)
        )
        assert response.status_code == 200

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 3
    statuses_in_order = [h["status"] for h in history["items"]]
    assert statuses_in_order == ["sown", "growing", "flowering"]


def test_close_crop_cycle_creates_a_history_entry_for_harvested(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-01"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 6
    assert history["items"][-1]["status"] == "harvested"


def test_updating_without_changing_status_does_not_create_duplicate_history(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens))

    # Update something unrelated (season) without touching cultivation_status.
    response = client.put(f"/api/v1/crops/{cycle['id']}", json={"season": "rabi"}, headers=auth_headers(tokens))
    assert response.status_code == 200

    # Also explicitly resend the SAME status - must not create a duplicate.
    same_status = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "sown"}, headers=auth_headers(tokens)
    )
    assert same_status.status_code == 200

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 1


def test_invalid_status_transition_still_behaves_exactly_as_before(client, registered_farmer, sample_crop_id):
    """Guards Phase 2 against weakening the existing ALLOWED_TRANSITIONS
    enforcement - an invalid transition must still be rejected with 409,
    and must not create a history entry."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    response = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "flowering"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


def test_history_retrieval_respects_ownership(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens_a = registered_farmer
    plot = _create_plot(client, tokens_a)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens_a)
    ).json()

    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_new_crop_cycle_has_no_stage_history_until_a_transition_happens(client, registered_farmer, sample_crop_id):
    """A freshly created crop cycle (status=PLANNED, no transition yet)
    must have an empty history - a plan or the initial PLANNED status
    alone never creates a history entry."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    history = client.get(f"/api/v1/crops/{cycle['id']}/stage-history", headers=auth_headers(tokens)).json()
    assert history["total"] == 0


def test_existing_crop_cycle_behavior_remains_backward_compatible(client, registered_farmer, sample_crop_id):
    """Guards that Phase 2 didn't alter any existing CropCycle response
    field or status-transition behavior."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cultivation_status"] == "planned"
    assert body["crop"]["name"] == "Tomato"
    assert body["variety_id"] is None
    assert body["seed_variety"] == "Hybrid-1"
