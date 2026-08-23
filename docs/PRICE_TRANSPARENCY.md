# Price Transparency

## The core promise: never an unexplained number

Every price shown to a farmer traces back to an explicit source:
`REFERENCE_PRICE` (sourced, timestamped, region-tagged), `DEALER_PRICE`
(the listing's current price), and the checkout-time breakdown
(`subtotal`, `discount`, `delivery_fee`, `tax`, `final_amount`) - never
mixed into one unexplained figure.

## Normalization - always same-unit comparison

`app/services/price_comparison.py:price_per_unit()` divides price by
`pack_size_value` - and because `Product` bakes pack size into product
identity (see docs/PRODUCT_CATALOG.md), every comparison is inherently
between the SAME unit. Verified by test with a real cross-pack-size
scenario: a 1L listing at ₹480 (₹0.48/ml) correctly compares as cheaper
per-unit than a 500ml reference at ₹250 (₹0.50/ml), rather than being
flagged as suspiciously different just because the totals differ.

## Reference price - always sourced, never invented

`ReferencePrice.source_type` is one of `OFFICIAL_SOURCE`,
`AUTHORIZED_MARKET_SOURCE`, `MANUFACTURER_REFERENCE`,
`VERIFIED_MARKET_DATA`, `ADMIN_ENTERED_REFERENCE` - there is no code path
that creates a `ReferencePrice` without an explicit source type. If none
exists for a product, `GET /products/{id}/prices` returns a real `404`
("Reference price unavailable") - verified by test - never a fabricated
number (Requirement 71's absolute rule).

## Price history - natural, no separate table needed

`ReferencePrice` rows are never updated in place - each new price is a
new row, so `GET /products/{id}/price-history` is simply every row for
that product ordered by `effective_date`. `DealerPriceHistory` (a
genuinely separate append-only table) captures every dealer price change
specifically, since that's a different kind of event (Requirement 57).

## Price staleness

`retrieved_at`/`effective_date` are always returned alongside a
reference price - the API does not hide how old the data is. **Not yet
built:** a farmer-facing "updated X days ago" wording computed from these
timestamps (Requirement 59) — the raw timestamps are available to the
client, but the friendly staleness message itself isn't rendered
server-side yet. Disclosed gap.

## Server-side calculation - the absolute rule, enforced structurally

`order_service.checkout()` never reads a price from the request body -
`CheckoutRequest` has no price field at all, only `idempotency_key` and
`delivery_area`. Every `OrderItem.unit_price` is read fresh from
`DealerProduct.price` at the moment of checkout. Verified by test with a
real scenario: a farmer adds an item to cart, the dealer raises the price
afterward, and checkout correctly uses the NEW price, not the one visible
when the item was added.
