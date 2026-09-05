"""
FakeSmsOtpProvider - TEST-ONLY, mirrors the FakeWeatherProvider pattern.
Injected via FastAPI's dependency_overrides only; the production default
remains TwilioVerifyProvider/NotConfiguredSmsOtpProvider per
app/core/sms_provider_dependency.py.
"""
from app.services.sms.sms_otp_provider import OtpCheckResult, OtpSendResult, SmsOtpProvider


class FakeSmsOtpProvider(SmsOtpProvider):
    def __init__(self, *, available: bool = True, valid_code: str = "123456"):
        self._available = available
        self._valid_code = valid_code
        self.sent_to: list[str] = []

    @property
    def provider_name(self) -> str:
        return "fake_test_provider"

    def send_otp(self, phone_number: str) -> OtpSendResult:
        self.sent_to.append(phone_number)
        if not self._available:
            return OtpSendResult(available=False, provider_name=self.provider_name, unavailable_reason="fake provider marked unavailable")
        return OtpSendResult(available=True, provider_name=self.provider_name)

    def check_otp(self, phone_number: str, code: str) -> OtpCheckResult:
        if not self._available:
            return OtpCheckResult(available=False, approved=False, provider_name=self.provider_name, unavailable_reason="fake provider marked unavailable")
        return OtpCheckResult(available=True, approved=code == self._valid_code, provider_name=self.provider_name)
