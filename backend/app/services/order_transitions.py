"""
Single source of truth for order status transition validation - reused by
order_service, dealer_order_service, and payment_service rather than each
re-implementing the same check (which risks the three copies drifting out
of sync over time).
"""
from app.core import error_codes
from app.core.errors import AppError
from app.models.order import ALLOWED_ORDER_TRANSITIONS, Order, OrderStatus


def apply_transition(order: Order, target: OrderStatus) -> None:
    allowed = ALLOWED_ORDER_TRANSITIONS.get(order.status, set())
    if target not in allowed:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot change order status from '{order.status.value}' to '{target.value}'.", 409)
    order.status = target
