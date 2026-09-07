"""
Missing Backlog Batch 8 (group 4): D13-04, D55-05
(docs/audit/FINAL_CANONICAL_group_A.md, docs/audit/FINAL_CANONICAL_group_C.md).

Zero-code bonus closure - NOT a new feature. D13-04 ("Perennial Crops:
recurring maintenance") is fully satisfied by two mechanisms already
independently VERIFIED elsewhere in this project: D8-08 (Task.repeat_interval_days -
completing a task auto-creates its own next occurrence) and D13-05
(TaskType.PRUNING - perennial-crop maintenance previously had no dedicated
task-type value). Neither mechanism is crop-lifespan-aware or
season-aware in any way that would make it stop working for a
`season="perennial"` crop cycle - Task.crop_cycle_id scopes generically,
and the recurrence-creation code path never reads `season` at all (see
task_service._maybe_create_next_recurrence). This test proves the
COMBINATION - a recurring PRUNING task against a perennial-season crop
cycle, recurring across multiple completions without ever needing to
close the cycle (a perennial crop cycle IS long-running, unlike an
annual one) - rather than merely asserting it by inference.
"""
from datetime import date, timedelta

from tests.conftest import auth_headers
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from tests.harvest_factories import valid_harvest_listing_payload


def test_recurring_pruning_task_on_a_perennial_crop_cycle_keeps_recurring(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops",
        json=valid_crop_cycle_payload(sample_crop_id, season="perennial"),
        headers=auth_headers(tokens),
    ).json()
    assert cycle["season"] == "perennial"

    due = (date.today() + timedelta(days=1)).isoformat()
    task = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks",
        json={"task_type": "pruning", "title": "Annual pruning", "due_date": due, "repeat_interval_days": 365},
        headers=auth_headers(tokens),
    ).json()
    assert task["task_type"] == "pruning"

    # Complete it twice - a perennial crop cycle is never closed the way
    # an annual one is, so nothing should ever stop this from recurring.
    for _ in range(2):
        items = client.get(f"/api/v1/crop-cycles/{cycle['id']}/tasks", headers=auth_headers(tokens)).json()["items"]
        pending = next(t for t in items if t["title"] == "Annual pruning" and t["status"] == "pending")
        client.post(f"/api/v1/tasks/{pending['id']}/complete", headers=auth_headers(tokens))

    items = client.get(f"/api/v1/crop-cycles/{cycle['id']}/tasks", headers=auth_headers(tokens)).json()["items"]
    pruning_tasks = [t for t in items if t["title"] == "Annual pruning"]
    assert len(pruning_tasks) == 3  # original + 2 recurrences
    assert sum(1 for t in pruning_tasks if t["status"] == "completed") == 2
    assert sum(1 for t in pruning_tasks if t["status"] == "pending") == 1

    # The crop cycle itself is untouched by any of this - still growing,
    # still perennial, never auto-closed by task completion.
    refreshed_cycle = client.get(f"/api/v1/crops/{cycle['id']}", headers=auth_headers(tokens)).json()
    assert refreshed_cycle["season"] == "perennial"
    assert refreshed_cycle["cultivation_status"] == "planned"


# --- D55-05: harvest listing preferred pickup date ---

def test_preferred_pickup_date_defaults_to_null(client, farmer_with_crop_cycle):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(
        f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(farmer_tokens)
    ).json()

    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(),
        headers=auth_headers(farmer_tokens),
    ).json()
    assert listing["preferred_pickup_date"] is None


def test_preferred_pickup_date_persists_when_provided(client, farmer_with_crop_cycle):
    farmer_tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(
        f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(farmer_tokens)
    ).json()

    listing = client.post(
        f"/api/v1/harvests/{harvest['id']}/listing",
        json=valid_harvest_listing_payload(preferred_pickup_date="2026-09-20"),
        headers=auth_headers(farmer_tokens),
    ).json()
    assert listing["preferred_pickup_date"] == "2026-09-20"
