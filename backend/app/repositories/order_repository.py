import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.delivery import Delivery
from app.models.order import Order, OrderItem, OrderStatus
from app.models.order_dispute import OrderDispute, Refund
from app.models.payment import Payment


def create_order(db: Session, order: Order) -> Order:
    db.add(order)
    return order


def get_order_owned_by_farmer(db: Session, order_id: uuid.UUID, farmer_id: uuid.UUID) -> Order | None:
    return db.execute(select(Order).where(Order.id == order_id, Order.farmer_id == farmer_id).options(joinedload(Order.items))).unique().scalar_one_or_none()


def get_order_by_id_admin(db: Session, order_id: uuid.UUID) -> Order | None:
    """Unrestricted lookup for admin actions (dispute resolution, refund
    completion) - admin bypasses the farmer/dealer ownership check by
    design, since they're resolving a dispute BETWEEN those two parties."""
    return db.execute(select(Order).where(Order.id == order_id).options(joinedload(Order.items))).unique().scalar_one_or_none()


def get_order_owned_by_dealer(db: Session, order_id: uuid.UUID, dealer_id: uuid.UUID) -> Order | None:
    return db.execute(select(Order).where(Order.id == order_id, Order.dealer_id == dealer_id).options(joinedload(Order.items))).unique().scalar_one_or_none()


def get_draft_order(db: Session, farmer_id: uuid.UUID, dealer_id: uuid.UUID) -> Order | None:
    return db.execute(
        select(Order).where(Order.farmer_id == farmer_id, Order.dealer_id == dealer_id, Order.status == OrderStatus.DRAFT).options(joinedload(Order.items))
    ).unique().scalar_one_or_none()


def get_by_idempotency_key(db: Session, idempotency_key: str) -> Order | None:
    return db.execute(select(Order).where(Order.idempotency_key == idempotency_key)).scalar_one_or_none()


def list_orders_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Order], int]:
    stmt = select(Order).where(Order.farmer_id == farmer_id, Order.status != OrderStatus.DRAFT)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def list_orders_for_dealer(db: Session, dealer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Order], int]:
    stmt = select(Order).where(Order.dealer_id == dealer_id, Order.status != OrderStatus.DRAFT)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def get_item_by_dealer_product(db: Session, order_id: uuid.UUID, dealer_product_id: uuid.UUID) -> OrderItem | None:
    return db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id, OrderItem.dealer_product_id == dealer_product_id)
    ).scalar_one_or_none()


def create_item(db: Session, item: OrderItem) -> OrderItem:
    db.add(item)
    return item


def delete_item(db: Session, item: OrderItem) -> None:
    db.execute(delete(OrderItem).where(OrderItem.id == item.id))


def create_payment(db: Session, payment: Payment) -> Payment:
    db.add(payment)
    return payment


def get_payment(db: Session, payment_id: uuid.UUID) -> Payment | None:
    return db.get(Payment, payment_id)


def get_latest_payment_for_order(db: Session, order_id: uuid.UUID) -> Payment | None:
    return db.execute(select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc()).limit(1)).scalar_one_or_none()


def create_delivery(db: Session, delivery: Delivery) -> Delivery:
    db.add(delivery)
    return delivery


def get_delivery_for_order(db: Session, order_id: uuid.UUID) -> Delivery | None:
    return db.execute(select(Delivery).where(Delivery.order_id == order_id)).scalar_one_or_none()


def create_dispute(db: Session, dispute: OrderDispute) -> OrderDispute:
    db.add(dispute)
    return dispute


def get_dispute(db: Session, dispute_id: uuid.UUID) -> OrderDispute | None:
    return db.get(OrderDispute, dispute_id)


def get_dispute_for_order(db: Session, order_id: uuid.UUID) -> OrderDispute | None:
    return db.execute(select(OrderDispute).where(OrderDispute.order_id == order_id)).scalar_one_or_none()


def create_refund(db: Session, refund: Refund) -> Refund:
    db.add(refund)
    return refund


def get_refund_for_order(db: Session, order_id: uuid.UUID) -> Refund | None:
    return db.execute(select(Refund).where(Refund.order_id == order_id)).scalar_one_or_none()
