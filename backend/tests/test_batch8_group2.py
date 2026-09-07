"""
Missing Backlog Batch 8 (group 2): D5-02, D9-08, D50-04, D58-04
(docs/audit/FINAL_CANONICAL_group_A.md, docs/audit/FINAL_CANONICAL_group_C.md).
"""
import uuid

from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload


def _unique_name(prefix: str) -> str:
    """The test database is a real, persistent Postgres instance, never
    truncated between runs (a documented pattern throughout this project's
    own test suite) - crop_varieties.name is unique per crop, so a fixed
    literal would collide on a re-run. A random suffix keeps each test
    run's own row genuinely new."""
    return f"{prefix} {uuid.uuid4().hex[:8]}"


def _create_plot(client, tokens):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()


# --- D5-02: admin-authored crop variety creation ---

def test_admin_can_create_a_crop_variety(client, admin_tokens, sample_crop_id):
    name = _unique_name("Pusa Ruby")
    resp = client.post(
        f"/api/v1/crops/{sample_crop_id}/varieties",
        json={"name": name, "typical_duration_days": 90},
        headers=auth_headers(admin_tokens),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == name
    assert body["typical_duration_days"] == 90
    assert body["crop_id"] == sample_crop_id


def test_created_variety_appears_in_the_farmer_facing_list(client, admin_tokens, registered_farmer, sample_crop_id):
    name = _unique_name("Arka Vikas")
    client.post(
        f"/api/v1/crops/{sample_crop_id}/varieties",
        json={"name": name},
        headers=auth_headers(admin_tokens),
    )
    _, tokens = registered_farmer
    resp = client.get(f"/api/v1/crops/{sample_crop_id}/varieties", headers=auth_headers(tokens))
    names = [v["name"] for v in resp.json()]
    assert name in names


def test_duplicate_variety_name_for_the_same_crop_is_rejected(client, admin_tokens, sample_crop_id):
    name = _unique_name("Duplicate")
    client.post(
        f"/api/v1/crops/{sample_crop_id}/varieties", json={"name": name}, headers=auth_headers(admin_tokens)
    )
    resp = client.post(
        f"/api/v1/crops/{sample_crop_id}/varieties", json={"name": name}, headers=auth_headers(admin_tokens)
    )
    assert resp.status_code == 409


def test_non_admin_cannot_create_a_crop_variety(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    resp = client.post(
        f"/api/v1/crops/{sample_crop_id}/varieties",
        json={"name": _unique_name("Should Fail")},
        headers=auth_headers(tokens),
    )
    assert resp.status_code == 403


# --- D9-08: task partial completion ---

def test_reporting_progress_on_a_pending_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate 5 acres"}, headers=auth_headers(tokens)
    ).json()
    assert task["completion_percentage"] is None

    resp = client.post(
        f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 60}, headers=auth_headers(tokens)
    )
    assert resp.status_code == 200
    assert resp.json()["completion_percentage"] == 60
    assert resp.json()["status"] == "pending"


def test_progress_can_be_updated_multiple_times(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Weed the field"}, headers=auth_headers(tokens)
    ).json()

    client.post(f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 30}, headers=auth_headers(tokens))
    resp = client.post(f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 75}, headers=auth_headers(tokens))
    assert resp.json()["completion_percentage"] == 75


def test_percentage_out_of_range_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)
    ).json()

    resp = client.post(f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 150}, headers=auth_headers(tokens))
    assert resp.status_code == 422


def test_cannot_report_progress_on_a_completed_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    resp = client.post(f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 50}, headers=auth_headers(tokens))
    assert resp.status_code == 409


def test_cannot_report_progress_on_another_farmers_task(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)
    ).json()

    _, other_tokens = another_farmer
    resp = client.post(f"/api/v1/tasks/{task['id']}/report-progress", json={"completion_percentage": 50}, headers=auth_headers(other_tokens))
    assert resp.status_code == 404


# --- D50-04: historical yield ---

