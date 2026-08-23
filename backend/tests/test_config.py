from app.core.config import get_settings


def test_settings_load_from_environment():
    settings = get_settings()
    assert settings.environment == "testing"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.jwt_signing_key  # not empty
    assert settings.api_v1_prefix == "/api/v1"
