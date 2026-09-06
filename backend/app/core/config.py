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
    # D15-04 (docs/audit/FINAL_CANONICAL_group_A.md): frost risk from a
    # Magnus-formula dew-point approximation over already-fetched
    # temperature_c/humidity_percent - no new external data.
    weather_frost_dewpoint_celsius_threshold: float = 2.0
    # D15-08/D17-04/D15-09/D17-05/D75-01/D75-02 (docs/audit/FINAL_CANONICAL_group_{A,D}.md):
    # the buildable cumulative-rainfall/consecutive-dry-days increment,
    # derived from existing weather_snapshots history - not a real
    # hydrological/soil-moisture model.
    weather_cumulative_rainfall_window_days: int = 3
    weather_flood_risk_cumulative_rainfall_mm_threshold: float = 100.0
    weather_waterlogging_risk_cumulative_rainfall_mm_threshold: float = 50.0
    weather_dry_day_rainfall_mm_threshold: float = 1.0
    weather_drought_risk_consecutive_dry_days_threshold: int = 14

    # --- Payment gateway (D90-10: provider abstraction) - "sandbox" is
    # the only implemented adapter (moves no real money, matches this
    # project's pre-existing sandbox-only behavior exactly); a real
    # gateway name here with no adapter class falls back to "none"
    # (NotConfiguredPaymentGatewayProvider), same pattern as weather/SMS. ---
    payment_gateway_provider: str = "sandbox"  # "sandbox" | "none"

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

    # --- Background scheduler (Expert SLA automation) ---
    # Closes the long-disclosed "no background scheduler yet" gap (see
    # docs/CASE_MANAGEMENT.md's old "Assignment timeout" section,
    # docs/NOTIFICATION_ARCHITECTURE.md's "Trigger model"). Disabled
    # automatically in the test environment (see scheduler.py) so
    # background ticks never race against test transactions.
    scheduler_enabled: bool = True
    case_sla_sweep_interval_seconds: int = 300
    case_sla_reminder_before_hours: float = 4.0
    case_sla_max_reassignment_attempts: int = 2

    # --- Input inventory expiry sweep (D24-09) - same scheduler, a
    # separate slower-cadence job since expiry doesn't need 5-minute
    # granularity ---
    input_inventory_expiry_sweep_interval_seconds: int = 3600
    input_expiry_warning_days: int = 14

    # --- Proactive weather alert sweep (D16-10) - same scheduler; a farm
    # with dangerous weather is now checked even if the farmer never
    # opens the weather screen. Interval matches weather_current_cache_minutes
    # (30 min) so the sweep never forces a provider call more often than
    # a farmer's own pull-based check already would. ---
    proactive_weather_alert_sweep_interval_seconds: int = 1800

    # --- Task overdue alert sweep (D9-16/D9-03/D78-01/D37-04) - same
    # scheduler; a farmer who never opens the app is otherwise never told
    # a task became overdue (display_status is computed only on read). ---
    task_overdue_alert_sweep_interval_seconds: int = 3600

    # --- Soil testing (D20-12) - a real agronomic convention (soil
    # nutrient levels are typically re-tested every 2-3 years), not
    # invented for this project; same disclosed-placeholder treatment as
    # this project's other threshold settings. ---
    soil_test_max_age_days: int = 730

    # --- Payment timeout sweep (D66-03) - same scheduler; PaymentStatus.TIMEOUT
    # already existed but nothing ever assigned it, so a payment could sit
    # PENDING forever with no resolution. ---
    payment_timeout_minutes: int = 30
    payment_timeout_sweep_interval_seconds: int = 900

    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — used as a FastAPI dependency so tests can
    override it via dependency_overrides without touching real env vars."""
    return Settings()  # type: ignore[call-arg]  # values come from env/.env
