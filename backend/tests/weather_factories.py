from datetime import date, timedelta

from app.services.weather.weather_provider import ForecastDay, WeatherReading
from tests.fake_weather_provider import FakeWeatherProvider


def heavy_rain_provider() -> FakeWeatherProvider:
    """A provider whose today-forecast triggers the heavy-rain alert path."""
    return FakeWeatherProvider(
        current=WeatherReading(temperature_c=27.0, wind_speed_kmh=10.0),
        forecast=[
            ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=85.0, rainfall_mm=40.0)),
            ForecastDay(forecast_date=date.today() + timedelta(days=1), reading=WeatherReading(rain_probability_percent=20.0)),
        ],
    )
