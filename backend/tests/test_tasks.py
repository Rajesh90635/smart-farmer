from datetime import date, timedelta

from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider
from app.services.weather.weather_provider import WeatherReading


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
