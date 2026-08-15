# Scam Shield

## What it actually checks (this phase)

`GET /dealer-products/{id}/scam-shield` runs the price-anomaly comparison
(`app/services/price_comparison.py:compare_price`) against the latest
reference price and returns a neutral status. This is the ONE check fully
implemented this phase - the fuller checklist (dealer verification,
duplicate listings, suspicious discounts, delivery mismatch, payment
safety) is partially covered elsewhere in the platform (dealer
verification is checked before any offer is ever shown at all - see
below) but not consolidated into one "Scam Shield score" endpoint.

## Language - the absolute rule, verified by test

The response `message` field is built entirely from neutral, factual
templates ("This price is X% above the reference price for this
product... Consider comparing with other dealers.") - never an
accusation. `test_scam_shield_flags_a_high_price` explicitly asserts the
message never contains "scammer," "fraud," "cheater," or "cheat," no
matter how large the price deviation is. There is no code path in this
service that can produce an accusatory string - the message is
template-based, not free-form generation.

## Anomaly levels (3 non-normal levels + implicit "normal")

| Level | Threshold (configurable, PLACEHOLDER - not market-validated) |
|---|---|
| (normal - not flagged) | < 15% above reference |
| HIGH | ≥ 15% above reference |
| UNUSUAL | ≥ 30% above reference |
| REVIEW_REQUIRED | ≥ 50% above reference |

A `PriceAnomalyFlag` row is only persisted for non-normal levels -
normal prices are never stored as flags, keeping the flag table an
actual review queue for admin (Requirement 55), not a log of every price
ever checked.

## Dealer verification is a HARD GATE before Scam Shield even matters

`price_query_service.compare_offers_for_product` silently excludes any
dealer whose `verification_status != VERIFIED` from the comparison
results entirely - an unverified dealer's offer is never shown to a
farmer at all, regardless of its price. Verified by test
(`test_compare_offers_excludes_unverified_dealer`). This is arguably a
stronger protection than a price warning: the farmer never even sees the
option to buy from an unverified seller.

## What Scam Shield does NOT check yet (disclosed gaps)

- Duplicate product listings by the same dealer.
- Suspicious/predatory discount patterns.
- Delivery-area mismatch between what's promised and what's deliverable.
- Payment-safety signals beyond "sandbox only" (no real gateway risk
  exists yet since there's no real gateway).
- A consolidated 🟢/🟡/🔴 single visual status combining multiple checks -
  this phase only surfaces the price-anomaly check directly; a true
  multi-factor Scam Shield status is future work.

## Never automatically blocks a purchase

Per Requirement 27, a high/unusual/review-required price flag is
informational only - `checkout()` does not check `PriceAnomalyFlag` at
all and will proceed even against a flagged listing. The farmer is shown
the warning (via the Scam Shield endpoint, to be surfaced in a future
Flutter screen) but retains the choice to buy.
