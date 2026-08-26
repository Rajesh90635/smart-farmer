"""
Buyer marketplace: buyer registration (reuses ProfessionalProfile),
listing browse, offers/counter-offers, acceptance (concurrency-safe),
sale lifecycle, dispute/feedback.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.models.sale_order import SaleOrderStatus
from app.schemas.harvest import HarvestListingListResponse
from app.schemas.marketplace import (
    BuyerProfileRegisterRequest,
    BuyerProfileResponse,
    CounterOfferCreateRequest,
    CounterOfferResponse,
    OfferCreateRequest,
    OfferListResponse,
    OfferResponse,
    QualityDisputeCreateRequest,
    SaleCancelRequest,
    SaleDisputeCreateRequest,
    SaleDisputeListResponse,
    SaleDisputeResolveRequest,
    SaleDisputeResponse,
    SaleFeedbackCreateRequest,
    SaleOrderListResponse,
    SaleOrderResponse,
)
from app.services import buyer_service, harvest_service, offer_service, sale_order_service

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

_BUYER_ROLE = Role.BUYER.value


@router.post("/buyers", response_model=BuyerProfileResponse, status_code=201)
def register_buyer(
    payload: BuyerProfileRegisterRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> BuyerProfileResponse:
    return buyer_service.register_buyer(db, current_user.user_id, payload)


@router.get("/buyers/me", response_model=BuyerProfileResponse)
def get_my_buyer_profile(
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> BuyerProfileResponse:
    return buyer_service.get_my_buyer_profile(db, current_user.user_id)


@router.get("/listings", response_model=HarvestListingListResponse)
def browse_listings(
    crop_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> HarvestListingListResponse:
    """Buyer-facing 'Sell Your Crop' browse - service_area shown is
    already approximate-only at the data model level."""
    return harvest_service.list_marketplace_listings(db, crop_id=crop_id, limit=limit, offset=offset)


@router.post("/listings/{listing_id}/offers", response_model=OfferResponse, status_code=201)
def create_offer(
    listing_id: uuid.UUID,
    payload: OfferCreateRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> OfferResponse:
    return offer_service.create_offer(db, current_user.user_id, listing_id, payload)


@router.get("/listings/{listing_id}/offers", response_model=OfferListResponse)
def list_offers_for_listing(
    listing_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OfferListResponse:
    return offer_service.list_offers_for_my_listing(db, current_user.user_id, listing_id)


@router.post("/offers/{offer_id}/counter", response_model=CounterOfferResponse, status_code=201)
def create_counter_offer_as_farmer(
    offer_id: uuid.UUID,
    payload: CounterOfferCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CounterOfferResponse:
    return offer_service.create_counter_offer(db, current_user.user_id, offer_id, "farmer", payload)


@router.post("/offers/{offer_id}/counter-as-buyer", response_model=CounterOfferResponse, status_code=201)
def create_counter_offer_as_buyer(
    offer_id: uuid.UUID,
    payload: CounterOfferCreateRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> CounterOfferResponse:
    return offer_service.create_counter_offer(db, current_user.user_id, offer_id, "buyer", payload)


@router.post("/offers/{offer_id}/accept", response_model=SaleOrderResponse)
def accept_offer(
    offer_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    """Concurrency-safe: takes a real row lock on the listing before
    checking/decrementing available quantity - see offer_service.py."""
    return offer_service.accept_offer(db, current_user.user_id, offer_id)


@router.post("/offers/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(
    offer_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OfferResponse:
    return offer_service.reject_offer(db, current_user.user_id, offer_id)


# --- Sales (farmer side) ---

@router.get("/sales", response_model=SaleOrderListResponse)
def list_my_sales(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderListResponse:
    return sale_order_service.list_my_sales(db, current_user.user_id, limit=limit, offset=offset)


@router.get("/sales/{sale_id}", response_model=SaleOrderResponse)
def get_sale(
    sale_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    return sale_order_service.get_my_sale(db, current_user.user_id, sale_id)


@router.post("/sales/{sale_id}/accept", response_model=SaleOrderResponse)
def farmer_accept_sale(
    sale_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    return sale_order_service.farmer_accept(db, current_user.user_id, sale_id)


@router.post("/sales/{sale_id}/advance", response_model=SaleOrderResponse)
def advance_sale(
    sale_id: uuid.UUID,
    target_status: SaleOrderStatus,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    """A single endpoint for the farmer-driven PREPARING -> READY_FOR_COLLECTION
    -> COLLECTED -> IN_TRANSIT -> DELIVERED chain."""
    return sale_order_service.advance_status(db, current_user.user_id, sale_id, target_status)


@router.post("/sales/{sale_id}/cancel", response_model=SaleOrderResponse)
def cancel_sale_as_farmer(
    sale_id: uuid.UUID,
    payload: SaleCancelRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    return sale_order_service.cancel_sale(db, current_user.user_id, sale_id, payload, "farmer")


@router.post("/sales/{sale_id}/dispute", response_model=SaleDisputeResponse, status_code=201)
def create_dispute_as_farmer(
    sale_id: uuid.UUID,
    payload: SaleDisputeCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SaleDisputeResponse:
    return sale_order_service.create_dispute(db, current_user.user_id, sale_id, payload, "farmer")


@router.post("/sales/{sale_id}/feedback", status_code=204)
def submit_feedback_as_farmer(
    sale_id: uuid.UUID,
    payload: SaleFeedbackCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    sale_order_service.submit_feedback(db, current_user.user_id, sale_id, payload, "farmer")


@router.get("/disputes", response_model=SaleDisputeListResponse)
def list_open_sale_disputes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> SaleDisputeListResponse:
    return sale_order_service.list_open_disputes(db, limit=limit, offset=offset)


@router.post("/disputes/{dispute_id}/resolve", response_model=SaleDisputeResponse)
def resolve_sale_dispute(
    dispute_id: uuid.UUID,
    payload: SaleDisputeResolveRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> SaleDisputeResponse:
    return sale_order_service.resolve_dispute(db, current_user.user_id, dispute_id, payload)


@router.post("/disputes/{dispute_id}/quality-details", status_code=204)
def add_quality_dispute_details(
    dispute_id: uuid.UUID,
    payload: QualityDisputeCreateRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> None:
    sale_order_service.add_quality_dispute_details(db, dispute_id, payload)


# --- Sales (buyer side) ---

@router.get("/purchases", response_model=SaleOrderListResponse)
def list_my_purchases(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> SaleOrderListResponse:
    return sale_order_service.list_my_purchases(db, current_user.user_id, limit=limit, offset=offset)


@router.post("/purchases/{sale_id}/confirm-delivery", response_model=SaleOrderResponse)
def buyer_confirm_delivery(
    sale_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    return sale_order_service.buyer_confirm_delivery(db, current_user.user_id, sale_id)


@router.post("/purchases/{sale_id}/pay")
def initiate_sale_payment(
    sale_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
):
    payment = sale_order_service.initiate_payment(db, current_user.user_id, sale_id)
    return {"payment_id": str(payment.id), "status": payment.status.value, "amount": str(payment.amount)}


@router.post("/purchases/{sale_id}/pay/complete")
def complete_sale_payment(
    sale_id: uuid.UUID,
    succeed: bool = True,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
):
    """SANDBOX/TEST-ONLY - see docs/PAYMENT_AND_SETTLEMENT.md."""
    payment = sale_order_service.complete_payment(db, current_user.user_id, sale_id, succeed)
    return {"payment_id": str(payment.id), "status": payment.status.value}


@router.post("/purchases/{sale_id}/cancel", response_model=SaleOrderResponse)
def cancel_sale_as_buyer(
    sale_id: uuid.UUID,
    payload: SaleCancelRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> SaleOrderResponse:
    return sale_order_service.cancel_sale(db, current_user.user_id, sale_id, payload, "buyer")


@router.post("/purchases/{sale_id}/dispute", response_model=SaleDisputeResponse, status_code=201)
def create_dispute_as_buyer(
    sale_id: uuid.UUID,
    payload: SaleDisputeCreateRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> SaleDisputeResponse:
    return sale_order_service.create_dispute(db, current_user.user_id, sale_id, payload, "buyer")


@router.post("/purchases/{sale_id}/feedback", status_code=204)
def submit_feedback_as_buyer(
    sale_id: uuid.UUID,
    payload: SaleFeedbackCreateRequest,
    current_user: CurrentUser = Depends(require_role(_BUYER_ROLE)),
    db: Session = Depends(get_db),
) -> None:
    sale_order_service.submit_feedback(db, current_user.user_id, sale_id, payload, "buyer")
