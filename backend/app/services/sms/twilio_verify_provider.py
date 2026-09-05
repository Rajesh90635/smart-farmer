"""
TwilioVerifyProvider: real implementation against Twilio's Verify API
(https://www.twilio.com/docs/verify/api) - Twilio owns code generation,
SMS delivery, expiry, and attempt-limiting entirely on its side, so this
class only ever starts or checks a verification, never generates or
stores a code itself.

IMPORTANT HONESTY NOTE, same convention as OpenMeteoProvider's: written
against Twilio's real, documented Verify API request/response shape, but
could not be exercised against the live API from this build/sandbox
environment (no outbound network access to verify.twilio.com here).
Additionally, and specific to this SMS message content reaching an Indian
phone number: Indian carriers require a DLT-registered sender/template
(TRAI regulation) independent of this code being correct - a message can
be rejected by the carrier even when Twilio's API call itself succeeds.
Verify a real end-to-end OTP send on a real device before relying on this
in production.
"""
import httpx

from app.services.sms.sms_otp_provider import OtpCheckResult, OtpSendResult, SmsOtpProvider


class TwilioVerifyProvider(SmsOtpProvider):
    def __init__(self, *, account_sid: str, auth_token: str, verify_service_sid: str, timeout_seconds: float):
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._base_url = f"https://verify.twilio.com/v2/Services/{verify_service_sid}"
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "twilio"

    def send_otp(self, phone_number: str) -> OtpSendResult:
        try:
            with httpx.Client(timeout=self._timeout, auth=(self._account_sid, self._auth_token)) as client:
                response = client.post(f"{self._base_url}/Verifications", data={"To": phone_number, "Channel": "sms"})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return OtpSendResult(
                available=False,
                provider_name=self.provider_name,
                unavailable_reason=f"OTP send request failed: {exc.__class__.__name__}",
            )
        return OtpSendResult(available=True, provider_name=self.provider_name)

    def check_otp(self, phone_number: str, code: str) -> OtpCheckResult:
        try:
            with httpx.Client(timeout=self._timeout, auth=(self._account_sid, self._auth_token)) as client:
                response = client.post(f"{self._base_url}/VerificationCheck", data={"To": phone_number, "Code": code})
        except httpx.HTTPError as exc:
            return OtpCheckResult(
                available=False,
                approved=False,
                provider_name=self.provider_name,
                unavailable_reason=f"OTP check request failed: {exc.__class__.__name__}",
            )

        if response.status_code == 404:
            # Twilio's documented response when there is no pending
            # verification for this phone number (never sent, already
            # checked, or expired) - a real, expected outcome, not a
            # transport failure. Treated as simply "not approved".
            return OtpCheckResult(available=True, approved=False, provider_name=self.provider_name)

        try:
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return OtpCheckResult(
                available=False,
                approved=False,
                provider_name=self.provider_name,
                unavailable_reason=f"OTP check request failed: {exc.__class__.__name__}",
            )

        return OtpCheckResult(available=True, approved=body.get("status") == "approved", provider_name=self.provider_name)
