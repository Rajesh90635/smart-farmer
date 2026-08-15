# Dealer Workflow

## Reused verification, not a second system

Dealer/trader verification is the **exact same** `ProfessionalProfile`
(Prompt 8) used for field agents and experts - `verification_status`
(`pending`/`verified`/`rejected`/`suspended`/`expired`) is identical, and
only an ADMIN can change it. No dealer can self-verify, enforced by the
same role-gated endpoints already built in Prompt 8
(`/professionals/{id}/verify` etc.) - nothing new was built for dealer
verification specifically.

`DealerBusinessProfile` (new this phase) adds ONLY the fields a
commercial dealer genuinely needs that a field agent/expert profile
doesn't: business type, license number, contact info, business hours,
delivery areas. See docs/PROFESSIONAL_NETWORK.md (Prompt 8) for the base
profile.

## Listing a product (the only way a dealer can sell)

`POST /dealer-products` re-verifies BOTH conditions on every call, never
assuming from account state:
1. `ProfessionalProfile.verification_status == VERIFIED`
2. `Product.status == APPROVED`

A `PENDING`/`SUSPENDED`/`REJECTED`/`EXPIRED` dealer, or a listing attempt
against a `PENDING_REVIEW`/`REJECTED`/`SUSPENDED`/`RECALLED` product, is
rejected outright - verified by test
(`test_unverified_dealer_cannot_list_products`,
`test_dealer_cannot_list_a_pending_product`).

## Price changes are always audited

Every `PUT /dealer-products/{id}` that changes `price` writes a
`DealerPriceHistory` row (old price, new price, optional reason,
timestamp) and re-runs the price-anomaly check against the latest
reference price - verified by test.

## Dealer order dashboard

`GET /dealer/orders` lists only the calling dealer's own orders - never
another dealer's, verified by test
(`test_dealer_cannot_see_another_dealers_orders`). Actions available:
`accept`, `reject` (with a required reason), and `advance` through the
linear fulfillment chain (`preparing` -> ... -> `delivered`).

## Rejection requires a reason and restocks

`POST /dealer/orders/{id}/reject` requires `reason` in the request body
and automatically returns the reserved stock quantity to the listing -
verified by test.

## What a dealer/trader can NEVER do (structurally, not just permission-checked)

- Cannot alter an order's price after `CONFIRMED` - `Order`/`OrderItem`'s
  price fields are only ever written once, by `order_service.checkout`,
  never by any dealer-facing endpoint.
- Cannot see a farmer's crop-disease case or photo - no code path in this
  phase or Prompt 8 ever grants a dealer/trader a `PhotoAccessGrant` or a
  `CaseAssignment`.

## Business hours / delivery areas

`DealerBusinessProfile.business_hours` (JSONB, free-form) and
`delivery_areas` (JSONB list) are captured but **not yet enforced** in
checkout - a checkout doesn't currently reject an order because it falls
outside the dealer's stated delivery area or business hours. Disclosed
gap, not silently assumed handled.
