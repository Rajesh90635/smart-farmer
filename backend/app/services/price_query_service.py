"""
Farmer-facing price comparison: all VERIFIED dealers' offers for a
product, each individually normalized and compared against the latest
reference price. Never ranks a dealer higher for any reason other than
price/availability - no "sponsored" concept exists in this codebase.
"""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.professional_profile import VerificationStatus
from app.models.reference_price import ReferencePrice
from app.repositories import dealer_product_repository, product_repository, professional_repository
from app.schemas.price import DealerOfferComparisonResponse, PriceComparisonResponse, ScamShieldStatusResponse
from app.services.market.market_provider import MarketProvider
from app.services.price_comparison import compare_price, price_per_unit


def is_reference_price_stale(ref: ReferencePrice, settings: Settings) -> bool:
    """D88-10 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors weather's
    is_stale convention - a reference price is only as trustworthy as how
    recently it was actually effective, never how recently it was
    inserted into this database (retrieved_at can lag the real market
    date, e.g. a batch import)."""
    today = date.today()
    return (today - ref.effective_date).days > settings.reference_price_max_age_days


def _dealer_matches_location(dealer, *, district: str | None, state: str | None) -> bool:
    """D44-02/03/04 (docs/audit/FINAL_CANONICAL_group_B.md): mirrors
    nearby_professional_service's own service_area matching exactly - no
    second location-matching implementation. No criteria given -> every
    dealer matches (today's unfiltered behavior, unchanged)."""
    if district is None and state is None:
        return True
    area = dealer.service_area or {}
    if district is not None and area.get("district") == district:
        return True
    if state is not None and area.get("state") == state:
        return True
    return False


def compare_offers_for_product(
    db: Session, product_id: uuid.UUID, settings: Settings, market_provider: MarketProvider, *, district: str | None = None, state: str | None = None
) -> PriceComparisonResponse:
    product = product_repository.get_approved_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    ref = market_provider.get_reference_price(db, product_id=product_id)
    listings = dealer_product_repository.list_listings_for_product(db, product_id, available_only=True)

    offers = []
    for listing in listings:
        dealer = professional_repository.get_by_id(db, listing.dealer_id)
        if dealer is None or dealer.verification_status != VerificationStatus.VERIFIED:
            continue  # never surface an unverified dealer's offer
        if not _dealer_matches_location(dealer, district=district, state=state):
            continue
        result = compare_price(
            dealer_price=listing.price, pack_size_value=product.pack_size_value, pack_size_unit=product.pack_size_unit,
            reference_price=ref.price if ref.available else None, reference_pack_size_value=product.pack_size_value if ref.available else None, settings=settings,
        )
        offers.append(DealerOfferComparisonResponse(
            dealer_product_id=listing.id, dealer_id=listing.dealer_id, dealer_price=listing.price,
            price_per_unit=result.price_per_unit, unit=product.pack_size_unit, stock_quantity=listing.stock_quantity, is_available=listing.is_available,
        ))

    offers.sort(key=lambda o: o.price_per_unit)

    return PriceComparisonResponse(
        product_id=product_id,
        reference_price=ref.price if ref.available else None,
        # Reuses the same helper every offer's own per-unit price already
        # goes through (see compare_price above) - a second, duplicated raw
        # division here previously bypassed that function's rounding and
        # could return scientific notation (e.g. "1.0E+2") straight into
        # the farmer-facing response.
        reference_price_per_unit=price_per_unit(ref.price, product.pack_size_value) if ref.available else None,
        reference_source=ref.source_name if ref.available else None,
        offers=offers,
    )


def get_scam_shield_status(db: Session, dealer_product_id: uuid.UUID, settings: Settings, market_provider: MarketProvider) -> ScamShieldStatusResponse:
    listing = dealer_product_repository.get_by_id(db, dealer_product_id)
    if listing is None:
        raise AppError(error_codes.NOT_FOUND, "Listing not found.", 404)

    product = product_repository.get_product(db, listing.product_id)
    ref = market_provider.get_reference_price(db, product_id=listing.product_id)

    result = compare_price(
        dealer_price=listing.price, pack_size_value=product.pack_size_value, pack_size_unit=product.pack_size_unit,
        reference_price=ref.price if ref.available else None, reference_pack_size_value=product.pack_size_value if ref.available else None, settings=settings,
    )

    if result.anomaly_level is None:
        message = "This price is within the normal range for this product." if ref.available else "No reference price is available for comparison yet."
    else:
        message = f"This price is {result.percent_above_reference:.0f}% above the reference price for this product. Consider comparing with other dealers."

    return ScamShieldStatusResponse(
        dealer_product_id=listing.id,
        price_per_unit=result.price_per_unit,
        reference_price_per_unit=result.reference_price_per_unit,
        percent_above_reference=result.percent_above_reference,
        anomaly_level=result.anomaly_level.value if result.anomaly_level else None,
        message=message,
    )
