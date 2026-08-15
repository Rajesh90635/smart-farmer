# Sale Workflow

## The state machine (exactly the 12 specified statuses)

```
PENDING -> ACCEPTED -> PREPARING -> READY_FOR_COLLECTION -> COLLECTED
    |          |             |               |
CANCELLED  CANCELLED     CANCELLED       CANCELLED
                                                |
                                          IN_TRANSIT -> DELIVERED -> PAYMENT_PENDING -> PAID -> COMPLETED
                                                             |             |              |
                                                          DISPUTED     DISPUTED       DISPUTED
                                                             |
                                              PAYMENT_PENDING / COMPLETED / CANCELLED (dispute resolution)
```

`ALLOWED_SALE_ORDER_TRANSITIONS` (`app/models/sale_order.py`) is the
single source of truth, enforced by every service function through one
shared `_apply_transition` helper - the same discipline established for
`Order` (Prompt 9) and `CropHealthCase` (Prompt 8).

## Payment and Delivery are REUSED, not duplicated - the core Prompt 9 mandate

`SaleOrder` payments and deliveries flow through the **exact same**
`Payment` and `Delivery` tables Prompt 9 built for agricultural-input
orders. Both tables gained a nullable `sale_order_id` column this phase
(alongside the pre-existing, now-also-nullable `order_id`) -
"exactly one is set" is maintained by construction: every write in
`order_service.py`/`payment_service.py` (Prompt 9) sets `order_id` and
leaves `sale_order_id` NULL; every write in `sale_order_service.py`
(this phase) does the reverse. No `SalePayment`/`SaleDelivery` duplicate
tables exist.

**Disclosed limitation:** there is no DB-level `CHECK` constraint
enforcing "exactly one of order_id/sale_order_id" - it's maintained by
service-layer discipline only, consistent with how this project already
handles several other "exactly one of" invariants without a DB
constraint. A future hardening pass could add one.

## Sandbox payment - same honesty as Prompt 9

`sale_order_service.complete_payment()` is the same kind of TEST-ONLY
sandbox simulator as Prompt 9's `payment_service.complete_payment()` -
clearly not a real gateway integration. See docs/PAYMENT_AND_SETTLEMENT.md.

## Cancellation - requires a real reason, restores quantity

`SaleOrder.cancellation_reason` must be one of the 7 specified values
(`CANCELLATION_REASONS` in `app/models/sale_order.py`) - an invalid
reason is rejected with `422`, verified by test. Cancelling a sale
restores the accepted quantity back to the originating `HarvestListing`
(under the same row lock used for acceptance) and reactivates the
listing if it had gone inactive - verified by test
(`test_cancellation_restores_listing_quantity`).

## Dispute - only reachable from delivery-stage-or-later

A dispute can only be filed once the sale has reached `DELIVERED`,
`PAYMENT_PENDING`, or `PAID` - verified by test that an earlier-stage
sale (still `PENDING`) is rejected with `422`
(`test_dispute_requires_delivery_stage`).

## Collection location - the disclosed gap

`SaleOrder.exact_collection_location` exists as a field specifically to
satisfy "reveal exact collection information only when required, after
sale confirmation" (Requirement 29) - but **no endpoint currently
populates it**. The farmer-approximate `service_area_snapshot` (copied
from the listing at sale creation) is the only location data actually
flowing through this phase. A future endpoint (farmer explicitly shares
exact location once the sale reaches an appropriate stage, e.g.
`ACCEPTED` or `READY_FOR_COLLECTION`) is the natural next step, with the
same "who accessed it, when, why" audit pattern already used for crop
photo access (Prompt 8) as the template to follow.

## Buyer's own delivery confirmation vs. farmer's dispatch-side status

Mirrors Prompt 9's exact pattern: the farmer advancing through
`COLLECTED -> IN_TRANSIT -> DELIVERED` is their side of fulfillment;
`POST /marketplace/purchases/{id}/confirm-delivery` (buyer-only) is a
separate action transitioning to `PAYMENT_PENDING` - the buyer's own
acknowledgment, not assumed automatically from the farmer's status
update.
