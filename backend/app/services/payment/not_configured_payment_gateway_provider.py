"""
NotConfiguredPaymentGatewayProvider: returned when Settings.payment_gateway_provider
names a real gateway (e.g. "razorpay") that has no adapter class written
yet, or is explicitly "none". Mirrors NotConfiguredWeatherProvider - never
fabricates a reference, always available=False.
"""
from decimal import Decimal

from app.services.payment.payment_gateway_provider import PaymentGatewayProvider, PaymentInitiationResult


class NotConfiguredPaymentGatewayProvider(PaymentGatewayProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    @property
    def is_sandbox_completable(self) -> bool:
        return False

    def initiate_payment(self, *, amount: Decimal, reference_hint: str) -> PaymentInitiationResult:
        return PaymentInitiationResult(
            available=False,
            provider_name=self.provider_name,
            unavailable_reason="No live payment gateway is configured in this environment.",
        )
