import uuid
from datetime import date, datetime, timezone

from app.models.crop_variety import CropVariety
from app.models.crop_cycle_stage_history import CropCycleStageHistory
from app.models.crop_cycle import CultivationStatus
from app.models.harvest_record import HarvestRecord
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


def test_crop_cycle_response_includes_is_closed_flag(client, registered_farmer, sample_crop_id):
    """D7-11 (docs/audit/FINAL_CANONICAL_group_A.md): a read-only
    convenience over the existing HARVESTED/CANCELLED terminal facts."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    assert cycle["is_closed"] is False

    cancelled = client.put(
        f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": "cancelled"}, headers=auth_headers(tokens)
    ).json()
    assert cancelled["is_closed"] is True


def test_create_crop_cycle_response_includes_previous_crop_cycle(client, registered_farmer, sample_crop_id):
    """D3-12 (docs/audit/FINAL_CANONICAL_group_A.md): the plot's own most
    recent prior cycle, for read-only farmer context - never returned for
    a plot's very first cycle."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    headers = auth_headers(tokens)

    first = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()
    assert first["previous_crop_cycle_id"] is None

    client.put(f"/api/v1/crops/{first['id']}", json={"cultivation_status": "cancelled"}, headers=headers)

    second = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, sowing_date="2026-10-01", expected_harvest_date="2027-01-01"),
        headers=headers,
    ).json()
    assert second["previous_crop_cycle_id"] == first["id"]
    assert second["previous_crop_name"] == "Tomato"


