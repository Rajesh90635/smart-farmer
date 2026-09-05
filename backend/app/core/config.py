"""
Environment-based application configuration.

Rule: nothing here has a real secret default. Anything security-sensitive
(JWT signing key, DB password) either has NO default (fails loudly if unset)
or a default that is obviously a dev-only placeholder and is documented as
such in .env.example.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    # --- App identity ---
    app_name: str = "smart-farmer-api"
    environment: Literal["development", "testing", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    # Full DSN, e.g. postgresql+psycopg://user:pass@host:5432/dbname
    database_url: str = Field(..., description="Set via DATABASE_URL env var. No default in any real environment.")
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Auth / JWT ---
    jwt_signing_key: str = Field(..., description="Set via JWT_SIGNING_KEY. Never commit a real value.")
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 14

    # --- CORS ---
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    # Flutter's `web-server` device binds an arbitrary port each run (not a
    # fixed one we could add to cors_allowed_origins above), so local dev
    # additionally allows any localhost/127.0.0.1 port via regex. None in
    # production - set only for local development.
    cors_allowed_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # --- Local storage ---
    local_storage_root: str = "./storage-data"

    # --- Crop photo upload/validation limits (configurable, never
    # hard-coded scattered through the code) ---
    photo_max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    photo_allowed_mime_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    photo_min_width_px: int = 300
    photo_min_height_px: int = 300
    photo_max_dimension_px: int = 1600  # longest side after processing/compression
    photo_thumbnail_max_dimension_px: int = 320
    photo_jpeg_quality: int = 85

    # --- Image quality heuristic thresholds (non-AI, technical checks
    # only; never a disease/agricultural judgment) ---
    photo_quality_min_mean_brightness: float = 25.0   # below this: "too dark"
    photo_quality_max_mean_brightness: float = 230.0  # above this: "too bright"
    photo_quality_min_blur_variance: float = 15.0     # below this: "too blurry"

    # --- OCR (Phase 30) - PLACEHOLDERS, same honesty convention as the
    # AI confidence gate (Prompt 6) and image quality thresholds above:
    # real Tesseract mean per-word confidence scores, thresholds not yet
    # validated against a large real-world invoice/receipt sample. ---
    ocr_high_confidence_mean_word_score: float = 75.0
    ocr_medium_confidence_mean_word_score: float = 45.0

    # --- AI confidence thresholds (PLACEHOLDERS - no evaluation dataset
    # exists yet; see docs/AI_EVALUATION.md before treating these as safe) ---
    ai_confidence_high_threshold: float = 0.85
    ai_confidence_medium_threshold: float = 0.60

    # --- Weather (free-first: Open-Meteo needs no API key at all) ---
    weather_provider: str = "open_meteo"  # "open_meteo" | "none"
    weather_api_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_request_timeout_seconds: float = 8.0
    weather_current_cache_minutes: int = 30
    weather_forecast_cache_minutes: int = 180

    # --- Weather alert thresholds (PLACEHOLDERS - not agriculturally
    # validated; see docs/WEATHER_ALERT_RULES.md before treating as safe) ---
    weather_rain_probability_threshold: float = 40.0     # percent
    weather_heavy_rain_probability_threshold: float = 70.0
    weather_heavy_rain_mm_threshold: float = 20.0        # mm/day
    weather_high_wind_kmh_threshold: float = 40.0
    weather_extreme_heat_celsius_threshold: float = 40.0
    weather_extreme_cold_celsius_threshold: float = 5.0

    # --- SMS / OTP (password-reset identity verification - Requirement:
    # closes the previously-documented account-takeover gap. "none" keeps
    # today's dev/test default; setting "twilio" without all three Twilio
    # values below still falls back to "none" - see sms_provider_dependency.py) ---
    sms_provider: str = "none"  # "twilio" | "none"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_verify_service_sid: str | None = None
    twilio_request_timeout_seconds: float = 10.0

    # --- Notifications ---
    notification_default_quiet_hours_start: str = "22:00"
    notification_default_quiet_hours_end: str = "06:00"

    # --- Price comparison / Scam Shield thresholds (PLACEHOLDERS - not
    # validated against real market data; see docs/PRICE_COMPARISON.md) ---
    price_anomaly_high_percent: float = 15.0        # dealer price > reference + this % -> HIGH
    price_anomaly_unusual_percent: float = 30.0     # dealer price > reference + this % -> UNUSUAL
    price_anomaly_review_percent: float = 50.0      # dealer price > reference + this % -> REVIEW_REQUIRED

    # --- Order/tax defaults (PLACEHOLDERS - not real tax/delivery-fee policy) ---
    order_default_tax_percent: float = 0.0
    order_default_delivery_fee: float = 0.0

    # --- Rate limiting (design values; enforcement wired in Security foundation) ---
    rate_limit_requests_per_minute: int = 60

    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — used as a FastAPI dependency so tests can
    override it via dependency_overrides without touching real env vars."""
    return Settings()  # type: ignore[call-arg]  # values come from env/.env
