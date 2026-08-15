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