def test_create_crop_cycle_suggests_expected_harvest_date_from_variety_duration(client, registered_farmer, sample_crop_id, db_session):
    """D5-04 (docs/audit/FINAL_CANONICAL_group_A.md): a suggestion only,
    never silently written into the farmer's own expected_harvest_date."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    variety = CropVariety(
        crop_id=uuid.UUID(sample_crop_id), name=f"90-Day Hybrid {uuid.uuid4().hex[:8]}", typical_duration_days=90
    )
    db_session.add(variety)
    db_session.commit()
    db_session.refresh(variety)

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(
            sample_crop_id, variety_id=str(variety.id), sowing_date="2026-06-01", expected_harvest_date=None
        ),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["expected_harvest_date"] is None
    assert body["suggested_expected_harvest_date"] == "2026-08-30"


def test_create_crop_cycle_does_not_suggest_a_harvest_date_when_the_farmer_supplied_their_own(
    client, registered_farmer, sample_crop_id, db_session
):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    variety = CropVariety(
        crop_id=uuid.UUID(sample_crop_id), name=f"90-Day Hybrid {uuid.uuid4().hex[:8]}", typical_duration_days=90
    )
    db_session.add(variety)
    db_session.commit()
    db_session.refresh(variety)

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, variety_id=str(variety.id), sowing_date="2026-06-01"),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["suggested_expected_harvest_date"] is None


def test_crop_year_summary_groups_harvests_and_stage_changes_by_year(client, registered_farmer, sample_crop_id, db_session):
    """D13-06 (docs/audit/FINAL_CANONICAL_group_A.md): a long-running cycle
    with real harvest/stage-change rows spanning two calendar years."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    cycle_id = uuid.UUID(cycle["id"])

    from app.models.crop_cycle import CropCycle

    crop_cycle_row = db_session.get(CropCycle, cycle_id)
    db_session.add(
        HarvestRecord(
            farmer_id=crop_cycle_row.plot.farm.farmer_id,
            farm_id=crop_cycle_row.plot.farm_id,
            plot_id=crop_cycle_row.plot_id,
            crop_cycle_id=cycle_id,
            crop_id=crop_cycle_row.crop_id,
            actual_harvest_date=date(2026, 9, 10),
            actual_quantity="50.00",
            unit="kg",
        )
    )
    db_session.add(
        HarvestRecord(
            farmer_id=crop_cycle_row.plot.farm.farmer_id,
            farm_id=crop_cycle_row.plot.farm_id,
            plot_id=crop_cycle_row.plot_id,
            crop_cycle_id=cycle_id,
            crop_id=crop_cycle_row.crop_id,
            actual_harvest_date=date(2027, 9, 10),
            actual_quantity="60.00",
            unit="kg",
        )
    )
    db_session.add(
        CropCycleStageHistory(
            crop_cycle_id=cycle_id,
            status=CultivationStatus.SOWN,
            entered_at=datetime(2026, 6, 5, tzinfo=timezone.utc),
        )
    )
    db_session.add(
        CropCycleStageHistory(
            crop_cycle_id=cycle_id,
            status=CultivationStatus.SOWN,
            entered_at=datetime(2027, 6, 5, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/crops/{cycle['id']}/year-summary", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert [y["year"] for y in body["years"]] == [2026, 2027]
    assert len(body["years"][0]["harvests"]) == 1
    assert body["years"][0]["harvests"][0]["actual_quantity"] == "50.00"
    assert len(body["years"][0]["stage_changes"]) == 1
    assert len(body["years"][1]["harvests"]) == 1
    assert body["years"][1]["harvests"][0]["actual_quantity"] == "60.00"


def test_crop_cycle_response_includes_plot_soil_type(client, registered_farmer, sample_crop_id):
    """D19-05 (docs/audit/FINAL_CANONICAL_group_A.md): pure surfacing of
    the plot's soil descriptors on the crop-cycle response."""
    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json=valid_plot_payload(soil_type="black soil", soil_category="black_cotton"),
        headers=headers,
    ).json()

    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    )
    assert cycle.status_code == 201
    body = cycle.json()
    assert body["plot_soil_type"] == "black soil"
    assert body["plot_soil_category"] == "black_cotton"


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


def test_crop_cycle_can_start_in_land_preparation_and_transition_to_planned(client, registered_farmer, sample_crop_id):
    """D7-01 (docs/audit/FINAL_CANONICAL_group_A.md): an optional
    pre-sowing stage - creation still defaults to PLANNED unless a farmer
    explicitly asks to start earlier."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, initial_status="land_preparation"),
        headers=auth_headers(tokens),
    )
    assert cycle.status_code == 201
    assert cycle.json()["cultivation_status"] == "land_preparation"

    response = client.put(
        f"/api/v1/crops/{cycle.json()['id']}", json={"cultivation_status": "planned"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["cultivation_status"] == "planned"


def test_initial_status_cannot_skip_past_land_preparation_or_planned(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, initial_status="sown"),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_sown_can_optionally_pass_through_germinating_before_growing(client, registered_farmer, sample_crop_id):
    """D7-03: SOWN can still go directly to GROWING (unchanged) - this
    just proves the optional GERMINATING waypoint also works."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    for target_status in ["sown", "germinating", "growing"]:
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


def test_closing_a_crop_cycle_with_no_harvest_or_finances_creates_an_honest_empty_snapshot(client, registered_farmer, sample_crop_id):
    """D97-02..09 (docs/audit/FINAL_CANONICAL_group_D.md): harvest/quality
    fields must be None (never fabricated) when no harvest was ever
    recorded; cost/revenue/profit are 0, matching get_financial_summary's
    own non-nullable-defaults-to-zero contract."""
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
    snapshot = response.json()["closure_snapshot"]
    assert snapshot is not None
    assert snapshot["harvest_quantity"] is None
    assert snapshot["harvest_status"] is None
    assert snapshot["actual_cost"] == "0.00"
    assert snapshot["actual_revenue"] == "0.00"
    assert snapshot["actual_profit_loss"] == "0.00"
    assert snapshot["disease_summary"] == {"total_photos_analyzed": 0, "disease_detected_count": 0, "diseases_observed": []}
    assert snapshot["weather_impact_summary"] == {"weather_alert_count": 0, "categories": []}


def test_closure_snapshot_weather_impact_counts_a_real_crop_alert_notification(client, registered_farmer, sample_crop_id, db_session):
    """A real pre-existing bug found and fixed while implementing D96-08
    (docs/audit/FINAL_CANONICAL_group_D.md): every notification actually
    tied to a crop_cycle entity (weather_alert_orchestration_service.py's
    evaluate_crop_weather_alert candidate) is category 'crop_alert' - the
    closure snapshot's own weather_impact_summary previously filtered for
    'weather_alert'/'rain_alert'/'heavy_rain_alert' only, none of which is
    ever actually tied to a crop_cycle (those are always farm-scoped
    instead), so weather_alert_count was silently always 0 for every crop
    cycle ever closed. Inserting the real notification row directly here
    (rather than wiring up a full weather-provider heavy-rain fixture) is
    a direct, deterministic proof of the fix."""
    from app.models.notification import Notification, NotificationCategory, NotificationPriority

    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    farmer_id = client.get("/api/v1/farmers/me", headers=auth_headers(tokens)).json()["user_id"]
    db_session.add(Notification(
        farmer_id=uuid.UUID(farmer_id), category=NotificationCategory.CROP_ALERT, priority=NotificationPriority.MEDIUM,
        title="Heavy Rain Warning", body="Heavy rain expected for your Tomato crop.", language_code="en",
        dedup_key=f"test_crop_alert:{cycle['id']}", related_entity_type="crop_cycle", related_entity_id=cycle["id"],
    ))
    db_session.commit()

    response = client.post(f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=auth_headers(tokens))
    assert response.status_code == 200
    weather_impact = response.json()["closure_snapshot"]["weather_impact_summary"]
    assert weather_impact["weather_alert_count"] == 1
    assert weather_impact["categories"] == ["crop_alert"]


def test_closing_a_crop_cycle_snapshots_the_linked_harvest_and_ledger(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))

    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/harvests/{harvest['id']}/confirm-ready", json={"estimated_quantity": "800.00"}, headers=auth_headers(tokens))
    client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )

    response = client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    snapshot = response.json()["closure_snapshot"]
    assert snapshot["harvest_quantity"] == "800.00"
    assert snapshot["harvest_status"] == "ready"
    assert snapshot["actual_cost"] == "500.00"


