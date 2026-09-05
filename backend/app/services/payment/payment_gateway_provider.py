"""
PaymentGatewayProvider: the abstraction every payment gateway sits behind
(D90-10, docs/audit/c13_governance_farmbrain_security.md) - the same
"provider abstraction, real business logic depends on the interface, not
a specific vendor" pattern already used for WeatherProvider (weather/weather_provider.py)
and ModelProvider (ai/model_provider.py).

Named `PaymentGatewayProvider`, not `PaymentProvider` - `app.models.payment.PaymentProvider`
already exists as the DB enum recording which provider a Payment row used
(SANDBOX/UPI/CARD/NET_BANKING/CASH_ON_DELIVERY); reusing that name for
this ABC would shadow it in every file that needs both.

WHAT THIS DOES NOT DO: it does not make a real gateway suddenly work.
Only `SandboxPaymentGatewayProvider` is actually implemented - it never
moves real money, mirroring exactly what `payment_service.py`/
`sale_order_service.py` already did before this refactor, just behind an
interface now instead of hardcoded inline. A real gateway (Razorpay,
PayU, Cashfree, etc.) would need its own adapter class implementing this
same interface plus a real webhook receiver (a real gateway calls YOUR
server; `is_sandbox_completable` below is what structurally prevents the
farmer's own client from ever being the thing that reports a real
payment's success) - live-gateway verification would be ENVIRONMENT_DEPENDENT
(real merchant credentials), not something this pass invents or fakes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PaymentInitiationResult:
    available: bool
    provider_name: str
    external_reference: str | None = None
    unavailable_reason: str | None = None


class PaymentGatewayProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def is_sandbox_completable(self) -> bool:
        """True only for a provider whose completion can be driven by a
        direct, synchronous, farmer-callable call (the sandbox test hook,
        `POST .../pay/complete`). A real gateway's completion arrives via
        an asynchronous webhook THE GATEWAY calls - never something the
        farmer's own client can trigger - so a real adapter must return
        False here, and the service layer must refuse the sandbox
        completion endpoint for it rather than silently pretend a real
        payment succeeded because a client asked nicely."""

    @abstractmethod
    def initiate_payment(self, *, amount: Decimal, reference_hint: str) -> PaymentInitiationResult:
        """Starts a payment attempt and returns an external reference to
        store on the Payment row. `available=False` (never a fabricated
        reference) when this provider isn't actually configured/reachable."""
