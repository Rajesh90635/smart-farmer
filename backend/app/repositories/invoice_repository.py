"""
Invoice repository. Ownership enforced the same way as every other
farmer-scoped entity in this project.
"""
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice


def create(db: Session, invoice: Invoice) -> Invoice:
    db.add(invoice)
    return invoice


def get_owned(db: Session, invoice_id: uuid.UUID, farmer_id: uuid.UUID) -> Invoice | None:
    return db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[Invoice]:
    return list(
        db.execute(
            select(Invoice).where(Invoice.crop_cycle_id == crop_cycle_id, Invoice.farmer_id == farmer_id).order_by(Invoice.created_at.desc())
        )
        .scalars()
        .all()
    )


def delete(db: Session, invoice: Invoice) -> None:
    db.execute(sa_delete(Invoice).where(Invoice.id == invoice.id))
