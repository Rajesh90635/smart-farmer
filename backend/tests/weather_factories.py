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


def frost_risk_provider() -> FakeWeatherProvider:
    """D15-04: humidity_percent=100 makes the dew point equal the air
    temperature exactly (Magnus formula), so a low temperature here
    reliably crosses the frost threshold regardless of its exact value."""
    return FakeWeatherProvider(
        current=WeatherReading(temperature_c=1.0, humidity_percent=100.0, wind_speed_kmh=5.0),
        forecast=[
            ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=5.0)),
        ],
    )


def calm_dry_provider() -> FakeWeatherProvider:
    """A provider with no rain/wind/temperature extremes of its own - used
    for cumulative-rainfall/drought tests so only the pre-seeded
    weather_snapshots history (not this fetch's own reading) drives the
    alert being tested."""
    return FakeWeatherProvider(
        current=WeatherReading(temperature_c=25.0, humidity_percent=50.0, wind_speed_kmh=5.0, rainfall_mm=0.0),
        forecast=[
            ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=5.0)),
        ],
    )
