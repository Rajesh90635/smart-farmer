"""
Harvest lifecycle. AI/weather may suggest a crop is approaching harvest
(a future integration point - Prompt 6's crop-stage intelligence is not
wired into automatic status transitions here), but every status change
past PLANNED requires an explicit farmer action through these functions -
there is no scheduled job or AI callback anywhere in this phase that
mutates HarvestRecord.status.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.harvest_listing import HarvestListing
from app.models.harvest_record import HarvestRecord, HarvestStatus
from app.repositories import crop_cycle_repository, harvest_repository
from app.schemas.harvest import (
    HarvestConfirmReadyRequest,
    HarvestListingCreateRequest,
    HarvestListingListResponse,
    HarvestListingResponse,
    HarvestListResponse,
    HarvestResponse,
)
from app.services.audit_logger import AuditLogger


def get_or_create_harvest_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> HarvestResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    existing = harvest_repository.get_harvest_by_crop_cycle(db, crop_cycle_id)
    if existing is not None:
        return HarvestResponse.model_validate(existing)

    harvest = HarvestRecord(
        farmer_id=farmer_uuid,
        farm_id=crop_cycle.plot.farm_id,
        plot_id=crop_cycle.plot_id,
        crop_cycle_id=crop_cycle.id,
        crop_id=crop_cycle.crop_id,
        expected_harvest_date=crop_cycle.expected_harvest_date,
        status=HarvestStatus.PLANNED,
    )
    harvest_repository.create_harvest(db, harvest)
    AuditLogger(db).log("HARVEST_RECORD_CREATED", actor_id=farmer_id, actor_role="farmer", entity="harvest_record", entity_id=str(harvest.id))
    db.commit()
    db.refresh(harvest)
    return HarvestResponse.model_validate(harvest)


def mark_approaching(db: Session, farmer_id: str, harvest_id: uuid.UUID) -> HarvestResponse:
    harvest = harvest_repository.get_harvest_owned(db, harvest_id, uuid.UUID(farmer_id))
    if harvest is None:
        raise AppError(error_codes.NOT_FOUND, "Harvest record not found.", 404)
    if harvest.status == HarvestStatus.PLANNED:
        harvest.status = HarvestStatus.APPROACHING
    db.commit()
    db.refresh(harvest)
    return HarvestResponse.model_validate(harvest)


def confirm_ready(db: Session, farmer_id: str, harvest_id: uuid.UUID, payload: HarvestConfirmReadyRequest) -> HarvestResponse:
    harvest = harvest_repository.get_harvest_owned(db, harvest_id, uuid.UUID(farmer_id))
    if harvest is None:
        raise AppError(error_codes.NOT_FOUND, "Harvest record not found.", 404)

    harvest.status = HarvestStatus.READY
    if payload.actual_harvest_date:
        harvest.actual_harvest_date = payload.actual_harvest_date
    if payload.estimated_quantity:
        harvest.estimated_quantity = payload.estimated_quantity

    AuditLogger(db).log("HARVEST_CONFIRMED_READY", actor_id=farmer_id, actor_role="farmer", entity="harvest_record", entity_id=str(harvest.id))
    db.commit()
    db.refresh(harvest)
    return HarvestResponse.model_validate(harvest)


def list_my_harvests(db: Session, farmer_id: str, *, limit: int = 50, offset: int = 0) -> HarvestListResponse:
    items, total = harvest_repository.list_harvests_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return HarvestListResponse(items=[HarvestResponse.model_validate(h) for h in items], total=total)


def create_listing(db: Session, farmer_id: str, harvest_id: uuid.UUID, payload: HarvestListingCreateRequest) -> HarvestListingResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    harvest = harvest_repository.get_harvest_owned(db, harvest_id, farmer_uuid)
    if harvest is None:
        raise AppError(error_codes.NOT_FOUND, "Harvest record not found.", 404)

    existing_active = harvest_repository.get_active_listing_for_crop_cycle(db, harvest.id)
    if existing_active is not None and not payload.confirm_duplicate:
        raise AppError(
            "DUPLICATE_LISTING_WARNING",
            "You already have an active listing for this crop. Pass confirm_duplicate=true to create another anyway.",
            409,
        )

    listing = HarvestListing(
        harvest_record_id=harvest.id,
        farmer_id=farmer_uuid,
        crop_id=harvest.crop_id,
        quantity_available=payload.quantity_available,
        unit=payload.unit,
        quality_grade=payload.quality_grade,
        expected_availability_date=payload.expected_availability_date,
        service_area=payload.service_area,
        preferred_price=payload.preferred_price,
        delivery_option=payload.delivery_option,
        notes=payload.notes,
    )
    harvest_repository.create_listing(db, listing)
    harvest.status = HarvestStatus.LISTED

    AuditLogger(db).log("HARVEST_LISTING_CREATED", actor_id=farmer_id, actor_role="farmer", entity="harvest_listing", entity_id=str(listing.id))
    db.commit()
    db.refresh(listing)
    return HarvestListingResponse.model_validate(listing)


def list_my_listings(db: Session, farmer_id: str, *, limit: int = 50, offset: int = 0) -> HarvestListingListResponse:
    items, total = harvest_repository.list_listings_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return HarvestListingListResponse(items=[HarvestListingResponse.model_validate(i) for i in items], total=total)


def list_marketplace_listings(db: Session, *, crop_id: uuid.UUID | None = None, limit: int = 50, offset: int = 0) -> HarvestListingListResponse:
    items, total = harvest_repository.list_active_listings(db, crop_id=crop_id, limit=limit, offset=offset)
    return HarvestListingListResponse(items=[HarvestListingResponse.model_validate(i) for i in items], total=total)