def test_yield_history_is_empty_for_a_crop_with_no_recorded_harvests(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    resp = client.get(f"/api/v1/harvests/yield-history/{sample_crop_id}", headers=auth_headers(tokens))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["average_yield"] is None


def test_yield_history_includes_harvests_across_multiple_crop_cycles(client, registered_farmer, sample_crop_id):
    """Two separate plots, each with its own crop cycle for the same crop -
    a plot only ever allows one non-terminal cycle at a time, so this is
    the realistic way two independent past harvests for one crop exist."""
    _, tokens = registered_farmer

    for _ in range(2):
        plot = _create_plot(client, tokens)
        cycle = client.post(
            f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
        ).json()
        harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()
        client.post(
            f"/api/v1/harvests/{harvest['id']}/confirm-ready",
            json={"actual_harvest_date": "2026-09-01", "estimated_quantity": "100.00"},
            headers=auth_headers(tokens),
        )

    resp = client.get(f"/api/v1/harvests/yield-history/{sample_crop_id}", headers=auth_headers(tokens))
    body = resp.json()
    assert len(body["items"]) == 2


def test_average_yield_is_honestly_none_until_actual_quantity_is_ever_populated(client, registered_farmer, sample_crop_id):
    """D50-04's own row discloses this dependency: HarvestRecord.actual_quantity
    is never set anywhere in this codebase today (only estimated_quantity is,
    via confirm-ready) - real per-crop-cycle actual yield recording is D49-02/
    D50-02's own separately-deferred FUTURE work. average_yield must stay
    honestly None rather than silently averaging estimated_quantity instead
    (which would conflate two fields this project deliberately keeps
    distinct)."""
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()
    client.post(
        f"/api/v1/harvests/{harvest['id']}/confirm-ready",
        json={"actual_harvest_date": "2026-09-01", "estimated_quantity": "100.00"},
        headers=auth_headers(tokens),
    )

    resp = client.get(f"/api/v1/harvests/yield-history/{sample_crop_id}", headers=auth_headers(tokens))
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["actual_quantity"] is None
    assert body["average_yield"] is None


def test_yield_history_is_isolated_per_farmer(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens = registered_farmer
    plot = _create_plot(client, tokens)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/harvests/from-crop-cycle/{cycle['id']}", headers=auth_headers(tokens)).json()

    _, other_tokens = another_farmer
    resp = client.get(f"/api/v1/harvests/yield-history/{sample_crop_id}", headers=auth_headers(other_tokens))
    assert resp.json()["items"] == []


def test_yield_history_unknown_crop_returns_404(client, registered_farmer):
    _, tokens = registered_farmer
    import uuid

    resp = client.get(f"/api/v1/harvests/yield-history/{uuid.uuid4()}", headers=auth_headers(tokens))
    assert resp.status_code == 404


# --- D58-04: handling charge itemization ---

def _create_listing(client, tokens, crop_cycle_id, **overrides):
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(**overrides), headers=auth_headers(tokens)
    ).json()


def test_handling_charge_is_included_in_the_itemized_breakdown(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="100.00")

    buyer_tokens, _ = verified_buyer
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers",
        json=valid_offer_payload(quantity="100.00", price_per_unit="30.00"),
        headers=auth_headers(buyer_tokens),
    ).json()

    resp = client.post(
        f"/api/v1/marketplace/offers/{offer['id']}/accept",
        json={"handling_charge": "50.00"},
        headers=auth_headers(farmer_tokens),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["handling_charge"] == "50.00"
    assert body["charges"] == "50.00"
    assert body["net_value"] == "2950.00"


def test_handling_charge_combines_with_other_itemized_charges(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="100.00")

    buyer_tokens, _ = verified_buyer
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers",
        json=valid_offer_payload(quantity="100.00", price_per_unit="30.00"),
        headers=auth_headers(buyer_tokens),
    ).json()

    resp = client.post(
        f"/api/v1/marketplace/offers/{offer['id']}/accept",
        json={"transport_charge": "20.00", "handling_charge": "10.00"},
        headers=auth_headers(farmer_tokens),
    )
    body = resp.json()
    assert body["transport_charge"] == "20.00"
    assert body["handling_charge"] == "10.00"
    assert body["commission_charge"] is None
    assert body["storage_charge"] is None
    assert body["charges"] == "30.00"


def test_handling_charge_defaults_to_null_when_not_supplied(client, farmer_with_crop_cycle, verified_buyer):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    listing = _create_listing(client, farmer_tokens, crop_cycle_id, quantity_available="100.00")

    buyer_tokens, _ = verified_buyer
    offer = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/offers",
        json=valid_offer_payload(quantity="100.00", price_per_unit="30.00"),
        headers=auth_headers(buyer_tokens),
    ).json()

    resp = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=auth_headers(farmer_tokens))
    assert resp.json()["handling_charge"] is None
