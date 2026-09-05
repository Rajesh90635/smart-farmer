"""
Offer/negotiation + concurrency-safe acceptance.

THE MANDATORY CONCURRENCY GUARANTEE: when a farmer accepts an offer,
accept_offer takes a real row lock (SELECT ... FOR UPDATE via
harvest_repository.get_listing_for_update) on the HarvestListing BEFORE
checking/decrementing quantity_available. Two simultaneous accept
requests against the same listing serialize on this lock - the second
request sees the already-decremented quantity and correctly fails if it
would oversell, rather than both succeeding based on a stale read. This
is a real database-level guarantee, not an application-level check that
could race.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.buyer_offer import BuyerOffer, CounterOffer, NegotiationParty, OfferStatus
from app.models.professional_profile import VerificationStatus
from app.models.sale_order import SaleOrder
from app.repositories import buyer_offer_repository, harvest_repository, professional_repository, sale_order_repository
from app.schemas.marketplace import AcceptOfferRequest, CounterOfferCreateRequest, CounterOfferResponse, OfferCreateRequest, OfferListResponse, OfferResponse, SaleOrderResponse
from app.services.audit_logger import AuditLogger


def _get_verified_buyer_or_404(db: Session, user_id: str):
    buyer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if buyer is None or buyer.verification_status != VerificationStatus.VERIFIED:
        raise AppError(error_codes.NOT_FOUND, "No verified buyer profile found for this account.", 404)
    return buyer


def create_offer(db: Session, user_id: str, listing_id: uuid.UUID, payload: OfferCreateRequest) -> OfferResponse:
    buyer = _get_verified_buyer_or_404(db, user_id)

    listing = harvest_repository.get_listing_by_id(db, listing_id)
    if listing is None or not listing.is_active:
        raise AppError(error_codes.NOT_FOUND, "Listing not found or no longer active.", 404)

    # D59-03 (docs/audit/c09_market_sales.md): the buyer's OWN registered
    # min_quantity/max_quantity (BuyerBusinessProfile) was never
    # cross-checked against anything - a buyer profile stating "I only
    # buy 500-2000kg lots" could still submit an offer for 10kg or
    # 50000kg with no rejection. Only enforced when the buyer actually
    # SET a bound - an unset min/max means no constraint, not zero/infinity.
    business_profile = buyer_offer_repository.get_buyer_business_profile(db, buyer.id)
    if business_profile is not None:
        if business_profile.min_quantity is not None and payload.quantity < business_profile.min_quantity:
            raise AppError(
                error_codes.VALIDATION_ERROR,
                f"Your buyer profile's minimum purchase quantity is {business_profile.min_quantity} {payload.unit} - this offer is below that.",
                422,
            )
        if business_profile.max_quantity is not None and payload.quantity > business_profile.max_quantity:
            raise AppError(
                error_codes.VALIDATION_ERROR,
                f"Your buyer profile's maximum purchase quantity is {business_profile.max_quantity} {payload.unit} - this offer exceeds that.",
                422,
            )

    offer = BuyerOffer(
        harvest_listing_id=listing.id,
        buyer_id=buyer.id,
        quantity=payload.quantity,
        unit=payload.unit,
        price_per_unit=payload.price_per_unit,
        quality_requirements=payload.quality_requirements,
        valid_until=payload.valid_until,
        collection_terms=payload.collection_terms,
    )
    buyer_offer_repository.create_offer(db, offer)

    AuditLogger(db).log("BUYER_OFFER_CREATED", actor_id=user_id, actor_role="buyer", entity="harvest_listing", entity_id=str(listing.id))
    db.commit()
    db.refresh(offer)
    return OfferResponse.model_validate(offer)


def list_offers_for_my_listing(db: Session, farmer_id: str, listing_id: uuid.UUID) -> OfferListResponse:
    listing = harvest_repository.get_listing_owned(db, listing_id, uuid.UUID(farmer_id))
    if listing is None:
        raise AppError(error_codes.NOT_FOUND, "Listing not found.", 404)
    offers = buyer_offer_repository.list_offers_for_listing(db, listing_id)
    return OfferListResponse(items=[OfferResponse.model_validate(o) for o in offers], total=len(offers))


def create_counter_offer(db: Session, user_id: str, offer_id: uuid.UUID, role: str, payload: CounterOfferCreateRequest) -> CounterOfferResponse:
    offer = buyer_offer_repository.get_offer_by_id(db, offer_id)
    if offer is None:
        raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)

    if role == "farmer":
        listing = harvest_repository.get_listing_owned(db, offer.harvest_listing_id, uuid.UUID(user_id))
        if listing is None:
            raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)
        party = NegotiationParty.FARMER
    else:
        buyer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
        if buyer is None or offer.buyer_id != buyer.id:
            raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)
        party = NegotiationParty.BUYER

    if offer.status != OfferStatus.ACTIVE:
        raise AppError(error_codes.VALIDATION_ERROR, "This offer is no longer active.", 409)

    counter = CounterOffer(buyer_offer_id=offer.id, proposed_by=party, price_per_unit=payload.price_per_unit, quantity=payload.quantity, message=payload.message)
    buyer_offer_repository.create_counter_offer(db, counter)

    AuditLogger(db).log("COUNTER_OFFER_CREATED", actor_id=user_id, actor_role=role, entity="buyer_offer", entity_id=str(offer.id))
    db.commit()
    db.refresh(counter)
    return CounterOfferResponse.model_validate(counter)


def accept_offer(db: Session, farmer_id: str, offer_id: uuid.UUID, payload: AcceptOfferRequest | None = None) -> SaleOrderResponse:
    offer = buyer_offer_repository.get_offer_by_id(db, offer_id)
    if offer is None:
        raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)

    if offer.status != OfferStatus.ACTIVE:
        raise AppError(error_codes.VALIDATION_ERROR, "This offer is no longer active.", 409)

    # Real bug fixed here: `valid_until`/OfferStatus.EXPIRED existed but
    # nothing ever checked expiry - a farmer could accept an offer after
    # its own declared validity window had passed. Checked here (accept
    # time), not as a background job, since no scheduler exists in this
    # project (see docs/audit/README.md) - this is the one place an
    # expired-but-still-ACTIVE offer is actually read before being acted on.
    if offer.valid_until is not None and offer.valid_until < datetime.now(timezone.utc):
        offer.status = OfferStatus.EXPIRED
        db.commit()
        raise AppError(error_codes.VALIDATION_ERROR, "This offer has expired and can no longer be accepted.", 409)

    latest_counter = buyer_offer_repository.get_latest_counter_offer(db, offer.id)
    final_price = latest_counter.price_per_unit if latest_counter else offer.price_per_unit
    final_quantity = latest_counter.quantity if latest_counter else offer.quantity

    listing = harvest_repository.get_listing_for_update(db, offer.harvest_listing_id)
    if listing is None or listing.farmer_id != uuid.UUID(farmer_id):
        raise AppError(error_codes.NOT_FOUND, "Listing not found.", 404)
    if not listing.is_active:
        raise AppError(error_codes.VALIDATION_ERROR, "This listing is no longer active.", 422)

    if final_quantity > listing.quantity_available:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            f"Only {listing.quantity_available} {listing.unit} remain available - cannot accept an offer for {final_quantity}.",
            409,
        )

    gross_value = final_price * final_quantity
    # Real bug fixed here: this was unconditionally Decimal("0") - "net
    # realization" was structurally incapable of ever differing from
    # gross. Now farmer-entered at accept time (never estimated/fabricated
    # by the backend), matching the ledger/cost-estimate convention used
    # everywhere else in this app - see AcceptOfferRequest's docstring.
    charges = payload.charges if payload is not None else Decimal("0")
    if charges > gross_value:
        raise AppError(error_codes.VALIDATION_ERROR, "Charges cannot exceed the sale's gross value.", 422)
    net_value = gross_value - charges

    sale = SaleOrder(
        harvest_listing_id=listing.id,
        buyer_offer_id=offer.id,
        farmer_id=uuid.UUID(farmer_id),
        buyer_id=offer.buyer_id,
        crop_id=listing.crop_id,
        quantity=final_quantity,
        unit=listing.unit,
        quality_grade_snapshot=listing.quality_grade,
        price_per_unit=final_price,
        gross_value=gross_value,
        charges=charges,
        net_value=net_value,
        collection_method=listing.delivery_option.value,
        service_area_snapshot=listing.service_area,
    )
    sale_order_repository.create_sale_order(db, sale)

    listing.quantity_available -= final_quantity
    if listing.quantity_available <= 0:
        listing.is_active = False

    offer.status = OfferStatus.ACCEPTED

    AuditLogger(db).log("BUYER_OFFER_ACCEPTED", actor_id=farmer_id, actor_role="farmer", entity="harvest_listing", entity_id=str(listing.id))
    AuditLogger(db).log("SALE_ORDER_CREATED", actor_id=farmer_id, actor_role="farmer", entity="sale_order", entity_id=str(sale.id))

    db.commit()
    db.refresh(sale)
    return SaleOrderResponse.model_validate(sale)


def reject_offer(db: Session, farmer_id: str, offer_id: uuid.UUID) -> OfferResponse:
    offer = buyer_offer_repository.get_offer_by_id(db, offer_id)
    if offer is None:
        raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)
    listing = harvest_repository.get_listing_owned(db, offer.harvest_listing_id, uuid.UUID(farmer_id))
    if listing is None:
        raise AppError(error_codes.NOT_FOUND, "Offer not found.", 404)

    offer.status = OfferStatus.REJECTED
    AuditLogger(db).log("BUYER_OFFER_REJECTED", actor_id=farmer_id, actor_role="farmer", entity="buyer_offer", entity_id=str(offer.id))
    db.commit()
    db.refresh(offer)
    return OfferResponse.model_validate(offer)
