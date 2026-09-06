from datetime import date, timedelta

from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider
from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload
from app.services.weather.weather_provider import WeatherReading


def _create_plot(client, tokens):
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    return client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()


def test_create_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"task_type": "irrigation", "title": "Check drip lines"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["display_status"] == "pending"
    assert body["title"] == "Check drip lines"


def test_task_calendar_groups_tasks_by_date_across_crop_cycles(client, registered_farmer, sample_crop_id):
    """D8-01 (docs/audit/FINAL_CANONICAL_group_A.md): a farmer-level,
    date-grouped view spanning two different plots/crop cycles."""
    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    plot_a = _create_plot(client, tokens)
    plot_b = _create_plot(client, tokens)
    cycle_a = client.post(
        f"/api/v1/plots/{plot_a['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()
    cycle_b = client.post(
        f"/api/v1/plots/{plot_b['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()

    client.post(
        f"/api/v1/crop-cycles/{cycle_a['id']}/tasks",
        json={"title": "Weed plot A", "due_date": "2026-07-01"},
        headers=headers,
    )
    client.post(
        f"/api/v1/crop-cycles/{cycle_b['id']}/tasks",
        json={"title": "Weed plot B", "due_date": "2026-07-01"},
        headers=headers,
    )
    client.post(
        f"/api/v1/crop-cycles/{cycle_a['id']}/tasks",
        json={"title": "Fertilize plot A", "due_date": "2026-07-15"},
        headers=headers,
    )
    client.post(
        f"/api/v1/crop-cycles/{cycle_a['id']}/tasks", json={"title": "No due date yet"}, headers=headers
    )

    response = client.get("/api/v1/farmers/me/tasks/calendar", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    dated_groups = [g for g in body["groups"] if g["due_date"] is not None]
    assert [g["due_date"] for g in dated_groups] == ["2026-07-01", "2026-07-15"]
    assert len(dated_groups[0]["tasks"]) == 2
    assert {t["crop_cycle_id"] for t in dated_groups[0]["tasks"]} == {cycle_a["id"], cycle_b["id"]}
    undated_group = next(g for g in body["groups"] if g["due_date"] is None)
    assert len(undated_group["tasks"]) == 1


def test_task_calendar_never_leaks_another_farmers_tasks(client, registered_farmer, another_farmer, sample_crop_id):
    _, tokens_a = registered_farmer
    plot = _create_plot(client, tokens_a)
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens_a)
    ).json()
    client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks", json={"title": "Farmer A's task"}, headers=auth_headers(tokens_a)
    )

    _, tokens_b = another_farmer
    response = client.get("/api/v1/farmers/me/tasks/calendar", headers=auth_headers(tokens_b))
    assert response.status_code == 200
    assert response.json() == {"groups": [], "total": 0}


def test_cannot_create_task_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Sneaky task"}, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_task_with_future_due_date_is_not_overdue(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    future = (date.today() + timedelta(days=5)).isoformat()
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Future task", "due_date": future}, headers=auth_headers(tokens)
    )
    assert response.json()["display_status"] == "pending"


def test_task_with_past_due_date_is_overdue(client, farmer_with_crop_cycle, db_session):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from app.core.jwt import decode_access_token
    from app.models.task import Task
    import uuid

    farmer_id = decode_access_token(tokens["access_token"])["sub"]
    task = Task(
        farmer_id=uuid.UUID(farmer_id),
        crop_cycle_id=uuid.UUID(crop_cycle_id),
        title="Overdue task",
        due_date=date.today() - timedelta(days=3),
    )
    db_session.add(task)
    db_session.commit()

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers(tokens))
    assert response.json()["display_status"] == "overdue"
    assert response.json()["status"] == "pending"


