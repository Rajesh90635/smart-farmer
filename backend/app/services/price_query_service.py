"""
Farmer-facing price comparison: all VERIFIED dealers' offers for a
product, each individually normalized and compared against the latest
reference price. Never ranks a dealer higher for any reason other than
price/availability - no "sponsored" concept exists in this codebase.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.professional_profile import VerificationStatus
from app.repositories import dealer_product_repository, product_repository, professional_repository
from app.schemas.price import DealerOfferComparisonResponse, PriceComparisonResponse, ScamShieldStatusResponse
from app.services.price_comparison import compare_price


def compare_offers_for_product(db: Session, product_id: uuid.UUID, settings: Settings) -> PriceComparisonResponse:
    product = product_repository.get_approved_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    ref = product_repository.get_latest_reference_price(db, product_id)
    listings = dealer_product_repository.list_listings_for_product(db, product_id, available_only=True)

    offers = []
    for listing in listings:
        dealer = professional_repository.get_by_id(db, listing.dealer_id)
        if dealer is None or dealer.verification_status != VerificationStatus.VERIFIED:
            continue  # never surface an unverified dealer's offer
        result = compare_price(
            dealer_price=listing.price, pack_size_value=product.pack_size_value, pack_size_unit=product.pack_size_unit,
            reference_price=ref.price if ref else None, reference_pack_size_value=product.pack_size_value if ref else None, settings=settings,
        )
        offers.append(DealerOfferComparisonResponse(
            dealer_product_id=listing.id, dealer_id=listing.dealer_id, dealer_price=listing.price,
            price_per_unit=result.price_per_unit, unit=product.pack_size_unit, stock_quantity=listing.stock_quantity, is_available=listing.is_available,
        ))

    offers.sort(key=lambda o: o.price_per_unit)

    return PriceComparisonResponse(
        product_id=product_id,
        reference_price=ref.price if ref else None,
        reference_price_per_unit=(ref.price / product.pack_size_value) if ref else None,
        reference_source=ref.source_name if ref else None,
        offers=offers,
    )


def get_scam_shield_status(db: Session, dealer_product_id: uuid.UUID, settings: Settings) -> ScamShieldStatusResponse:
    listing = dealer_product_repository.get_by_id(db, dealer_product_id)
    if listing is None:
        raise AppError(error_codes.NOT_FOUND, "Listing not found.", 404)

    product = product_repository.get_product(db, listing.product_id)
    ref = product_repository.get_latest_reference_price(db, listing.product_id)

    result = compare_price(
        dealer_price=listing.price, pack_size_value=product.pack_size_value, pack_size_unit=product.pack_size_unit,
        reference_price=ref.price if ref else None, reference_pack_size_value=product.pack_size_value if ref else None, settings=settings,
    )

    if result.anomaly_level is None:
        message = "This price is within the normal range for this product." if ref else "No reference price is available for comparison yet."
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
