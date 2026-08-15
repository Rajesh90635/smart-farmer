# Marketplace Trust

## Buyer trust - verification is the hard gate, reputation is a soft signal

Only `VerificationStatus.VERIFIED` buyers can make offers at all (a hard
404 for anyone else, verified by test) - this is the primary trust
mechanism, not a score. `SaleFeedback` (see below) exists to build a
secondary reputation signal over time, but **no aggregated trust
score/badge is computed or displayed this phase** - Requirement 53/54's
"do not let a buyer with many disputes appear identical to a trusted
buyer" is only partially addressed: verification status is always
visible and enforced, but a numeric dispute-rate or cancellation-rate
figure is not yet computed anywhere. Disclosed gap.

## SaleFeedback - one table, both directions

Rather than separate `FarmerFeedback`/`BuyerFeedback` tables, one
`SaleFeedback` table (distinguished by `given_by_role`) serves both
"farmer rates buyer" and "buyer rates farmer" - avoiding two
near-duplicate tables for a structurally identical shape (rating +
helpful + role-specific JSONB details + free text). Farmer-specific
fields (fair_transaction, payment_on_time, collection_experience) and
buyer-specific fields (quality_feedback, quantity_accuracy,
delivery_experience) both live in `feedback_details` (JSONB) rather than
as separate always-half-null columns.

## DemandSignal - honestly empty, never invented

Per the absolute "do not invent demand data" rule, `demand_signals` has
**zero seed rows** and no code path generates one automatically. The
table exists purely so an admin can enter a signal with a **required,
non-defaulted `source` field** documenting where the claim comes from -
mirroring the exact honesty pattern `ReferencePrice` established in
Prompt 9. No endpoint to create/query `DemandSignal` was built this
phase either - the table is schema-only, ready for that endpoint
whenever a real, documented demand-data source exists to populate it.

## Anti-scam rules - status against the 10 absolute rules

| Rule | Status |
|---|---|
| 1. Verified buyers only for trusted marketplace | ✅ Enforced - hard 404 for unverified |
| 2. No hidden charges | ✅ `gross_value`/`charges`/`net_value` always shown separately (though `charges` is always 0 this phase - no fee model configured, see docs/PAYMENT_AND_SETTLEMENT.md) |
| 3. No fake offers | ✅ Every offer requires a real verified buyer account |
| 4. No fake market prices | ✅ Reused from Prompt 9 - reference prices always sourced |
| 5. No fake buyer verification | ✅ Admin-only, reused from Prompt 8 |
| 6. No fake ratings | ✅ `SaleFeedback` is raw signal only, no computed/inflated score exists to fake |
| 7. No payment claims without confirmation | ✅ Same sandbox-honesty pattern as Prompt 9 - a sale is never marked PAID without a real (sandbox) Payment reaching SUCCESS |
| 8. No unauthorized contact-data exposure | ✅ No contact info (phone/email) is exposed in any buyer-facing or farmer-facing listing/offer/sale response this phase |
| 9. No changing agreed price silently | ✅ `SaleOrder` price fields are frozen at creation, never recalculated |
| 10. Maintain transaction history | ✅ Append-only counter-offers, immutable audit log entries for every lifecycle event |

## Scam Shield for the harvest marketplace - NOT extended this phase (disclosed gap)

Requirement 52 asks to reuse Prompt 9's Scam Shield "for farmers selling"
(checking buyer verification/offer transparency/payment terms) and "for
farmers buying" seeds (already true via seed reuse, see
docs/SEED_MARKETPLACE.md). The SELLING side is only partially covered:
buyer verification is checked (hard gate), but there's no dedicated
"Scam Shield status" endpoint for a harvest offer the way
`GET /dealer-products/{id}/scam-shield` exists for a product listing.
Building one would mean scoring an offer/buyer combination (price vs. some
notion of a fair regional price, buyer history) - deferred since it would
require the demand-signal/reference-price-for-crops infrastructure this
phase doesn't populate.
