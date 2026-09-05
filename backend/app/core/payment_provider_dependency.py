"""
FastAPI dependency providing the configured PaymentGatewayProvider.
Exactly one switch point: `Settings.payment_gateway_provider` - mirrors
`weather_provider_dependency.py` exactly.
"""
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.payment.not_configured_payment_gateway_provider import NotConfiguredPaymentGatewayProvider
from app.services.payment.payment_gateway_provider import PaymentGatewayProvider
from app.services.payment.sandbox_payment_gateway_provider import SandboxPaymentGatewayProvider


@lru_cache
def get_payment_gateway_provider() -> PaymentGatewayProvider:
    settings: Settings = get_settings()
    if settings.payment_gateway_provider == "sandbox":
        return SandboxPaymentGatewayProvider()
    return NotConfiguredPaymentGatewayProvider()
