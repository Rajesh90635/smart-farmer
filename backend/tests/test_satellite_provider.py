"""D76-06/D90-08 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from datetime import date

from app.services.satellite.not_configured_satellite_provider import NotConfiguredSatelliteProvider
from tests.fake_satellite_provider import FakeSatelliteProvider


def test_not_configured_satellite_provider_never_fabricates_an_ndvi_value():
    provider = NotConfiguredSatelliteProvider()
    result = provider.get_ndvi(polygon=[(0.0, 0.0)], start_date=date.today(), end_date=date.today())
    assert result.available is False
    assert result.ndvi is None
    assert result.unavailable_reason is not None


def test_fake_satellite_provider_returns_a_real_looking_ndvi_when_available():
    provider = FakeSatelliteProvider(ndvi=0.72)
    result = provider.get_ndvi(polygon=[(0.0, 0.0)], start_date=date.today(), end_date=date.today())
    assert result.available is True
    assert result.ndvi == 0.72


def test_fake_satellite_provider_can_simulate_unavailability():
    provider = FakeSatelliteProvider(available=False)
    result = provider.get_ndvi(polygon=[(0.0, 0.0)], start_date=date.today(), end_date=date.today())
    assert result.available is False
    assert result.ndvi is None
