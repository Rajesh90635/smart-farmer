import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.harvest_listing import HarvestListing
from app.models.harvest_record import HarvestRecord


def create_harvest(db: Session, harvest: HarvestRecord) -> HarvestRecord:
    db.add(harvest)
    return harvest


def get_most_recent_harvest_by_crop_cycle(db: Session, crop_cycle_id: uuid.UUID) -> HarvestRecord | None:
    """Used only by the pre-existing get-or-create flow, which must stay
    idempotent for single-harvest crops. Deliberately does NOT use
    scalar_one_or_none() - once a crop cycle has multiple harvests (Phase
    0), more than one row can match, and scalar_one_or_none() would raise
    MultipleResultsFound instead of returning a sane result. Order by
    created_at so behavior for existing single-harvest cycles is
    unchanged (there's only one row, so "most recent" == "the" row)."""
    return db.execute(
        select(HarvestRecord)
        .where(HarvestRecord.crop_cycle_id == crop_cycle_id)
        .order_by(HarvestRecord.created_at.desc())
        .limit(1)
    ).scalars().first()


def list_harvests_by_crop_cycle(db: Session, crop_cycle_id: uuid.UUID) -> list[HarvestRecord]:
    """The actual multi-harvest read path (Phase 0) - returns every
    harvest for a cycle, oldest first, for crops picked repeatedly."""
    return list(
        db.execute(
            select(HarvestRecord).where(HarvestRecord.crop_cycle_id == crop_cycle_id).order_by(HarvestRecord.created_at.asc())
        ).scalars().all()
    )


def get_harvest_owned(db: Session, harvest_id: uuid.UUID, farmer_id: uuid.UUID) -> HarvestRecord | None:
    return db.execute(select(HarvestRecord).where(HarvestRecord.id == harvest_id, HarvestRecord.farmer_id == farmer_id)).scalar_one_or_none()


def list_harvests_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[HarvestRecord], int]:
    stmt = select(HarvestRecord).where(HarvestRecord.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(HarvestRecord.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def create_listing(db: Session, listing: HarvestListing) -> HarvestListing:
    db.add(listing)
    return listing


def get_listing_by_id(db: Session, listing_id: uuid.UUID) -> HarvestListing | None:
    return db.get(HarvestListing, listing_id)


def get_listing_for_update(db: Session, listing_id: uuid.UUID) -> HarvestListing | None:
    """SELECT ... FOR UPDATE - the actual row lock that makes concurrent
    offer-acceptance safe. Must be called within an open transaction; the
    lock is held until commit/rollback."""
    return db.execute(select(HarvestListing).where(HarvestListing.id == listing_id).with_for_update()).scalar_one_or_none()


def get_listing_owned(db: Session, listing_id: uuid.UUID, farmer_id: uuid.UUID) -> HarvestListing | None:
    return db.execute(select(HarvestListing).where(HarvestListing.id == listing_id, HarvestListing.farmer_id == farmer_id)).scalar_one_or_none()


def get_active_listing_for_crop_cycle(db: Session, harvest_record_id: uuid.UUID) -> HarvestListing | None:
    return db.execute(
        select(HarvestListing).where(HarvestListing.harvest_record_id == harvest_record_id, HarvestListing.is_active.is_(True))
    ).scalar_one_or_none()


def list_active_listings(db: Session, *, crop_id: uuid.UUID | None, limit: int, offset: int) -> tuple[list[HarvestListing], int]:
    stmt = select(HarvestListing).where(HarvestListing.is_active.is_(True))
    if crop_id is not None:
        stmt = stmt.where(HarvestListing.crop_id == crop_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(HarvestListing.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def list_listings_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[HarvestListing], int]:
    stmt = select(HarvestListing).where(HarvestListing.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(HarvestListing.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total
