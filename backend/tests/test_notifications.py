from datetime import time

from tests.conftest import auth_headers, override_weather_provider
from tests.weather_factories import heavy_rain_provider


def test_get_default_notification_preferences(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/notification-preferences", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["weather_alerts_enabled"] is True
    assert body["audio_alerts_enabled"] is False


def test_update_notification_preferences(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.put(
        "/api/v1/notification-preferences",
        json={"rain_alerts_enabled": False, "quiet_hours_start": "22:00:00", "quiet_hours_end": "06:00:00"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rain_alerts_enabled"] is False
    assert body["quiet_hours_start"] == "22:00:00"


def test_weather_check_creates_a_rain_notification(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    response = client.get("/api/v1/notifications", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    categories = {n["category"] for n in body["items"]}
    assert "heavy_rain_alert" in categories


def test_repeated_weather_checks_do_not_duplicate_the_same_alert(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    response = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    heavy_rain_notifications = [n for n in response["items"] if n["category"] == "heavy_rain_alert"]
    assert len(heavy_rain_notifications) == 1


def test_disabling_rain_alerts_suppresses_new_rain_notifications(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    client.put("/api/v1/notification-preferences", json={"rain_alerts_enabled": False}, headers=auth_headers(tokens))

    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    response = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    assert response["total"] == 0


def test_mark_notification_read(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    listing = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    notification_id = listing["items"][0]["id"]
    assert listing["unread_count"] >= 1

    response = client.post(f"/api/v1/notifications/{notification_id}/read", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["read_at"] is not None


def test_mark_all_read(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    response = client.post("/api/v1/notifications/read-all", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["marked_read"] >= 1

    listing = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    assert listing["unread_count"] == 0


def test_farmer_a_cannot_read_farmer_bs_notification(client, farmer_with_located_farm, another_farmer):
    tokens_a, farm_id = farmer_with_located_farm
    _, tokens_b = another_farmer

    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens_a))

    notification_id = client.get("/api/v1/notifications", headers=auth_headers(tokens_a)).json()["items"][0]["id"]

    response = client.post(f"/api/v1/notifications/{notification_id}/read", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_farmer_a_cannot_see_farmer_bs_notifications_in_list(client, farmer_with_located_farm, another_farmer):
    tokens_a, farm_id = farmer_with_located_farm
    _, tokens_b = another_farmer

    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens_a))

    response = client.get("/api/v1/notifications", headers=auth_headers(tokens_b)).json()
    assert response["total"] == 0


class TestQuietHours:
    def test_time_within_normal_range(self):
        from app.models.notification_preference import NotificationPreference
        from app.services.notification_service import is_within_quiet_hours

        prefs = NotificationPreference(quiet_hours_start=time(22, 0), quiet_hours_end=time(23, 0))
        assert is_within_quiet_hours(time(22, 30), prefs) is True
        assert is_within_quiet_hours(time(21, 0), prefs) is False

    def test_overnight_wraparound_range(self):
        from app.models.notification_preference import NotificationPreference
        from app.services.notification_service import is_within_quiet_hours

        prefs = NotificationPreference(quiet_hours_start=time(22, 0), quiet_hours_end=time(6, 0))
        assert is_within_quiet_hours(time(23, 0), prefs) is True
        assert is_within_quiet_hours(time(3, 0), prefs) is True
        assert is_within_quiet_hours(time(12, 0), prefs) is False

    def test_no_quiet_hours_configured(self):
        from app.models.notification_preference import NotificationPreference
        from app.services.notification_service import is_within_quiet_hours

        prefs = NotificationPreference()
        assert is_within_quiet_hours(time(23, 0), prefs) is False
