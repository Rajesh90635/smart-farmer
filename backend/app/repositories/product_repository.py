import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.price_anomaly_flag import PriceAnomalyFlag
from app.models.product import Product, ProductStatus
from app.models.reference_price import ReferencePrice


def create_product(db: Session, product: Product) -> Product:
    db.add(product)
    return product


def get_product(db: Session, product_id: uuid.UUID) -> Product | None:
    return db.get(Product, product_id)


def get_approved_product(db: Session, product_id: uuid.UUID) -> Product | None:
    product = db.get(Product, product_id)
    if product is None or product.status != ProductStatus.APPROVED:
        return None
    return product


def list_products(db: Session, *, status: ProductStatus | None, query: str | None, category=None, limit: int, offset: int) -> tuple[list[Product], int]:
    stmt = select(Product)
    if status is not None:
        stmt = stmt.where(Product.status == status)
    if query:
        stmt = stmt.where(Product.name.ilike(f"%{query}%"))
    if category is not None:
        stmt = stmt.where(Product.category == category)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(Product.name).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def create_reference_price(db: Session, ref: ReferencePrice) -> ReferencePrice:
    db.add(ref)
    return ref


def get_latest_reference_price(db: Session, product_id: uuid.UUID) -> ReferencePrice | None:
    return db.execute(
        select(ReferencePrice).where(ReferencePrice.product_id == product_id).order_by(ReferencePrice.effective_date.desc(), ReferencePrice.retrieved_at.desc()).limit(1)
    ).scalar_one_or_none()


def list_reference_price_history(db: Session, product_id: uuid.UUID) -> list[ReferencePrice]:
    return list(
        db.execute(select(ReferencePrice).where(ReferencePrice.product_id == product_id).order_by(ReferencePrice.effective_date.desc())).scalars().all()
    )


def create_anomaly_flag(db: Session, flag: PriceAnomalyFlag) -> PriceAnomalyFlag:
    db.add(flag)
    return flag


def list_unreviewed_anomaly_flags(db: Session, *, limit: int, offset: int) -> tuple[list[PriceAnomalyFlag], int]:
    stmt = select(PriceAnomalyFlag).where(PriceAnomalyFlag.reviewed_at.is_(None))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(PriceAnomalyFlag.detected_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total
