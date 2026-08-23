# Marketplace Scam Shield (Harvest Selling)

See docs/SCAM_SHIELD.md (Prompt 9) for the full price-anomaly Scam Shield
built for agricultural input purchases - that implementation is unchanged
and fully reused for seed purchases (see docs/SEED_MARKETPLACE.md).

## What applies to harvest SELLING this phase

| Check | Status |
|---|---|
| Buyer verification | ✅ Hard gate - unverified buyers cannot make offers at all (404, not just a warning) |
| Offer transparency | ✅ Price, quantity, and terms are always structured fields, never hidden in free text |
| Payment terms | ✅ Sandbox-only, same honesty as Prompt 9 - a sale is never PAID without real (sandbox) payment confirmation |
| Collection terms | ✅ `collection_method` is always shown as a structured field on the sale |
| Buyer history | ❌ Not built - no dispute-rate/cancellation-rate figure is computed or surfaced (see docs/MARKETPLACE_TRUST.md) |
| Price-anomaly-style warning for a harvest offer | ❌ Not built - there's no "reference price for this crop in this region" data source this phase to compare an offer against (see docs/PROMPT10_ASSUMPTIONS_RISKS.md) |

## Never an unverified accusation

Consistent with Prompt 9's absolute rule, nothing in this phase's code
produces language like "scammer" or "fraud" - the only currently-enforced
protection (buyer verification) is a hard structural gate, not a warning
message, so there was no accusatory-language surface to introduce this
phase in the first place.

## No hidden charges - verified structurally

`SaleOrder.gross_value`, `charges`, and `net_value` are always three
separate fields in every sale response - `charges` is currently always
`0` (no transport/platform fee model configured, see
docs/PAYMENT_AND_SETTLEMENT.md), but the field exists and is never
folded into `gross_value` silently, so adding a real fee later doesn't
require a schema change or risk hiding it.

## No changing agreed price silently - verified by test

Once a `SaleOrder` is created, `price_per_unit`/`quantity`/`gross_value`/
`net_value` are frozen - no service function in `sale_order_service.py`
ever recalculates or overwrites them. Verified indirectly by every sale
lifecycle test: the price shown at creation matches the price shown at
every subsequent status check.
