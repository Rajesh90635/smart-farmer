"""
MarketProvider: D90-02 (docs/audit/FINAL_CANONICAL_group_D.md) - the
abstraction every market-price source sits behind, mirroring
WeatherProvider/PaymentGatewayProvider exactly. Today's only real
implementation (DatabaseMarketProvider) wraps the existing, already-working
ReferencePrice DB query - this is a refactor of that working feature into
the established interface shape, not new functionality, and leaves room
for a future live-market-API-backed implementation without touching any
caller.

Like WeatherProvider, reports availability explicitly rather than raising
for the expected "no reference price yet" case.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class MarketPriceResult:
    available: bool
    provider_name: str
    price: Decimal | None = None
    source_name: str | None = None
    effective_date: date | None = None
    unavailable_reason: str | None = None


class MarketProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_reference_price(self, db: Session, *, product_id: uuid.UUID, region: dict | None = None) -> MarketPriceResult:
        """Never fabricates a price - returns available=False with a
        reason when no real reference price exists for this product."""
