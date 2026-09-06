"""
DatabaseMarketProvider: today's only concrete MarketProvider - wraps the
existing ReferencePrice query exactly as price_query_service already used
it directly, so this refactor changes zero real behavior. `region` is
accepted (matching the interface's future-proofed shape) but not yet used
to filter - ReferencePrice.region has no matching query today, and
inventing region-filtering behavior that doesn't really exist would be
worse than honestly ignoring it for now.
"""
import uuid

from sqlalchemy.orm import Session

from app.repositories import product_repository
from app.services.market.market_provider import MarketPriceResult, MarketProvider


class DatabaseMarketProvider(MarketProvider):
    @property
    def provider_name(self) -> str:
        return "database"

    def get_reference_price(self, db: Session, *, product_id: uuid.UUID, region: dict | None = None) -> MarketPriceResult:
        ref = product_repository.get_latest_reference_price(db, product_id)
        if ref is None:
            return MarketPriceResult(available=False, provider_name=self.provider_name, unavailable_reason="No reference price recorded for this product yet.")
        return MarketPriceResult(
            available=True, provider_name=self.provider_name, price=ref.price, source_name=ref.source_name, effective_date=ref.effective_date,
        )