def test_task_with_no_due_date_is_never_overdue(client, farmer_with_crop_cycle, db_session):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from app.core.jwt import decode_access_token
    from app.models.task import Task
    import uuid
    from datetime import datetime, timezone

    farmer_id = decode_access_token(tokens["access_token"])["sub"]
    task = Task(farmer_id=uuid.UUID(farmer_id), crop_cycle_id=uuid.UUID(crop_cycle_id), title="No due date task", due_date=None)
    db_session.add(task)
    db_session.commit()
    task.created_at = datetime.now(timezone.utc) - timedelta(days=365)
    db_session.commit()

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers(tokens))
    assert response.json()["display_status"] == "pending"


def test_complete_task_requires_explicit_action(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["display_status"] == "completed"
    assert body["completed_at"] is not None


def test_completed_task_is_never_overdue_even_with_a_past_due_date(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    past = (date.today() - timedelta(days=10)).isoformat()
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T", "due_date": past}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    response = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens))
    assert response.json()["display_status"] == "completed"


def test_cannot_complete_an_already_completed_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    response = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))
    assert response.status_code == 409


def test_cancel_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)).json()

    response = client.post(f"/api/v1/tasks/{task['id']}/cancel", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["display_status"] == "cancelled"


def test_unauthorized_task_access_is_rejected(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    task = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "T"}, headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_weather_advisory_attached_to_pending_spraying_task_reusing_step15_rule(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"task_type": "spraying", "title": "Spray for aphids"}, headers=auth_headers(tokens)
    )

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens))

    assert response.status_code == 200
    tasks = response.json()["items"]
    spraying_task = next(t for t in tasks if t["task_type"] == "spraying")
    assert spraying_task["weather_advisory"] is not None
    assert spraying_task["weather_advisory"]["action"] == "avoid_spraying"
    assert spraying_task["weather_advisory"]["basis"] == "high_wind"


def test_no_weather_advisory_when_conditions_are_normal(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"task_type": "spraying", "title": "Spray for aphids"}, headers=auth_headers(tokens)
    )

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, wind_speed_kmh=10.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens))

    spraying_task = next(t for t in response.json()["items"] if t["task_type"] == "spraying")
    assert spraying_task["weather_advisory"] is None


def test_non_spraying_task_never_gets_a_weather_advisory(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"task_type": "irrigation", "title": "Check drip lines"}, headers=auth_headers(tokens)
    )

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens))

    irrigation_task = next(t for t in response.json()["items"] if t["task_type"] == "irrigation")
    assert irrigation_task["weather_advisory"] is None


def test_completed_spraying_task_never_gets_a_weather_advisory(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"task_type": "spraying", "title": "Spray"}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens))

    spraying_task = next(t for t in response.json()["items"] if t["task_type"] == "spraying")
    assert spraying_task["weather_advisory"] is None


def test_task_dependency_blocks_completion_until_dependency_is_completed(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    prerequisite = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Prepare soil"}, headers=auth_headers(tokens)
    ).json()
    dependent = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Sow seeds", "depends_on_task_id": prerequisite["id"]},
        headers=auth_headers(tokens),
    ).json()
    assert dependent["depends_on_task_id"] == prerequisite["id"]
    assert dependent["dependency_completed"] is False

    blocked = client.post(f"/api/v1/tasks/{dependent['id']}/complete", headers=auth_headers(tokens))
    assert blocked.status_code == 409

    client.post(f"/api/v1/tasks/{prerequisite['id']}/complete", headers=auth_headers(tokens))
    still_blocked_check = client.get(f"/api/v1/tasks/{dependent['id']}", headers=auth_headers(tokens))
    assert still_blocked_check.json()["dependency_completed"] is True

    allowed = client.post(f"/api/v1/tasks/{dependent['id']}/complete", headers=auth_headers(tokens))
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "completed"


