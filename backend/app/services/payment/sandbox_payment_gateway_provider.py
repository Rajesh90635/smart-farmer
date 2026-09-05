"""
SandboxPaymentGatewayProvider: the ONLY provider actually implemented
this phase - moves no real money, ever. Extracted from what
payment_service.py/sale_order_service.py already did inline
(`external_reference=f"sandbox-{uuid.uuid4().hex[:12]}"`) - same
behavior, now behind the PaymentGatewayProvider interface.
"""
import uuid
from decimal import Decimal

from app.services.payment.payment_gateway_provider import PaymentGatewayProvider, PaymentInitiationResult


class SandboxPaymentGatewayProvider(PaymentGatewayProvider):
    @property
    def provider_name(self) -> str:
        return "sandbox"

    @property
    def is_sandbox_completable(self) -> bool:
        return True

    def initiate_payment(self, *, amount: Decimal, reference_hint: str) -> PaymentInitiationResult:
        return PaymentInitiationResult(
            available=True,
            provider_name=self.provider_name,
            external_reference=f"sandbox-{uuid.uuid4().hex[:12]}",
        )
