from app.core.config import get_settings
from app.core.farmer_messages import get_message
from app.services.weather.weather_provider import WeatherReading
from app.services.weather_alert_rules import (
    evaluate_crop_weather_alert,
    evaluate_extreme_weather_alerts,
    evaluate_rain_alerts,
    evaluate_spray_condition_warning,
)

settings = get_settings()


class TestRainAlerts:
    def test_no_alert_below_threshold(self):
        reading = WeatherReading(rain_probability_percent=10)
        assert evaluate_rain_alerts(reading, settings) == []

    def test_light_rain_alert_at_threshold(self):
        reading = WeatherReading(rain_probability_percent=settings.weather_rain_probability_threshold)
        candidates = evaluate_rain_alerts(reading, settings)
        assert len(candidates) == 1
        assert candidates[0].category.value == "rain_alert"
        assert candidates[0].priority.value == "low"

    def test_heavy_rain_alert_by_probability(self):
        reading = WeatherReading(rain_probability_percent=settings.weather_heavy_rain_probability_threshold)
        candidates = evaluate_rain_alerts(reading, settings)
        assert candidates[0].category.value == "heavy_rain_alert"
        assert candidates[0].priority.value == "high"

    def test_heavy_rain_alert_by_mm_even_with_lower_probability(self):
        reading = WeatherReading(rain_probability_percent=45, rainfall_mm=settings.weather_heavy_rain_mm_threshold)
        candidates = evaluate_rain_alerts(reading, settings)
        assert candidates[0].category.value == "heavy_rain_alert"

    def test_no_data_produces_no_alert(self):
        assert evaluate_rain_alerts(None, settings) == []
        assert evaluate_rain_alerts(WeatherReading(), settings) == []

    def test_never_claims_certainty(self):
        reading = WeatherReading(rain_probability_percent=95)
        candidates = evaluate_rain_alerts(reading, settings)
        assert "probability" in candidates[0].message_params


class TestExtremeWeatherAlerts:
    def test_high_wind_detected(self):
        reading = WeatherReading(wind_speed_kmh=settings.weather_high_wind_kmh_threshold)
        keys = [c.message_key for c in evaluate_extreme_weather_alerts(reading, settings)]
        assert "high_wind_alert" in keys

    def test_extreme_heat_detected(self):
        reading = WeatherReading(temperature_c=settings.weather_extreme_heat_celsius_threshold)
        keys = [c.message_key for c in evaluate_extreme_weather_alerts(reading, settings)]
        assert "extreme_heat_alert" in keys

    def test_extreme_cold_detected(self):
        reading = WeatherReading(temperature_c=settings.weather_extreme_cold_celsius_threshold)
        keys = [c.message_key for c in evaluate_extreme_weather_alerts(reading, settings)]
        assert "extreme_cold_alert" in keys

    def test_normal_weather_produces_no_alerts(self):
        reading = WeatherReading(temperature_c=25, wind_speed_kmh=10)
        assert evaluate_extreme_weather_alerts(reading, settings) == []

    def test_no_data_produces_no_alert(self):
        assert evaluate_extreme_weather_alerts(None, settings) == []


class TestCropWeatherAlert:
    def test_fires_on_heavy_rain(self):
        reading = WeatherReading(rain_probability_percent=settings.weather_heavy_rain_probability_threshold)
        candidate = evaluate_crop_weather_alert(crop_name="Tomato", cultivation_status="flowering", forecast_today=reading, settings=settings)
        assert candidate is not None
        assert candidate.message_params["crop_name"] == "Tomato"
        assert candidate.message_params["stage"] == "flowering"

    def test_no_alert_on_light_rain(self):
        reading = WeatherReading(rain_probability_percent=20)
        candidate = evaluate_crop_weather_alert(crop_name="Tomato", cultivation_status="flowering", forecast_today=reading, settings=settings)
        assert candidate is None

    def test_never_recommends_a_chemical(self):
        reading = WeatherReading(rain_probability_percent=90)
        candidate = evaluate_crop_weather_alert(crop_name="Tomato", cultivation_status="flowering", forecast_today=reading, settings=settings)
        forbidden = ["pesticide", "spray", "chemical", "dosage", "fungicide"]
        assert not any(term in candidate.message_key.lower() for term in forbidden)


class TestSprayConditionWarning:
    def test_warns_on_high_wind(self):
        reading = WeatherReading(wind_speed_kmh=settings.weather_high_wind_kmh_threshold)
        candidate = evaluate_spray_condition_warning(reading, settings)
        assert candidate is not None
        assert candidate.message_key == "spray_condition_warning"

    def test_warns_on_imminent_rain(self):
        reading = WeatherReading(rain_probability_percent=settings.weather_rain_probability_threshold)
        candidate = evaluate_spray_condition_warning(reading, settings)
        assert candidate is not None

    def test_no_warning_in_good_conditions(self):
        reading = WeatherReading(wind_speed_kmh=5, rain_probability_percent=5)
        assert evaluate_spray_condition_warning(reading, settings) is None

    def test_never_recommends_a_specific_pesticide_or_dosage(self):
        reading = WeatherReading(wind_speed_kmh=100)
        candidate = evaluate_spray_condition_warning(reading, settings)
        message = get_message(candidate.message_key, "en")
        forbidden = ["ml/l", "kg/acre", "dosage", "brand"]
        assert not any(term in message.lower() for term in forbidden)
