"""D77-06 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from app.services.iot.not_configured_iot_provider import NotConfiguredIoTProvider
from tests.fake_iot_provider import FakeIoTProvider


def test_not_configured_iot_provider_never_fabricates_a_reading():
    provider = NotConfiguredIoTProvider()
    result = provider.get_reading(sensor_id="sensor-1", metric="soil_moisture")
    assert result.available is False
    assert result.value is None
    assert result.unavailable_reason is not None


def test_fake_iot_provider_returns_a_real_looking_reading_when_available():
    provider = FakeIoTProvider(value=55.0, unit="percent")
    result = provider.get_reading(sensor_id="sensor-1", metric="soil_moisture")
    assert result.available is True
    assert result.value == 55.0
    assert result.unit == "percent"


def test_fake_iot_provider_can_simulate_unavailability():
    provider = FakeIoTProvider(available=False)
    result = provider.get_reading(sensor_id="sensor-1", metric="soil_moisture")
    assert result.available is False
    assert result.value is None
