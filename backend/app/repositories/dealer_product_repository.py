import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dealer_price_history import DealerPriceHistory
from app.models.dealer_product import DealerProduct


def create(db: Session, listing: DealerProduct) -> DealerProduct:
    db.add(listing)
    return listing


def get_by_id(db: Session, listing_id: uuid.UUID) -> DealerProduct | None:
    return db.get(DealerProduct, listing_id)


def get_by_id_for_update(db: Session, listing_id: uuid.UUID) -> DealerProduct | None:
    """SELECT ... FOR UPDATE - locks the listing row so a concurrent
    checkout against the same listing can't read-then-decrement
    stock_quantity in an overlapping transaction (see harvest_repository's
    get_listing_for_update for the same pattern). Must be called within an
    open transaction; the lock is held until commit/rollback."""
    return db.execute(select(DealerProduct).where(DealerProduct.id == listing_id).with_for_update()).scalar_one_or_none()


def get_by_dealer_and_product(db: Session, dealer_id: uuid.UUID, product_id: uuid.UUID) -> DealerProduct | None:
    return db.execute(
        select(DealerProduct).where(DealerProduct.dealer_id == dealer_id, DealerProduct.product_id == product_id)
    ).scalar_one_or_none()


def get_owned_by_dealer(db: Session, listing_id: uuid.UUID, dealer_id: uuid.UUID) -> DealerProduct | None:
    return db.execute(
        select(DealerProduct).where(DealerProduct.id == listing_id, DealerProduct.dealer_id == dealer_id)
    ).scalar_one_or_none()


def list_listings_for_product(db: Session, product_id: uuid.UUID, *, available_only: bool = True) -> list[DealerProduct]:
    stmt = select(DealerProduct).where(DealerProduct.product_id == product_id)
    if available_only:
        stmt = stmt.where(DealerProduct.is_available.is_(True))
    return list(db.execute(stmt.order_by(DealerProduct.price.asc())).scalars().all())


def list_listings_for_dealer(db: Session, dealer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[DealerProduct], int]:
    stmt = select(DealerProduct).where(DealerProduct.dealer_id == dealer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(DealerProduct.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def create_price_history(db: Session, entry: DealerPriceHistory) -> DealerPriceHistory:
    db.add(entry)
    return entry


def list_price_history(db: Session, dealer_product_id: uuid.UUID) -> list[DealerPriceHistory]:
    return list(
        db.execute(select(DealerPriceHistory).where(DealerPriceHistory.dealer_product_id == dealer_product_id).order_by(DealerPriceHistory.changed_at.desc())).scalars().all()
    )
