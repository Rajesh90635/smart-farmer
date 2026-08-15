# Product Catalog

## Controlled master catalog, not free-text dealer entry

`Product` is admin-curated. Dealers can never type an arbitrary product
name into existence - they select from already-APPROVED `Product` rows
when creating a `DealerProduct` listing. This mirrors the exact
create-then-approve pattern already established for professional
verification (Prompt 8) and applied to the product itself here.

## Status lifecycle (exactly 5 values, no extras)

`PENDING_REVIEW` (initial, always) -> `APPROVED` (admin action) /
`REJECTED` (admin action) -> `SUSPENDED` / `RECALLED` (admin action,
reachable from APPROVED). Only `APPROVED` products ever appear in farmer
search (`GET /products`) or can be newly listed by a dealer
(`POST /dealer-products`) - both enforced at the repository/service
layer, not just hidden in the UI.

## Pack size is baked into product identity

A 500ml bottle and a 1L bottle of the "same" product are **two separate
`Product` rows**, each with its own `pack_size_value`/`pack_size_unit`.
This is the simplest correct way to guarantee price comparisons are
always apples-to-apples (see docs/PRICE_TRANSPARENCY.md) - there's no
runtime unit-conversion logic that could silently compare incompatible
quantities, because incompatible quantities are structurally different
rows.

## Categories (a DB enum, not free text)

`SEED`, `FERTILIZER`, `BIO_INPUT`, `PEST_CONTROL_PRODUCT`,
`CROP_PROTECTION_PRODUCT`, `EQUIPMENT`, `OTHER_AGRICULTURAL_INPUT` -
exactly the categories given, deliberately never calling everything a
"medicine."

## `usage_information` is deliberately non-prescriptive

This field exists for generic descriptive text (e.g. "for foliar
application") - it must **never** contain a dosage or application rate.
This is enforced by convention and admin review at content-entry time,
not a technical filter, since the field is free text entered by an
admin. See docs/PRODUCT_SAFETY.md for the absolute rule this supports.

## Batch/expiry - one active batch per listing (a disclosed simplification)

`DealerProduct.batch_number`/`manufacturing_date`/`expiry_date` live on
the listing itself, not a separate `ProductBatch` table. This means a
dealer with multiple concurrent batches of the same product would need
separate listings to represent them distinctly - a real limitation for a
high-volume dealer, acceptable for this MVP's scale, and disclosed rather
than silently modeled as if full multi-batch inventory existed.
`is_expired()` is checked at the service layer before a listing is
included in checkout eligibility (Requirement 47's "do not allow expired
products to be sold").

## Image upload — not built this phase

`Product.image_storage_key` exists as a column, but no upload endpoint
was built this phase. It's designed to reuse the existing `FileStorage`
abstraction (Prompt 5) when that endpoint is eventually added — not a
new storage mechanism.

## Seed data — illustrative, clearly marked

5 seed products were added in the migration, all with `is_test_product =
true`. These exist so the schema/API can be exercised end-to-end; they
are not real, regulator-approved products and must never be presented as
such in a production deployment.
