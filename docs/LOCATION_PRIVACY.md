# Location Privacy (Harvest Marketplace-specific)

> Supplements docs/SECURITY.md and the Prompt 8/9 location-privacy
> sections already in place. This document covers what's specific to
> harvest selling.

## Two distinct location fields, two distinct exposure rules

| Field | Where | Exposure |
|---|---|---|
| `HarvestListing.service_area` | The public listing | Approximate only (state/district as entered by the farmer) - shown to EVERY browsing buyer, always |
| `SaleOrder.exact_collection_location` | The confirmed sale | Exact - but **not built this phase** (see docs/SALE_WORKFLOW.md's disclosed gap); the field exists precisely so a future endpoint can populate it only after an appropriate confirmation stage, never before |

## What is verified true right now

- No code path copies `Farm.latitude`/`longitude` into `HarvestListing.service_area`
  - verified by test that the field only ever contains the keys the
    farmer explicitly provided (`state`/`district` in this phase's
    test data), never `latitude`/`longitude`.
- `SaleOrder.service_area_snapshot` is copied from the LISTING's
  approximate area at sale-creation time, not the farm's exact
  coordinates - the buyer never gains access to precise location merely
  by having an offer accepted.

## What is NOT yet built (disclosed, not silently assumed done)

- **Access audit for exact collection location** (Requirement 29 - "record
  location shared timestamp, who accessed it, why") - moot until the
  exact-location-sharing endpoint itself exists. When built, it should
  follow the exact `AuditLogger` pattern already used for crop-photo
  access (Prompt 8's `CASE_PHOTO_ACCESSED` audit action) as a direct
  template.
- **Buyer's own location/service-area privacy** - `ProfessionalProfile.service_area`
  (reused from Prompt 8) is already approximate-only by the same
  convention, but no code path in this phase specifically re-verifies
  that a buyer's exact address (if one is ever captured) stays private -
  moot since no such field exists yet.
