# Offer & Negotiation

## Append-only negotiation history - the absolute rule, enforced by schema

`BuyerOffer` is the opening ask. `CounterOffer` rows are **append-only** -
every counter from either party (`proposed_by`: `farmer` or `buyer`) is a
NEW row referencing the same `buyer_offer_id`; no service function ever
updates or deletes a prior counter. Verified by test
(`test_offer_and_counter_offer_negotiation_history_is_never_overwritten`):
after a farmer counter and a buyer counter, accepting the offer correctly
uses the LATEST counter's price (₹32), not the original offer's price
(₹30) or the farmer's intermediate counter (₹34) - all three rows remain
independently queryable in the database.

## Both parties can counter - role-checked, not assumed

`POST /marketplace/offers/{id}/counter` (farmer) and
`.../counter-as-buyer` (buyer) are separate endpoints with separate
ownership checks - a farmer can only counter an offer against their own
listing; a buyer can only counter their own offer. Neither can impersonate
the other side.

## THE CONCURRENCY GUARANTEE - the most important thing built this phase

`offer_service.accept_offer()`:
1. Reads the offer and determines the final agreed price/quantity (latest
   counter, or the original offer if never countered).
2. Takes a **real PostgreSQL row lock** via
   `harvest_repository.get_listing_for_update()`
   (`SELECT ... FOR UPDATE`) on the `HarvestListing` row - BEFORE
   checking `quantity_available`.
3. Checks the (now-locked, guaranteed-current) quantity. If insufficient,
   raises `409` and the transaction rolls back, releasing the lock.
4. If sufficient, creates the `SaleOrder`, decrements
   `quantity_available`, and commits - releasing the lock.

**This was verified with a real concurrency test, not just code
inspection.** A farmer with a 1000kg listing receives two offers (700kg
and 600kg - together exceeding availability). Both are accepted from two
separate Python threads **simultaneously**
(`test_concurrent_offer_acceptance_never_oversells`). The second
thread's transaction blocks on the row lock until the first commits, then
sees the updated (decremented) quantity and correctly fails. **Result:
exactly one request succeeds (200), exactly one fails (409), and the
final remaining quantity is verified to reflect exactly one sale — never
both, never neither.** This test was run 5 times consecutively during
development specifically to rule out a lucky thread-scheduling race
rather than a real guarantee - all 5 passed identically.

## Price snapshot - no separate table (see docs/SALE_WORKFLOW.md)

The accepted price/quantity/quality are frozen directly onto the
`SaleOrder` row at creation - this IS the price lock (Requirement 33),
never recalculated from the listing or offer afterward.

## Offer expiry

`BuyerOffer.valid_until` exists and is captured from the buyer's request,
but **no code path checks it** - an offer past its `valid_until` can
still be accepted or countered this phase. A disclosed gap; enforcing
this would require either a background job (marking expired offers
`OfferStatus.EXPIRED`) or an on-read check in `accept_offer`/
`create_counter_offer` - neither is built yet.
