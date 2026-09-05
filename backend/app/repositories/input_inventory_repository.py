import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.input_inventory import InputInventoryItem


def create(db: Session, item: InputInventoryItem) -> InputInventoryItem:
    db.add(item)
    return item


def get_owned(db: Session, item_id: uuid.UUID, farmer_id: uuid.UUID) -> InputInventoryItem | None:
    return db.execute(
        select(InputInventoryItem).where(InputInventoryItem.id == item_id, InputInventoryItem.farmer_id == farmer_id)
    ).scalar_one_or_none()


def list_for_farmer(db: Session, farmer_id: uuid.UUID) -> list[InputInventoryItem]:
    return list(
        db.execute(
            select(InputInventoryItem).where(InputInventoryItem.farmer_id == farmer_id).order_by(InputInventoryItem.created_at.desc())
        ).scalars().all()
    )


def list_expiring_unalerted(db: Session, *, on_or_before: date) -> list[InputInventoryItem]:
    """Used by the background expiry sweep (input_inventory_service.py) -
    quantity > 0 (no point warning about a fully-consumed item) and not
    already alerted for this expiry (expiry_alerted_at is None)."""
    return list(
        db.execute(
            select(InputInventoryItem).where(
                InputInventoryItem.expiry_date.isnot(None),
                InputInventoryItem.expiry_date <= on_or_before,
                InputInventoryItem.expiry_alerted_at.is_(None),
                InputInventoryItem.quantity > 0,
            )
        ).scalars().all()
    )
