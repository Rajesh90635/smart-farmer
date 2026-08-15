# Farmer Marketplace ("Sell Your Harvest")

## HarvestListing - the farmer-facing sell listing

Created from a `HarvestRecord` via `POST /harvests/{id}/listing`. Buyers
browse active listings via `GET /marketplace/listings` - only
`is_active=true` listings are ever shown, and `is_active` automatically
flips to `false` once `quantity_available` reaches zero (set inside the
same locked transaction that decrements it during offer acceptance - see
docs/OFFER_NEGOTIATION.md).

## Location privacy - approximate only, by construction

`HarvestListing.service_area` is a farmer-typed JSONB object
(`{state, district}` in this phase's usage) - there is no code path that
copies the farm's precise `latitude`/`longitude` into it. Verified by
test (`test_listing_service_area_never_contains_exact_coordinates_by_construction`):
the field never contains `latitude`/`longitude` keys at all, because
nothing ever writes them there.

**Exact collection location** (`SaleOrder.exact_collection_location`)
is a separate field on the SALE record, not the listing - it stays
`NULL` until an explicit farmer action populates it (not built this
phase - see docs/SALE_WORKFLOW.md's disclosed gap). The schema
correctly separates "what a browsing buyer sees" (always approximate)
from "what a confirmed buyer eventually needs" (exact, but gated).

## Duplicate listing handling (Requirement 65 - warn, don't silently block)

Creating a second active listing for the same `HarvestRecord` returns
`409` with an explicit warning message, UNLESS `confirm_duplicate=true`
is passed, in which case it's created anyway. Verified by test: the
first duplicate attempt is rejected, a `confirm_duplicate=true` retry
succeeds.

## Quantity control (Requirement 66)

`quantity_available` starts at the farmer's stated amount and is
decremented by exactly the accepted quantity every time an offer is
accepted (never by the *offered* amount before acceptance). Verified by
test with a real before/after check
(`test_accepting_offer_decrements_listing_quantity`).

## What's NOT built this phase (disclosed)

- **Smart buyer matching/ranking** (Requirement 39/40) - a farmer sees
  raw offers as they arrive; there's no `BuyerMatchingService` ranking
  buyers by verification/crop-fit/service-area/reputation the way
  Prompt 8's `nearby_professional_service.py` ranks professionals. This
  is a real, disclosed gap - the natural next step would mirror that
  exact pattern.
- **Demand signal display** - `DemandSignal` exists as a table (see
  docs/MARKETPLACE_TRUST.md) but nothing surfaces it on the listing or
  marketplace browse screens yet.
- **Photo upload for harvest listings** (Requirement 37) - no image
  field or upload endpoint exists on `HarvestListing` this phase.
