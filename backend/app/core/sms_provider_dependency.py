"""
FastAPI dependency providing the configured SmsOtpProvider. Exactly one
switch point: `Settings.sms_provider`. Same pattern as
weather_provider_dependency.py.
"""
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.sms.not_configured_provider import NotConfiguredSmsOtpProvider
from app.services.sms.sms_otp_provider import SmsOtpProvider
from app.services.sms.twilio_verify_provider import TwilioVerifyProvider


@lru_cache
def get_sms_provider() -> SmsOtpProvider:
    settings: Settings = get_settings()
    if settings.sms_provider == "twilio" and settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_verify_service_sid:
        return TwilioVerifyProvider(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            verify_service_sid=settings.twilio_verify_service_sid,
            timeout_seconds=settings.twilio_request_timeout_seconds,
        )
    return NotConfiguredSmsOtpProvider()
