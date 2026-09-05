"""
NotConfiguredSmsOtpProvider: returned when Settings.sms_provider is "none"
or otherwise unresolved (e.g. "twilio" selected but credentials missing).

Fails CLOSED, unlike NotConfiguredWeatherProvider's benign "no data" -
an unverifiable OTP must never be treated as approved, since that would
silently re-open the exact account-takeover gap this provider exists to
close. available=False on both methods is what forces every call site to
refuse the password reset rather than proceed.
"""
from app.services.sms.sms_otp_provider import OtpCheckResult, OtpSendResult, SmsOtpProvider


class NotConfiguredSmsOtpProvider(SmsOtpProvider):
    _UNAVAILABLE_REASON = "No SMS/OTP provider is configured in this environment."

    @property
    def provider_name(self) -> str:
        return "none"

    def send_otp(self, phone_number: str) -> OtpSendResult:
        return OtpSendResult(available=False, provider_name=self.provider_name, unavailable_reason=self._UNAVAILABLE_REASON)

    def check_otp(self, phone_number: str, code: str) -> OtpCheckResult:
        return OtpCheckResult(available=False, approved=False, provider_name=self.provider_name, unavailable_reason=self._UNAVAILABLE_REASON)
