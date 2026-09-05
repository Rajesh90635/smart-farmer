"""
SmsOtpProvider: the abstraction every SMS/OTP source sits behind, mirroring
WeatherProvider and ModelProvider - business/API code never talks to a
specific SMS vendor's API directly, which is what protects the provider's
credentials and lets the vendor be swapped without touching an endpoint.

This exists to close a previously-documented, deliberately-accepted gap:
password-reset had no proof the caller owns the phone number they're
resetting (see docs/SECURITY.md and the prior docstrings in api/v1/auth.py
and auth_service.reset_password) - "no OTP/email channel exists" is no
longer true once a provider is configured here.

Every method reports availability explicitly rather than raising - a
provider being unconfigured or a network/vendor failure is an expected
outcome the caller MUST handle by refusing the password reset (fail
closed), never by silently skipping verification.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class OtpSendResult:
    available: bool
    provider_name: str
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class OtpCheckResult:
    available: bool
    # Only meaningful when available=True. A caller must treat
    # available=False as "cannot verify" - never as "approved".
    approved: bool
    provider_name: str
    unavailable_reason: str | None = None


class SmsOtpProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def send_otp(self, phone_number: str) -> OtpSendResult:
        """Sends a one-time code to phone_number (E.164). The provider
        itself owns code generation, expiry, and delivery - this call
        only starts that process."""

    @abstractmethod
    def check_otp(self, phone_number: str, code: str) -> OtpCheckResult:
        """Verifies a code the farmer typed back against the most recent
        one sent to phone_number. approved=False for a wrong code, an
        expired/already-used one, or no pending code at all - these are
        deliberately indistinguishable to the caller (never reveal which,
        same principle as login's invalid-credentials response)."""
