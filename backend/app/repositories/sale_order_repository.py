import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sale_dispute import QualityDispute, SaleDispute, SaleFeedback
from app.models.sale_order import SaleOrder


def create_sale_order(db: Session, sale: SaleOrder) -> SaleOrder:
    db.add(sale)
    return sale


def get_sale_owned_by_farmer(db: Session, sale_id: uuid.UUID, farmer_id: uuid.UUID) -> SaleOrder | None:
    return db.execute(select(SaleOrder).where(SaleOrder.id == sale_id, SaleOrder.farmer_id == farmer_id)).scalar_one_or_none()


def get_sale_owned_by_buyer(db: Session, sale_id: uuid.UUID, buyer_id: uuid.UUID) -> SaleOrder | None:
    return db.execute(select(SaleOrder).where(SaleOrder.id == sale_id, SaleOrder.buyer_id == buyer_id)).scalar_one_or_none()


def get_sale_by_id(db: Session, sale_id: uuid.UUID) -> SaleOrder | None:
    return db.get(SaleOrder, sale_id)


def list_sales_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[SaleOrder], int]:
    stmt = select(SaleOrder).where(SaleOrder.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(SaleOrder.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def list_sales_for_buyer(db: Session, buyer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[SaleOrder], int]:
    stmt = select(SaleOrder).where(SaleOrder.buyer_id == buyer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(SaleOrder.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def create_dispute(db: Session, dispute: SaleDispute) -> SaleDispute:
    db.add(dispute)
    return dispute


def get_dispute(db: Session, dispute_id: uuid.UUID) -> SaleDispute | None:
    return db.get(SaleDispute, dispute_id)


def get_dispute_for_sale(db: Session, sale_id: uuid.UUID) -> SaleDispute | None:
    return db.execute(select(SaleDispute).where(SaleDispute.sale_order_id == sale_id)).scalar_one_or_none()


def create_quality_dispute(db: Session, quality_dispute: QualityDispute) -> QualityDispute:
    db.add(quality_dispute)
    return quality_dispute


def get_quality_dispute(db: Session, sale_dispute_id: uuid.UUID) -> QualityDispute | None:
    return db.execute(select(QualityDispute).where(QualityDispute.sale_dispute_id == sale_dispute_id)).scalar_one_or_none()


def create_feedback(db: Session, feedback: SaleFeedback) -> SaleFeedback:
    db.add(feedback)
    return feedback


def get_feedback(db: Session, sale_id: uuid.UUID, given_by_role: str) -> SaleFeedback | None:
    return db.execute(select(SaleFeedback).where(SaleFeedback.sale_order_id == sale_id, SaleFeedback.given_by_role == given_by_role)).scalar_one_or_none()