def test_task_dependency_must_be_in_the_same_crop_cycle(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    other_farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()
    other_plot = client.post(f"/api/v1/farms/{other_farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)).json()
    other_cycle = client.post(
        f"/api/v1/plots/{other_plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=auth_headers(tokens)
    ).json()
    other_task = client.post(
        f"/api/v1/crop-cycles/{other_cycle['id']}/tasks", json={"title": "Unrelated task"}, headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Sow seeds", "depends_on_task_id": other_task["id"]},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422


def test_task_dependency_must_exist(client, farmer_with_crop_cycle):
    import uuid

    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Sow seeds", "depends_on_task_id": str(uuid.uuid4())},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


def test_completing_a_recurring_task_creates_the_next_occurrence(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    due = (date.today() + timedelta(days=2)).isoformat()
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Water the field", "due_date": due, "repeat_interval_days": 7},
        headers=auth_headers(tokens),
    ).json()

    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    items = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens)).json()["items"]
    next_occurrences = [t for t in items if t["title"] == "Water the field" and t["status"] == "pending"]
    assert len(next_occurrences) == 1
    expected_due = (date.today() + timedelta(days=2 + 7)).isoformat()
    assert next_occurrences[0]["due_date"] == expected_due
    assert next_occurrences[0]["repeat_interval_days"] == 7


def test_completing_a_non_recurring_task_creates_no_new_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "One-off task"}, headers=auth_headers(tokens)
    ).json()

    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    items = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens)).json()["items"]
    assert len(items) == 1


def test_completing_a_recurring_task_after_crop_cycle_closed_does_not_recur(client, registered_farmer, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()

    task = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks",
        json={"title": "Water the field", "repeat_interval_days": 7},
        headers=headers,
    ).json()

    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=headers)
    client.post(f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=headers)

    # The task itself is already CANCELLED by the close-cycle auto-cancel
    # (D9-15) - completion is no longer reachable, confirming there is no
    # path left for a stray recurrence to be created from it.
    completed = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers)
    assert completed.status_code == 409


def test_cannot_create_a_task_for_a_closed_crop_cycle(client, registered_farmer, sample_crop_id):
    """D97-12 (docs/audit/FINAL_CANONICAL_group_D.md, BROKEN): create_task
    used to never check cultivation_status at all, unlike its sibling
    guards in complete_task/cancel_all_pending_for_crop_cycle - a farmer
    double-tap or a replayed offline-queued create could attach a live
    task to a HARVESTED/CANCELLED cycle."""
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()

    for target_status in ["sown", "growing", "flowering", "fruiting", "ready_for_harvest"]:
        client.put(f"/api/v1/crops/{cycle['id']}", json={"cultivation_status": target_status}, headers=headers)
    client.post(f"/api/v1/crops/{cycle['id']}/close", json={"actual_harvest_date": "2026-09-05"}, headers=headers)

    response = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks",
        json={"title": "Water the field"},
        headers=headers,
    )
    assert response.status_code == 409


def test_can_create_a_task_for_a_cancelled_crop_cycle_is_also_rejected(client, registered_farmer, sample_crop_id):
    """Same guard, CANCELLED branch (re-sowing's failure path) rather than
    HARVESTED (season closure's success path)."""
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    client.post(f"/api/v1/crops/{cycle['id']}/report-failure", json={"failure_reason": "pest"}, headers=headers)

    response = client.post(
        f"/api/v1/crop-cycles/{cycle['id']}/tasks",
        json={"title": "Water the field"},
        headers=headers,
    )
    assert response.status_code == 409


# --- Task update/skip/fail (D9-05/D9-06/D9-09/D9-10/D9-12) ---