def test_closure_snapshot_stays_frozen_after_a_later_ledger_entry(client, registered_farmer, sample_crop_id):
    """The whole point of a snapshot table over a live aggregate - editing
    the ledger after closure must never change what was already frozen."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))
    client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )

    close_response = client.post(
        f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=auth_headers(tokens)
    )
    assert close_response.json()["closure_snapshot"]["actual_cost"] == "500.00"

    # A later edit to the ledger (allowed - cultivation_status doesn't gate ledger writes).
    client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/ledger/entries",
        json={"entry_type": "expense", "category": "fertilizer", "amount": "1000.00", "entry_date": "2026-09-10"},
        headers=auth_headers(tokens),
    )

    reread = client.get(f"/api/v1/crops/{cycle['id']}", headers=auth_headers(tokens))
    assert reread.json()["closure_snapshot"]["actual_cost"] == "500.00"


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


def test_report_failure_accepts_drought_flood_and_weather_damage_reasons(client, registered_farmer, sample_crop_id):
    """D10-04/D10-05/D10-06 (docs/audit/FINAL_CANONICAL_group_A.md): all
    three enum values already existed in FailureReason - this closes the
    gap of having no test specifically asserting each is accepted."""
    for reason in ["drought", "flood", "weather_damage"]:
        _, tokens = registered_farmer
        plot = _create_plot(client, tokens)
        cycle = client.post(
            f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
        ).json()

        response = client.post(
            f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": reason}, headers=auth_headers(tokens)
        )
        assert response.status_code == 200, response.text
        assert response.json()["failure_reason"] == reason


def test_report_failure_other_reason_requires_a_note(client, registered_farmer, sample_crop_id):
    """D10-07: OTHER is a catch-all with no reason text of its own - a
    note is the only way it carries any real information."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()

    without_note = client.post(
        f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "other"}, headers=auth_headers(tokens)
    )
    assert without_note.status_code == 422

    with_note = client.post(
        f"/api/v1/crops/{cycle['id']}/report-failure",
        json={"failure_reason": "other", "failure_reason_note": "Farmer relocated mid-season"},
        headers=auth_headers(tokens),
    )
    assert with_note.status_code == 200
    assert with_note.json()["failure_reason_note"] == "Farmer relocated mid-season"


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


def test_cannot_create_a_second_active_crop_cycle_on_the_same_plot(client, registered_farmer, sample_crop_id):
    """D6-07/D11-05 (docs/audit/FINAL_CANONICAL_group_A.md): nothing
    previously stopped two non-terminal CropCycle rows existing on one
    plot at once - a real offline-replay/double-tap data-integrity risk."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_can_start_a_new_crop_cycle_once_the_old_one_is_closed(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=auth_headers(tokens))
    client.post(f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    )
    assert response.status_code == 201


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

    client.post(
        f"/api/v1/crops/{cycle['id']}/report-failure",
        json={"failure_reason": "other", "failure_reason_note": "unrelated to this test"},
        headers=auth_headers(tokens),
    )

    task_after = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens)).json()
    assert task_after["status"] == "completed"
