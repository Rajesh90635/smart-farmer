import uuid

from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.harvest_factories import valid_harvest_listing_payload


def _unique_crop(db_session) -> str:
    """A freshly created CropMaster row, not the shared seeded Tomato -
    that accumulates test-created grade options across runs against the
    same persistent test database, which would make grading assertions
    flaky (matches the existing pattern in test_crop_variety.py)."""
    from app.models.crop_master import CropMaster

    crop = CropMaster(name=f"Test-Only Crop {uuid.uuid4().hex[:8]}", is_active=True)
    db_session.add(crop)
    db_session.commit()
    return str(crop.id)


def _create_harvest_for_crop(client, tokens, crop_id: str) -> dict:
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(crop_id), headers=auth_headers(tokens)).json()
    return client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()


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


def test_create_listing_records_sorting_declaration(client, farmer_with_crop_cycle):
    """D52-01 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared
    only, defaults to not-sorted when omitted."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    default_response = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)
    )
    assert default_response.json()["is_sorted"] is False
    assert default_response.json()["sorting_notes"] is None

    harvest2 = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens)).json()
    sorted_response = client.post(
        f"/api/v1/harvests/{harvest2['id']}/listing",
        json=valid_harvest_listing_payload(is_sorted=True, sorting_notes="Removed bruised and undersized produce"),
        headers=auth_headers(tokens),
    )
    assert sorted_response.json()["is_sorted"] is True
    assert sorted_response.json()["sorting_notes"] == "Removed bruised and undersized produce"


def test_create_listing_records_packing_requirements(client, farmer_with_crop_cycle):
    """D52-03 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared
    only, honestly None (not fabricated empty text) when omitted."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    default_response = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=auth_headers(tokens)
    )
    assert default_response.json()["packing_requirements"] is None

    harvest2 = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}/new-harvest", headers=auth_headers(tokens)).json()
    packed_response = client.post(
        f"/api/v1/harvests/{harvest2['id']}/listing",
        json=valid_harvest_listing_payload(packing_requirements="50kg jute bags, no plastic"),
        headers=auth_headers(tokens),
    )
    assert packed_response.json()["packing_requirements"] == "50kg jute bags, no plastic"


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


# --- D47-01: mark_approaching audit log + explicit rejection on a wrong-status call ---

def test_marking_approaching_is_audit_logged(client, farmer_with_crop_cycle, db_session):
    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    client.post(f"/api/v1/harvests/{harvest['id']}/approaching", headers=auth_headers(tokens))

    entries = db_session.execute(
        select(AuditLog).where(AuditLog.entity == "harvest_record", AuditLog.entity_id == harvest["id"])
    ).scalars().all()
    assert any(e.action == "HARVEST_MARKED_APPROACHING" for e in entries)


def test_marking_approaching_twice_is_rejected_not_a_silent_noop(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    first = client.post(f"/api/v1/harvests/{harvest['id']}/approaching", headers=auth_headers(tokens))
    assert first.status_code == 200

    second = client.post(f"/api/v1/harvests/{harvest['id']}/approaching", headers=auth_headers(tokens))
    assert second.status_code == 409


# --- D51-02/D51-04: moisture_percent/defect_notes round-trip at confirm-ready ---

def test_confirm_ready_persists_moisture_and_defect_notes(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()

    response = client.post(
        f"/api/v1/harvests/{harvest['id']}/confirm-ready",
        json={"estimated_quantity": "1000.00", "moisture_percent": "12.50", "defect_notes": "A few bruised tomatoes near the bottom crate."},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["moisture_percent"] == "12.50"
    assert body["defect_notes"] == "A few bruised tomatoes near the bottom crate."


def test_existing_single_harvest_get_or_create_behavior_is_unchanged(client, farmer_with_crop_cycle):
    """Guards the pre-existing idempotency contract: a crop with only one
    harvest must keep working exactly as before Phase 0."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert first["id"] == second["id"]

    listed = client.get(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1


# --- D52-02/D51-03: formal per-crop grading engine ---

def test_admin_can_configure_grade_options_for_a_crop(client, registered_farmer, admin_tokens, db_session):
    crop_id = _unique_crop(db_session)
    response = client.post(
        f"/api/v1/crops/master/{crop_id}/grade-options",
        json={"grade_code": "GRADE_A", "display_name": "Grade A (Premium)", "sort_order": 1},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 201
    assert response.json()["grade_code"] == "GRADE_A"

    _, farmer_tokens = registered_farmer
    listed = client.get(f"/api/v1/crops/master/{crop_id}/grade-options", headers=auth_headers(farmer_tokens))
    assert listed.status_code == 200
    assert [o["grade_code"] for o in listed.json()] == ["GRADE_A"]


def test_duplicate_grade_code_for_the_same_crop_is_rejected(client, admin_tokens, db_session):
    crop_id = _unique_crop(db_session)
    client.post(
        f"/api/v1/crops/master/{crop_id}/grade-options",
        json={"grade_code": "GRADE_A", "display_name": "Grade A"},
        headers=auth_headers(admin_tokens),
    )
    duplicate = client.post(
        f"/api/v1/crops/master/{crop_id}/grade-options",
        json={"grade_code": "GRADE_A", "display_name": "Grade A (again)"},
        headers=auth_headers(admin_tokens),
    )
    assert duplicate.status_code == 409


def test_farmer_cannot_configure_grade_options(client, registered_farmer, db_session):
    crop_id = _unique_crop(db_session)
    _, tokens = registered_farmer
    response = client.post(
        f"/api/v1/crops/master/{crop_id}/grade-options",
        json={"grade_code": "GRADE_A", "display_name": "Grade A"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 403


def test_listing_quality_grade_stays_free_text_when_no_options_configured(client, registered_farmer, db_session):
    """D52-02: an unconfigured crop must never block a farmer's listing
    over a schema nobody has actually set up."""
    crop_id = _unique_crop(db_session)
    _, tokens = registered_farmer
    harvest = _create_harvest_for_crop(client, tokens, crop_id)

    response = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(quality_grade="Whatever the farmer wants to call it"),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201


def test_listing_quality_grade_is_validated_once_options_are_configured(client, registered_farmer, admin_tokens, db_session):
    crop_id = _unique_crop(db_session)
    client.post(
        f"/api/v1/crops/master/{crop_id}/grade-options",
        json={"grade_code": "GRADE_A", "display_name": "Grade A"},
        headers=auth_headers(admin_tokens),
    )

    _, tokens = registered_farmer
    harvest = _create_harvest_for_crop(client, tokens, crop_id)

    rejected = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(quality_grade="Not A Real Grade"),
        headers=auth_headers(tokens),
    )
    assert rejected.status_code == 422

    accepted = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(quality_grade="GRADE_A"),
        headers=auth_headers(tokens),
    )
    assert accepted.status_code == 201