def test_reschedule_task_to_new_due_date(client, farmer_with_crop_cycle):
    """D9-05/D9-06: one shared endpoint serves both snooze and reschedule."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Irrigate", "due_date": date.today().isoformat()},
        headers=auth_headers(tokens),
    ).json()

    new_due = (date.today() + timedelta(days=5)).isoformat()
    response = client.patch(f"/api/v1/tasks/{task['id']}", json={"due_date": new_due}, headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["due_date"] == new_due


def test_cannot_reschedule_a_completed_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    response = client.patch(
        f"/api/v1/tasks/{task['id']}", json={"due_date": date.today().isoformat()}, headers=auth_headers(tokens)
    )
    assert response.status_code == 409


def test_skip_recurring_task_generates_next_occurrence_without_completing_current(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    due = date.today().isoformat()
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Spray", "due_date": due, "repeat_interval_days": 7},
        headers=auth_headers(tokens),
    ).json()

    response = client.post(
        f"/api/v1/tasks/{task['id']}/skip", json={"reason": "rain expected"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancellation_reason"] == "rain expected"

    items = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", headers=auth_headers(tokens)).json()["items"]
    next_occurrences = [t for t in items if t["title"] == "Spray" and t["status"] == "pending"]
    assert len(next_occurrences) == 1
    assert next_occurrences[0]["due_date"] == (date.today() + timedelta(days=7)).isoformat()


def test_cannot_skip_a_non_recurring_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "One-off"}, headers=auth_headers(tokens)
    ).json()

    response = client.post(f"/api/v1/tasks/{task['id']}/skip", headers=auth_headers(tokens))
    assert response.status_code == 422


def test_cancel_task_can_include_a_reason(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/tasks/{task['id']}/cancel", json={"reason": "no longer needed"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["cancellation_reason"] == "no longer needed"


def test_task_can_be_marked_failed_with_reason(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/tasks/{task['id']}/fail", json={"reason": "pump broke"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["display_status"] == "failed"
    assert response.json()["cancellation_reason"] == "pump broke"


def test_cannot_fail_an_already_completed_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()
    client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    response = client.post(f"/api/v1/tasks/{task['id']}/fail", headers=auth_headers(tokens))
    assert response.status_code == 409


def test_task_priority_defaults_to_medium_and_is_settable(client, farmer_with_crop_cycle):
    """D37-03: a general task-priority field."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    default_task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate"}, headers=auth_headers(tokens)
    ).json()
    assert default_task["priority"] == "medium"

    high_task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Urgent spray", "priority": "high"},
        headers=auth_headers(tokens),
    ).json()
    assert high_task["priority"] == "high"


# --- Overdue task alert sweep (D9-16/D9-03/D78-01/D37-04) ---

def test_overdue_sweep_sends_one_alert_and_never_duplicates(client, farmer_with_crop_cycle, db_session):
    """The sweep's return value is a global sweep-wide count, not scoped to
    this test's own task - the shared test database can have other
    still-unalerted overdue tasks sitting around from other test runs,
    which would inflate an exact count (same hazard already fixed for
    run_expiry_check_sweep's own tests). Assert on this task's own alerted
    state and this farmer's own notifications instead."""
    import uuid
    from datetime import datetime, timezone

    from app.core.config import get_settings
    from app.models.task import Task
    from app.services.task_service import run_overdue_task_alert_sweep

    tokens, crop_cycle_id = farmer_with_crop_cycle
    # UTC, matching run_overdue_task_alert_sweep's own "today" exactly -
    # date.today() (local) would be off by one whenever local time and
    # UTC straddle midnight on different calendar days.
    utc_today = datetime.now(timezone.utc).date()
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"title": "Overdue irrigation", "due_date": (utc_today - timedelta(days=1)).isoformat()},
        headers=auth_headers(tokens),
    ).json()

    settings = get_settings()
    run_overdue_task_alert_sweep(db_session, settings)
    stored_task = db_session.get(Task, uuid.UUID(task["id"]))
    assert stored_task.overdue_alerted_at is not None

    run_overdue_task_alert_sweep(db_session, settings)  # must never duplicate

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    task_alerts = [n for n in notifications if n["category"] == "task_alert" and n["related_entity_id"] == task["id"]]
    assert len(task_alerts) == 1


def test_overdue_sweep_ignores_tasks_without_a_due_date(client, farmer_with_crop_cycle, db_session):
    import uuid

    from app.core.config import get_settings
    from app.models.task import Task
    from app.services.task_service import run_overdue_task_alert_sweep

    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "No due date"}, headers=auth_headers(tokens)
    ).json()

    run_overdue_task_alert_sweep(db_session, get_settings())
    stored_task = db_session.get(Task, uuid.UUID(task["id"]))
    assert stored_task.overdue_alerted_at is None
