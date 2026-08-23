# Seed Marketplace

## Fully reuses the Prompt 9 product catalog - no duplicate system

Per the explicit "reuse Product model, do not duplicate catalog systems"
instruction, seeds are simply `Product` rows with
`category = ProductCategory.SEED` (an enum value that already existed
since Prompt 9). There is no separate `SeedProduct`, `SeedVerification`,
or seed-specific catalog table.

## "Seed verification" = the existing Product approval workflow, unchanged

`Product.status` (PENDING_REVIEW/APPROVED/REJECTED/SUSPENDED/RECALLED)
already exactly matches what Requirement 46 asks for as
"SeedVerification" status - so it IS that, not a copy of it. A seed
product goes through the identical admin create-then-approve workflow as
a fertilizer or crop-protection product (see docs/PRODUCT_CATALOG.md,
Prompt 9).

## Endpoints - thin wrappers, not new logic

`GET /seeds` and `GET /seeds/{id}` call `product_service` functions
directly with a `category=SEED` filter - the only new code this phase is
the category filter itself
(`product_repository.list_products(..., category=...)`) and a check that
a requested seed product actually has `category == SEED` (returning 404
otherwise, so `/seeds/{id}` can't be used to fetch a non-seed product by
guessing an id).

## Purchase flow - fully reuses Prompt 9's cart/checkout/payment/delivery

Buying seeds uses the EXACT same `POST /cart`, `POST /orders/{id}/checkout`,
sandbox payment, and delivery endpoints as any other agricultural input -
no separate seed-ordering system exists, per Requirement 48's explicit
instruction.

## Price transparency - fully reuses Prompt 9

`GET /products/{id}/compare`, reference prices, price history, and Scam
Shield all work identically for a seed product as for any other
`Product` - no second price system was built (Requirement 51).

## Smart seed discovery - NOT built this phase (disclosed gap)

Requirement 50 envisions the seed marketplace being filtered by the
farmer's actual crop plan (e.g. a farmer growing tomatoes sees suitable
tomato seed products first). This phase's `/seeds` endpoint returns ALL
approved seed products, unfiltered by the farmer's crops - no code path
connects a farmer's `CropCycle`/`CropMaster` data to seed search
relevance yet. Building this without care would risk exactly the kind of
unsupported guarantee Requirement 50 explicitly warns against ("this is
guaranteed to produce X tons") - correctly left unconnected rather than
built with an implied yield promise.
