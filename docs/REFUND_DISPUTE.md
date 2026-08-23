# Refund & Dispute

## Dispute - only reachable after delivery, per the transition map

`OrderDispute` can only be created for an order in `DELIVERED` or
`OUT_FOR_DELIVERY` status - enforced by checking the order's current
status before creation, and the resulting transition to `DISPUTED` goes
through the same shared `order_transitions.apply_transition()` used
everywhere else. Verified by test that filing a dispute against a
`CONFIRMED` (not yet delivered) order returns `422`.

## Reasons (exactly the 7 specified)

`WRONG_PRODUCT`, `MISSING_ITEM`, `DAMAGED_PRODUCT`, `PAYMENT_ISSUE`,
`DELIVERY_ISSUE`, `UNEXPECTED_CHARGE`, `PRODUCT_AUTHENTICITY_CONCERN`.

## Photo evidence - NOT built this phase (disclosed gap)

Requirement 80 asks for optional photo evidence on a dispute.
`OrderDispute.evidence_note` is free text only this phase - no image
upload endpoint exists for dispute evidence. Reusing the crop-photo
upload infrastructure (Prompt 5) directly would conflate two different
domains (crop health photos vs. order/product evidence photos); the
correct extension is a parallel upload path using the same `FileStorage`
abstraction, not built yet.

## Resolution - admin-only, never automatic

`POST /disputes/{id}/resolve` requires the `ADMIN` role and an explicit
`status` + optional `refund_type`/`refund_amount`/`resolution_note`. No
code path resolves a dispute or issues a refund automatically based on
the dispute reason alone - a human decision is always required.

## Refund - foundation only, no real money movement

`Refund.status` reaching `COMPLETED` means the sandbox/manual bookkeeping
was marked complete by an admin (`POST /orders/{id}/refund/complete`) -
**never a real payment-gateway refund API call**, since no real gateway is
integrated this phase (see docs/PAYMENT_ARCHITECTURE.md). This must be
replaced with a real refund API integration before real money is
involved - flagged explicitly so it's never mistaken for a working refund
system.

## What happens to the order

Resolving a dispute with a non-`NO_REFUND` type transitions the order to
`REFUND_PENDING`; completing the refund transitions it to `REFUNDED` -
both via the shared transition map, both audited.
