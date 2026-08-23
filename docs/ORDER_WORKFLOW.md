# Order Workflow

## Cart = a DRAFT order (a deliberate consolidation, not an oversight)

No `Cart`/`CartItem` tables exist. "Adding to cart" creates-or-reuses a
`DRAFT`-status `Order` scoped to `(farmer_id, dealer_id)` and adds/updates
`OrderItem` rows on it directly. This naturally satisfies "prefer
separate seller orders" (Requirement 31) - a farmer buying from two
dealers automatically gets two separate DRAFT orders, one per dealer,
with no extra logic needed to split them apart later.

No separate `PriceSnapshot` table exists either - `OrderItem`'s price
columns (`unit_price`, `discount_amount`, `tax_amount`,
`final_item_amount`) ARE the frozen snapshot, populated exactly once at
`CONFIRMED` time and never touched again.

## The state machine (exactly the 16 specified statuses)

```
DRAFT -> PENDING_CONFIRMATION -> CONFIRMED -> PAYMENT_PENDING -> PAID
                                                                    |
                                          +-------------------------+
                                          |                         |
                                   ACCEPTED_BY_DEALER            REJECTED -> REFUND_PENDING -> REFUNDED
                                          |
                                     PREPARING -> READY_FOR_DISPATCH -> DISPATCHED -> OUT_FOR_DELIVERY
                                                                                            |    |
                                                                                     DELIVERED  DISPUTED
                                                                                            |         |
                                                                                       DISPUTED   REFUND_PENDING
CANCELLED reachable from DRAFT/PENDING_CONFIRMATION/CONFIRMED/PAYMENT_PENDING/ACCEPTED_BY_DEALER
```

`ALLOWED_ORDER_TRANSITIONS` (`app/models/order.py`) is the single source
of truth - every service function calls the shared
`order_transitions.apply_transition()` helper, which raises `409` on any
disallowed jump. **A real inconsistency was caught and fixed during
development**: checkout initially jumped straight from `DRAFT` to
`CONFIRMED`, silently bypassing the map's required `PENDING_CONFIRMATION`
intermediate step. Fixed by making checkout pass through both transitions
explicitly rather than special-casing around the map - the map is never
lied to.

## Checkout - server-side recalculation, the absolute rule

`CheckoutRequest` contains only `idempotency_key` and `delivery_area` -
**no price field exists in the request schema at all**. Every amount is
read fresh from `DealerProduct.price` at confirmation time. Verified by
test with a real "dealer raises price after farmer adds to cart" scenario
- checkout correctly uses the new price.

At checkout, the following are all re-validated (Requirement 64), and any
failure prevents order creation:
- Dealer still `VERIFIED`.
- Each listing still `is_available`.
- Sufficient `stock_quantity` for the requested quantity.

## Duplicate-order protection

`Order.idempotency_key` has a **database-level unique constraint** - a
retried checkout call with the same key returns the already-confirmed
order rather than creating a second one. Verified by test.

## Dealer fulfillment

A single endpoint (`POST /dealer/orders/{id}/advance?target_status=...`)
handles the entire linear `PREPARING -> ... -> DELIVERED` chain, since
each step shares identical authorization and logic - only the target
status differs, and the shared transition map is what actually enforces
correctness, not the endpoint.

## Farmer delivery confirmation - a separate action from dealer's DELIVERED mark

The dealer marking `DELIVERED` (their side of "I dispatched and it
arrived") and the farmer calling `POST /orders/{id}/confirm-delivery`
(their side of "I received it") are kept as two distinct actions per
Requirement 43 - the farmer's confirmation doesn't change the order
status further this phase (it's recorded via audit log only), since
`DELIVERED` is already the terminal happy-path status in the transition
map; a future dispute is the mechanism for "I say I didn't receive it."
