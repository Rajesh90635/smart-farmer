"""
Dealer product listing. A dealer may only list a product if BOTH:
1. Their ProfessionalProfile.verification_status == VERIFIED (reused from
   Prompt 8, not re-implemented).
2. The Product.status == APPROVED (this phase's own admin workflow).
Neither check is ever skipped - both are re-verified on every listing
create, not just at signup time.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.dealer_price_history import DealerPriceHistory
from app.models.dealer_product import DealerProduct
from app.models.price_anomaly_flag import PriceAnomalyFlag
from app.models.professional_profile import VerificationStatus
from app.repositories import dealer_product_repository, product_repository, professional_repository
from app.schemas.product import DealerProductCreateRequest, DealerProductListResponse, DealerProductResponse, DealerProductUpdateRequest
from app.services.audit_logger import AuditLogger
from app.services.price_comparison import compare_price


def _get_verified_dealer_or_404(db: Session, user_id: str):
    dealer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if dealer is None or dealer.verification_status != VerificationStatus.VERIFIED:
        raise AppError(error_codes.NOT_FOUND, "No verified dealer profile found for this account.", 404)
    return dealer


def create_listing(db: Session, user_id: str, payload: DealerProductCreateRequest, settings: Settings) -> DealerProductResponse:
    dealer = _get_verified_dealer_or_404(db, user_id)

    product = product_repository.get_approved_product(db, payload.product_id)
    if product is None:
        raise AppError(error_codes.VALIDATION_ERROR, "This product is not available for listing (not found or not approved).", 422)

    if dealer_product_repository.get_by_dealer_and_product(db, dealer.id, payload.product_id) is not None:
        raise AppError(error_codes.DUPLICATE_ACCOUNT, "You already have a listing for this product.", 409)

    listing = DealerProduct(
        dealer_id=dealer.id,
        product_id=payload.product_id,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        delivery_area=payload.delivery_area,
        batch_number=payload.batch_number,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
    )
    dealer_product_repository.create(db, listing)
    db.flush()

    dealer_product_repository.create_price_history(db, DealerPriceHistory(dealer_product_id=listing.id, old_price=None, new_price=payload.price, reason="initial listing"))
    _check_and_flag_anomaly(db, listing, product, settings)

    AuditLogger(db).log("DEALER_PRODUCT_LISTED", actor_id=user_id, actor_role="dealer", entity="dealer_product", entity_id=str(listing.id))
    db.commit()
    db.refresh(listing)
    return DealerProductResponse.model_validate(listing)


def update_listing(db: Session, user_id: str, listing_id: uuid.UUID, payload: DealerProductUpdateRequest, settings: Settings) -> DealerProductResponse:
    dealer = _get_verified_dealer_or_404(db, user_id)
    listing = dealer_product_repository.get_owned_by_dealer(db, listing_id, dealer.id)
    if listing is None:
        raise AppError(error_codes.NOT_FOUND, "Listing not found.", 404)

    price_changed = payload.price is not None and payload.price != listing.price
    old_price = listing.price

    if payload.price is not None:
        listing.price = payload.price
    if payload.stock_quantity is not None:
        listing.stock_quantity = payload.stock_quantity
    if payload.is_available is not None:
        listing.is_available = payload.is_available
    if payload.delivery_area is not None:
        listing.delivery_area = payload.delivery_area

    if price_changed:
        dealer_product_repository.create_price_history(
            db, DealerPriceHistory(dealer_product_id=listing.id, old_price=old_price, new_price=listing.price, reason=payload.price_change_reason)
        )
        product = product_repository.get_product(db, listing.product_id)
        if product:
            _check_and_flag_anomaly(db, listing, product, settings)

    AuditLogger(db).log("DEALER_PRODUCT_UPDATED", actor_id=user_id, actor_role="dealer", entity="dealer_product", entity_id=str(listing.id))
    db.commit()
    db.refresh(listing)
    return DealerProductResponse.model_validate(listing)


def list_my_listings(db: Session, user_id: str, *, limit: int = 50, offset: int = 0) -> DealerProductListResponse:
    dealer = _get_verified_dealer_or_404(db, user_id)
    items, total = dealer_product_repository.list_listings_for_dealer(db, dealer.id, limit=limit, offset=offset)
    return DealerProductListResponse(items=[DealerProductResponse.model_validate(i) for i in items], total=total)


def _check_and_flag_anomaly(db: Session, listing: DealerProduct, product, settings: Settings) -> None:
    ref = product_repository.get_latest_reference_price(db, product.id)
    result = compare_price(
        dealer_price=listing.price,
        pack_size_value=product.pack_size_value,
        pack_size_unit=product.pack_size_unit,
        reference_price=ref.price if ref else None,
        reference_pack_size_value=product.pack_size_value if ref else None,
        settings=settings,
    )
    if result.anomaly_level is not None:
        db.add(
            PriceAnomalyFlag(
                dealer_product_id=listing.id,
                level=result.anomaly_level,
                dealer_price_at_detection=listing.price,
                reference_price_at_detection=ref.price if ref else None,
            )
        )
