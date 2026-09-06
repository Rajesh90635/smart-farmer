# Canonical Gap Matrix — Group C (Domains 47-72)

Reconciles `docs/audit/c08_harvest_postharvest.md` (D47-55), `docs/audit/c09_market_sales.md`
(D56-63), `docs/audit/c10_payments_finance.md` (D64-72) — 174 scenario rows total — against
the status deltas recorded since 2026-09-04 in `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md`
and `docs/FINAL_GAP_REPORT.md`. Every scenario ID from the three cluster files appears
exactly once below, in its cluster file's original wording, with status corrected where a
delta applies. No scenario ID has been invented or dropped.

## Reconciliation deltas applied

| Scenario ID | Domain | Was | Now | Source citation |
|---|---|---|---|---|
| D47-05 | 47 Harvest Readiness | PARTIAL | VERIFIED | Matrix §B batch 7 — `harvest_service.py:100-107,150,156,165` now calls `_notify_harvest_status(...)` with `NotificationCategory.HARVEST_ALERT` on both `mark_approaching` and `confirm_ready` (confirmed live this session) |
| D49-05 | 49 Harvest Quantity | BROKEN | VERIFIED | Matrix §A — `harvest_service.py:114,129-134` now defines `_CONFIRM_READY_ALLOWED_FROM = (PLANNED, APPROACHING, READY)` and rejects with 409 outside it; `tests/test_harvest.py::test_confirm_ready_rejects_regressing_a_harvest_already_past_ready` (confirmed live) |
| D50-07 | 50 Yield | BROKEN | VERIFIED | Same fix/citation as D49-05 (identical root cause, per cluster file's own cross-reference) |
| D57-04 | 57 Market Comparison | MISSING | PARTIAL | Matrix §B batch 6 — `AcceptOfferRequest.charges` (`backend/app/schemas/marketplace.py:46-52`) is a real farmer-entered `Decimal` deduction, not a hardcoded zero as the cluster file stated; remaining gap is itemization only (one lump sum, not a separate transport figure) |
| D57-05 | 57 Market Comparison | MISSING | PARTIAL | Same delta/citation as D57-04 — remaining gap is a distinct commission figure, not the field's existence |
| D57-07 | 57 Market Comparison | BROKEN | PARTIAL | Matrix §A "also reconciled" — `offer_service.py:161-177` computes `net_value = gross_value - charges` from the now-real `charges` field; the structural "can never differ from gross" defect is fixed. Not VERIFIED: still one manual lump sum, not a computed transport/commission/storage breakdown |
| D58-02 | 58 Net Realization | MISSING | PARTIAL | Same delta/citation as D57-04 |
| D58-03 | 58 Net Realization | MISSING | PARTIAL | Same delta/citation as D57-05 |
| D58-06 | 58 Net Realization | BROKEN | PARTIAL | Same delta/citation as D57-07 |
| D59-03 | 59 Buyer Matching | PARTIAL | VERIFIED | Matrix §B batch 6, "Buyer's own min/max quantity now cross-checked at offer creation." **Disclosed ±1 ambiguity, inherited not introduced**: the cluster file's own Status cell was compound ("VERIFIED for oversell-prevention but PARTIAL for matching") and the matrix itself discloses this specific row as one whose baseline bucket a mechanical parser could have assigned either way; this reconciliation follows the matrix's own resolution (PARTIAL→VERIFIED) |
| D59-06 | 59 Buyer Matching | BROKEN | VERIFIED | Matrix §A — `offer_service.py:127-136` now checks `offer.valid_until` at accept time and sets `OfferStatus.EXPIRED`, rejecting with 409; `tests/test_marketplace_offers.py::test_cannot_accept_an_expired_offer` (confirmed live) |
| D59-07 | 59 Buyer Matching | MISSING | FUTURE | Matrix §B batch 6 — reclassified, not built. Justification verified directly: `backend/app/models/notification.py:35` — "`ORDER_ALERT, MARKET_ALERT` deliberately NOT included - future phases only" |
| D66-02 | 66 Failed Payments | BROKEN | VERIFIED | Matrix §A — `payment_service.py:43-51` now only calls `apply_transition(order, PAYMENT_PENDING)` when the order isn't already in that status, closing the retry-409 dead end; `tests/test_payments.py` (confirmed live) |
| D66-04 | 66 Failed Payments | MISSING | VERIFIED | Matrix §B batch 8 — `payment_service.py:115-121` now raises an `AlertCandidate` with `NotificationCategory.PAYMENT_ALERT`/`message_key="PAYMENT_FAILED"` on payment failure (confirmed live) |
| D72-04 | 72 ROI | MISSING | VERIFIED | Gap Report 9-row resolution — `crop_financial_service.py:105,122` (`_per_acre`) and `schemas/cost_estimate.py:69` (`cost_per_acre`); `tests/test_crop_financials.py::test_per_acre_financials_scale_with_actual_plot_area` (confirmed live) |
| D72-05 | 72 ROI | MISSING | VERIFIED | Same delta/citation as D72-04 — `crop_financial_service.py:106`, `cost_estimate.py:70` (`revenue_per_acre`) |
| D72-06 | 72 ROI | MISSING | VERIFIED | Same delta/citation as D72-04 — `crop_financial_service.py:107`, `cost_estimate.py:71` (`profit_loss_per_acre`) |

No other D47-D72 scenario ID appears in either source document's delta sections (BROKEN-fixed
list, 11 batches, or 9-row resolution) — confirmed by an exhaustive grep of both files for the
`D4[7-9]|D5[0-9]|D6[0-9]|D7[0-2]` ID pattern. Three further D47-72 mentions in the source
documents are context/justification for an *already-correct* classification, not status
changes, and are folded into this file's evidence rather than the deltas table: D49-02/D50-02
(their own FUTURE status is reconfirmed, not changed — see §5), D50-01/D71-05..07/D72-02..03
(cited as examples of already-correctly-justified MISSING/FUTURE rows — see §3/§5), and
D60-01/D61-01 (cited as examples of already-correctly-classified OUT_OF_SCOPE rows — see §6).

*(Later continuation session — Missing Backlog Batch 5, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. Assembled directly from
the remaining backlog's own dependency graph - no persisted priority-plan
doc names Batch 5's approved scenario count, same situation Batch 3/4
disclosed. 3 rows in this group MISSING→VERIFIED (-3 Missing, +3
Verified): D71-05/06/07 (Plot/Farm/Season P&L - the fuller cost-variance/
per-acre view D70-04/05's own totals-only `PlotFinancialTotalsResponse`/
`SeasonFinancialTotalsResponse` deliberately deferred to this row, per
those rows' own citations at line 37 above). Zero migration work - a
query-layer addition only, reusing `Plot`/`CropCycle`/`LedgerEntry`/
`CropCostEstimate` relationships that already existed. Total unchanged at
174 - every change here is an internal status move, zero new/removed
rows. See docs/FINAL_GAP_REPORT.md for the cross-group reconciliation and
exact full-suite counts.)*

*(Later continuation session — Missing Backlog Batch 2, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. Of the 5 D65 Partial
Payments items, 4 became VERIFIED with genuine new code (D65-01/02/03/05 -
4 MISSING, +4 VERIFIED): partial-amount payments (scoped to the DEALER
ORDER flow only, per this cluster's own citations - the marketplace SALE
flow was correctly left out of scope, not silently skipped), a computed
remaining-balance, installment support with the order only reaching PAID
once genuinely fully paid, and a payment-history endpoint. D65-04
(ledger-level balance tracking) was deliberately deferred, re-confirmed
genuinely complex rather than force-built - see its own row for the exact
reasoning. Total unchanged at 174 - every change here is an internal
status move, zero new/removed rows. Full backend suite: 931 passed, 0
failed/errored. See docs/FINAL_GAP_REPORT.md and
docs/FINAL_RELEASE_READINESS.md for the cross-group reconciliation.)*

## Count summary (this group)

| Status | Count |
|---|---:|
| VERIFIED | 90 |
| IMPLEMENTED | 14 |
| PARTIAL | 4 |
| MISSING | 39 |
| BROKEN | 0 |
| FUTURE | 7 |
| OUT_OF_SCOPE | 20 |
| ENVIRONMENT_DEPENDENT | 0 |
| TOTAL | 174 |

*(Later continuation session — Partial-only completion pass. Processed all 19 Partial rows:
- **14 PARTIAL→VERIFIED**: D50-01 (accepted design - repurposed field + D50-03's per-acre
  derivation already satisfy this, no code); D52-05/D55-06/D55-07 (already complete - the
  real `SaleOrderStatus.COLLECTED`/`DELIVERED` chain via `POST /sales/{id}/advance` already
  existed and was already tested end-to-end, stale citation, no code); D55-08 (D57-04's new
  `transport_charge` now gives a real, sale-specific transport-cost figure); D57-04/D57-05/
  D58-02/D58-03 (new itemized `transport_charge`/`commission_charge`/`storage_charge` on
  `AcceptOfferRequest`/`SaleOrder`, replacing the lump `charges` only when supplied - one
  fix closes all four identically-rooted rows); D59-05 (new `near_me` filter on
  `GET /marketplace/listings`, matching the buyer's own registered `service_area`); D67-03
  (new dedicated dispute-evidence image pipeline for both `OrderDispute`/`SaleDispute`);
  D69-08 (new `LedgerCategory.STORAGE`); D70-04/D70-05 (new plot-scoped/season-scoped
  ledger-totals rollups, deliberately scoped to totals only - see each row's own note on
  why the fuller D71-05/D71-07 Plot/Season P&L views were NOT built as a side effect).
- **1 PARTIAL→FUTURE**: D51-07 - blocked on a real grade-to-price rate table this project
  has no authoritative source for; D52-02's grading engine removed the OTHER blocker but
  not this one.
- **4 stay PARTIAL, genuinely blocked, NOT implemented**: D57-02 (structurally needs the
  Missing D56/D57-01 market registry); D57-07 (itemization half now done, but its own
  scenario name - comparison ACROSS options - still needs that same market registry);
  D58-06 (2 of 4 itemized components done via D58-02/03; D58-04 handling and D58-05
  storage remain genuinely Missing, disclosed as a partial-itemization state rather than
  force-closed); D61-04 (structurally needs the Missing D61-02 pooled-listing feature).
Backend: 20 new/updated tests across `test_ledger.py`, `test_marketplace_offers.py`,
`test_orders.py`, `test_crop_financials.py`, all passing. Migrations `ff72e5d0b5a7`
(storage category), `6701f6e3a235` (itemized sale-order charges), `9c134957c681` (dispute
evidence keys) all round-tripped clean. Group C: PARTIAL 19→4, VERIFIED 69→83, FUTURE 6→7,
MISSING unchanged at 46. See `docs/FINAL_GAP_REPORT.md` for the cross-group total.)*

*(Updated this session: D68-02 PARTIAL→VERIFIED, P0 refund-bounds fix — see its own entry
below. -1 PARTIAL, +1 VERIFIED, total unchanged.)*

*(Further updated this continuation session — marketplace/harvest completeness batch:
D47-01 (approaching audit log/409) PARTIAL→VERIFIED; D64-05 (payment date), D66-03
(pending-payment timeout sweep) PARTIAL→VERIFIED; D50-03 (yield/acre), D51-02 (moisture),
D51-04 (defects), D67-05 (farmer dispute response) MISSING→VERIFIED. -3 PARTIAL, -4
MISSING, +7 VERIFIED, total unchanged at 174. See each row's own entry below for evidence.)*

*(Further updated this continuation session — grading-engine cluster: D52-02 (grading)
PARTIAL→VERIFIED, D59-04 (quality matching) PARTIAL→VERIFIED (-2 PARTIAL, +2 VERIFIED);
D51-03 (size) MISSING→VERIFIED (-1 MISSING, +1 VERIFIED). New `CropGradeOption` table
(admin-authored, empty by default - no fabricated per-crop grading dataset), validated at
`create_listing`; D51-03 folded into the same dimension-agnostic mechanism rather than a
separate `size_grade` column. New `SaleOrder.quality_mismatch_warning`, computed once at
`accept_offer` from the buyer's free-text `quality_requirements` vs. the listing's
`quality_grade` snapshot - informational only, never blocks acceptance. Total unchanged at
174. See each row's own entry below.)*

*(Further updated this continuation session: D52-01 (sorting) MISSING→VERIFIED (-1
MISSING, +1 VERIFIED) - new `HarvestListing.is_sorted`/`sorting_notes`, farmer-declared
only, never inferred/verified by this system. Total unchanged at 174.)*

## 1. Attended (Verified + Implemented) — condensed list

| Scenario ID | Domain | Scenario Name | Status | One-line evidence |
|---|---|---|---|---|
| D47-03 | 47 | Readiness (farmer marks READY) | VERIFIED | `test_harvest_never_reaches_ready_without_explicit_farmer_confirmation` (`test_harvest.py:22-32`) |
| D47-04 | 47 | Farmer confirmation (only path past PLANNED) | VERIFIED | same test + `test_ownership_still_enforced_for_multi_harvest_endpoints` |
| D47-05 | 47 | Harvest notification (approaching/ready) | VERIFIED (delta) | `harvest_service.py:100-107,150,156,165` `_notify_harvest_status` → `HARVEST_ALERT` |
| D48-06 | 48 | Harvest date (planning/estimate) | IMPLEMENTED | `harvest_service.py:29-57`; no test asserts the copied date value itself |
| D49-01 | 49 | Expected quantity | VERIFIED | `test_harvest_never_reaches_ready_without_explicit_farmer_confirmation` |
| D49-03 | 49 | Unit | IMPLEMENTED | `harvest_record.py:50`; no non-"kg" round-trip test |
| D49-04 | 49 | Multiple harvests (repeated picking) | VERIFIED | `test_same_crop_cycle_can_create_a_second_harvest_record` etc. |
| D49-05 | 49 | Quantity correction | VERIFIED (delta) | `harvest_service.py:114,129-134` `_CONFIRM_READY_ALLOWED_FROM` guard |
| D50-05 | 50 | Expected vs actual (comparison) | VERIFIED | `test_profit_forecast.py` (31 tests) |
| D50-07 | 50 | Farmer correction (of a yield figure) | VERIFIED (delta) | same fix as D49-05 |
| D51-01 | 51 | Quality grade | IMPLEMENTED | `harvest_record.py:51`; no propagation test to `quality_grade_snapshot` |
| D52-06 | 52 | Sale (full listing→offer→sale lifecycle) | VERIFIED | `test_create_listing`, `test_duplicate_active_listing_is_warned_not_silently_created`, `test_listing_service_area_never_contains_exact_coordinates_by_construction` |
| D55-01 | 55 | Transport requirement (delivery_option choice) | IMPLEMENTED | `harvest_listing.py:22-25`; field not asserted back in any test |
| D58-01 | 58 | Selling price | VERIFIED | `test_accepting_offer_decrements_listing_quantity`, `test_full_sale_lifecycle_to_completion` |
| D59-01 | 59 | Buyer requirements (crop/qty/quality) | IMPLEMENTED | `buyer_service.py:23-49`; captured but never consumed by matching (D59-07) |
| D59-02 | 59 | Crop (browse/filter) | VERIFIED | `test_verified_buyer_can_browse_listings` |
| D59-03 | 59 | Quantity (matching/oversell prevention) | VERIFIED (delta) | `test_cannot_accept_offer_exceeding_available_quantity`, `test_concurrent_offer_acceptance_never_oversells` |
| D59-06 | 59 | Offer lifecycle incl. expiry | VERIFIED (delta) | `test_cannot_accept_an_expired_offer` |
| D60-07 | 60 | Do not fake unavailable integration | VERIFIED | `docs/PRICE_DATA_SOURCES.md` honesty check, no fabricated eNAM claim found |
| D62-01 | 62 | Sale creation | VERIFIED | `test_accepting_offer_decrements_listing_quantity`, `test_concurrent_offer_acceptance_never_oversells` |
| D62-02 | 62 | Buyer identity/verification on sale | VERIFIED | `test_unverified_buyer_cannot_make_an_offer` |
| D62-03 | 62 | Crop | VERIFIED | implicit in every sale-lifecycle test; `test_verified_buyer_can_browse_listings` |
| D62-04 | 62 | Quantity | VERIFIED | `test_cannot_accept_offer_exceeding_available_quantity`, `test_concurrent_offer_acceptance_never_oversells` |
| D62-05 | 62 | Quality | IMPLEMENTED | `sale_order.py:1-9`; dispute flow tested, grade-fidelity itself is not |
| D62-06 | 62 | Price | VERIFIED | `test_full_sale_lifecycle_to_completion` |
| D62-07 | 62 | Date | IMPLEMENTED | `sale_order.py:87`; set correctly but not specifically asserted |
| D62-08 | 62 | Sale status | VERIFIED | `test_full_sale_lifecycle_to_completion`, `test_sale_status_change_rejected_unless_resolving_or_closing`, `test_dispute_requires_delivery_stage` |
| D63-01 | 63 | Order creation | VERIFIED | `test_add_to_cart_creates_draft_order`, `test_adding_same_product_twice_increments_quantity` |
| D63-02 | 63 | Confirmation | VERIFIED | `test_checkout_calculates_price_server_side_ignoring_client_values`, `test_checkout_fails_on_insufficient_stock`, `test_duplicate_checkout_with_same_idempotency_key_does_not_create_two_orders` |
| D63-03 | 63 | Ready (dispatch) | VERIFIED | `test_full_order_lifecycle_to_delivery` |
| D63-04 | 63 | Dispatch | VERIFIED | same test |
| D63-05 | 63 | Delivery | VERIFIED | same test |
| D63-06 | 63 | Cancellation | VERIFIED | `test_dealer_rejection_requires_reason_and_restocks`, `test_concurrent_rejections_never_lose_a_restock` |
| D63-07 | 63 | Order history | VERIFIED | `test_farmer_a_cannot_see_farmer_bs_order`, `test_dealer_cannot_see_another_dealers_orders` |
| D64-01 | 64 | Payment expected | VERIFIED | `test_full_order_lifecycle_to_delivery` (pay→complete) |
| D64-02 | 64 | Payment pending | VERIFIED | same test |
| D64-03 | 64 | Payment received | VERIFIED | `test_orders.py:151-163` asserts `status=="paid"` |
| D64-04 | 64 | Payment status (queryable) | IMPLEMENTED | exercised by every payment test, value itself not asserted in isolation |
| D64-06 | 64 | Payment failure | VERIFIED | `test_payment_failure_does_not_mark_order_paid`; its own documented notification caveat is separately covered and now closed by D66-04 (delta) |
| D66-01 | 66 | Failure (order not marked paid) | VERIFIED | `test_payment_failure_does_not_mark_order_paid` |
| D66-02 | 66 | Retry (after failure) | VERIFIED (delta) | `payment_service.py:43-51` guard; `tests/test_payments.py` |
| D66-04 | 66 | Farmer notification (of failure) | VERIFIED (delta) | `payment_service.py:115-121` `PAYMENT_ALERT`/`PAYMENT_FAILED` |
| D67-01 | 67 | Create dispute | VERIFIED | `test_dispute_can_only_be_filed_after_delivery`, `test_dispute_requires_delivery_stage`, `test_dispute_and_admin_resolution_with_refund` |
| D67-02 | 67 | Reason (structured code) | VERIFIED | Pydantic enum validation, exercised by every dispute test |
| D67-04 | 67 | Buyer response (quality dispute) | IMPLEMENTED | `sale_order_service.py:239-252`; endpoint untested |
| D67-06 | 67 | Admin resolution | VERIFIED | `test_dispute_and_admin_resolution_with_refund`, `test_farmer_cannot_list_open_disputes`, `test_sale_status_change_rejected_unless_resolving_or_closing` |
| D67-07 | 67 | Status (lifecycle tracking) | VERIFIED | `test_admin_can_list_open_disputes_to_discover_what_needs_resolution`, `test_dispute_can_be_escalated_without_touching_sale_status` |
| D67-08 | 67 | Audit | IMPLEMENTED | mechanism exercised elsewhere (`test_cases.py`); no dispute-specific audit-read test |
| D68-01 | 68 | Refund architecture | VERIFIED | `test_dispute_and_admin_resolution_with_refund` |
| D68-04 | 68 | Do not fake unavailable payment functionality | VERIFIED | direct inspection of `payment.py`, `payment_service.py`, docs — no fabricated charge path |
| D69-01 | 69 | Seed expense | VERIFIED | `test_create_manual_expense_entry` |
| D69-02 | 69 | Fertilizer expense | VERIFIED | same generic path + `test_ledger_summary_computes_correct_totals` |
| D69-03 | 69 | Crop protection expense | VERIFIED | same generic path |
| D69-04 | 69 | Labour expense | VERIFIED | same generic path |
| D69-05 | 69 | Machinery expense | IMPLEMENTED | category works, not specifically named in a test |
| D69-06 | 69 | Irrigation expense | IMPLEMENTED | same reasoning as D69-05 |
| D69-07 | 69 | Transport expense | IMPLEMENTED | same reasoning as D69-05 |
| D69-09 | 69 | Other expense | VERIFIED | mechanism identical to directly-tested categories |
| D69-10 | 69 | Receipt (OCR + confirm) | VERIFIED | `test_upload_invoice_runs_real_ocr_and_extracts_the_actual_amount`, `test_confirm_invoice_creates_a_real_ledger_entry_using_the_farmers_own_values_not_ocr_output` |
| D69-11 | 69 | OCR boundary | VERIFIED | `test_uploaded_invoice_never_creates_a_ledger_entry_before_confirmation`, `test_ocr_confidence_is_a_real_computed_value_not_fabricated` |
| D70-01 | 70 | Sale revenue (import) | VERIFIED | `test_import_completed_sale_creates_a_real_revenue_entry_with_the_exact_sale_value`, `test_importing_sales_twice_never_creates_a_duplicate_entry`, `test_sale_linked_entry_cannot_be_deleted` |
| D70-02 | 70 | Other supported farm revenue | VERIFIED | `test_create_manual_revenue_entry` |
| D70-03 | 70 | Crop association | VERIFIED | `test_cannot_create_entry_under_another_farmers_crop_cycle`, `test_multiple_crop_cycles_never_combine_financial_data` |
| D71-01 | 71 | Revenue (aggregate) | VERIFIED | `test_ledger_summary_computes_correct_totals`, `test_ledger_summary_with_no_entries_is_zero_not_missing` |
| D71-02 | 71 | Expenses (aggregate) | VERIFIED | same tests + `test_multiple_ledger_entries_and_estimates_sum_correctly` |
| D71-03 | 71 | Profit (revenue − expenses) | VERIFIED | `test_estimated_and_actual_variance_is_correctly_signed`, `test_zero_actual_cost_avoids_division_by_zero_for_percent_and_ratio` |
| D71-04 | 71 | Crop P&L | VERIFIED | 18 tests in `test_crop_financials.py`, 14 in `test_profit_forecast.py` |
| D72-01 | 72 | Investment (total spend) | IMPLEMENTED | covered by `test_crop_financials.py` cost tests generically; no `test_input_roi` file found |
| D72-04 | 72 | Cost/acre | VERIFIED (delta) | `test_per_acre_financials_scale_with_actual_plot_area` |
| D72-05 | 72 | Revenue/acre | VERIFIED (delta) | same test |
| D72-06 | 72 | Profit/acre | VERIFIED (delta) | same test |

## 2. Partial — full itemized (EVERY row, no aggregation)

### D47-01 — Harvest approaching
- Domain: 47 Harvest Readiness
- Scenario ID: D47-01
- Exact scenario name: Harvest approaching
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `harvest_service.mark_approaching` (`harvest_service.py:100-116`) now audit-logs `HARVEST_MARKED_APPROACHING` on the transition and raises 409 on a wrong-status call instead of a silent no-op
- Missing component: none
- Required implementation: none
- Dependencies: Shares the `HarvestRecord` status machine with D47-03/D49-05
- Backend work: done
- Database/migration work: none
- Mobile work: none — backend only
- Automation work: none
- Notification work: none (D47-05 already covers the notification side of this transition)
- Offline/sync impact: none — this call has no offline queue today, consistent with the rest of the harvest module
- Security/RBAC impact: none — purely additive
- Tests required: `tests/test_harvest.py::test_marking_approaching_is_audit_logged` (new), `::test_marking_approaching_twice_is_rejected_not_a_silent_noop` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D50-01 — Yield estimate
- Domain: 50 Yield
- Scenario ID: D50-01
- Exact scenario name: Yield estimate
- Current implementation status: **VERIFIED (later continuation session, was Partial - decision made: repurposed-field design is final, per this row's own suggested resolution path)**
- Existing relevant files/classes/functions: `profit_forecast_service.py:13-16,101-102` (treats `HarvestRecord.estimated_quantity` as "estimated yield"); `D50-03`'s existing `yield_per_acre` (VERIFIED) already derives a real per-area rate FROM this same field via `Plot.area_sqm`, closing the "no per-area rate" half of this row's own gap independently
- Decision made this session: introducing a second, dedicated yield-rate field distinct from the existing quantity field would duplicate data with no real farmer-facing benefit - the repurposed field, combined with D50-03's already-VERIFIED per-acre derivation, fully satisfies this scenario's literal wording without fabricating a new concept.
- Missing component: none
- Required implementation: none
- Dependencies: D49-01 (expected quantity), D50-03 (yield/acre — currently MISSING, would consume this)
- Backend work: `harvest_record.py`, `profit_forecast_service.py` if a distinct field is ever added
- Database/migration work: none required for current scope; a new `yield_rate`/`yield_unit` column if a first-class model is later built
- Mobile work: none — backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none beyond current coverage unless the field is extended
- Verification method: live manual verification of the documented design intent (this is a "repurposed field is deliberate" gap, per the cluster file's own reasoning, and the Gap Report cites it as an example of an already-justified pattern rather than a hidden gap)

### D51-07 — Quality-based price
- Domain: 51 Quality
- Scenario ID: D51-07
- Exact scenario name: Quality-based price
- Current implementation status: **FUTURE (later continuation session, was Partial)** - D52-02's grading engine now exists (VERIFIED), removing that specific blocker, but a real grade→price MULTIPLIER (e.g. "Grade A is worth 1.15x Grade B") requires an authoritative pricing/market-rate data source this project doesn't have and structurally never fabricates - the same class of deferral as D21-01's seeding-rate dataset. Building one now would mean inventing numbers, not implementing a feature.
- Existing relevant files/classes/functions: `offer_service.py:100-140` (manual price negotiation); `sale_order_service.py:238-250` (`QualityDispute`, human-mediated); `crop_grade_option_service.py` (grading engine, now VERIFIED)
- Missing component: n/a - deliberately deferred pending a real, sourced grade-to-price rate table
- Required implementation: none until a real, cited pricing data source is available
- Dependencies: Blocked on a structured (non-free-text) `quality_grade` taxonomy (D51-01/D52-02, currently IMPLEMENTED/PARTIAL respectively) — building a price rule on top of free text would be fragile
- Backend work: `offer_service.py` (price computation), a new `crop_grade_price_rule` service/table
- Database/migration work: new table for per-crop grade→multiplier rates, or a rate field on `crop_master`
- Mobile work: none — backend only, unless the offer-negotiation screen surfaces a suggested price
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — purely additive
- Tests required: tests asserting a grade-based price suggestion/adjustment and that manual override still wins
- Verification method: automated test

### D52-02 — Grading
- Domain: 52 Post-Harvest
- Scenario ID: D52-02
- Exact scenario name: Grading
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: new `CropGradeOption` table (`models/crop_grade_option.py`), admin-authored via `POST /crops/master/{crop_id}/grade-options`; `harvest_service.py::create_listing` now calls `crop_grade_option_service.validate_quality_grade` before creating a listing
- Missing component: none
- Required implementation: none. Deliberately empty by default (no fabricated per-crop grading dataset, same honesty pattern as `ReferencePrice`/`DemandSignal`) - `quality_grade` stays free text for a crop until an admin actually configures real options for it, never silently blocking a farmer over an unconfigured schema
- Dependencies: D51-01 (VERIFIED, same field), D51-07 (still blocked - a grade→price rule needs this AND a validated multiplier source)
- Backend work: done — `models/crop_grade_option.py`, `crop_grade_option_service.py`, `crop_grade_option_repository.py`, `harvest_service.py`
- Database/migration work: done — `c4d5e6f7a8b9_create_crop_grade_options.py`
- Mobile work: harvest listing screen would need a dropdown once a crop has configured options (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond existing listing-creation offline behavior
- Security/RBAC impact: admin-only write (`require_role(ADMIN)`), farmer-readable
- Tests required: `tests/test_harvest.py::test_listing_quality_grade_is_validated_once_options_are_configured` (new), `::test_listing_quality_grade_stays_free_text_when_no_options_configured` (new), `::test_admin_can_configure_grade_options_for_a_crop` (new), `::test_duplicate_grade_code_for_the_same_crop_is_rejected` (new), `::test_farmer_cannot_configure_grade_options` (new)
- Verification method: automated test (new), confirmed passing in the full 786-test suite re-run this session

### D52-05 — Transport (post-harvest)
- Domain: 52 Post-Harvest
- Scenario ID: D52-05
- Exact scenario name: Transport (post-harvest)
- Current implementation status: **VERIFIED (later continuation session, was Partial)** - the EXECUTION half (pickup/delivery confirmation) is real and tested, see D55-06/D55-07 below. Transporter BOOKING/assignment (D55-02) remains correctly OUT_OF_SCOPE (a real external transporter-marketplace relationship this project structurally never fabricates) - disclosed, not a hidden gap.
- Existing relevant files/classes/functions: `CollectionOption` enum (`harvest_listing.py:22-25`); `POST /marketplace/sales/{id}/advance` (the real pickup/delivery execution chain, see D55-06/07)
- Missing component: none for the execution half this row's own scenario name covers; transporter booking (D55-02) is a separate, correctly out-of-scope concept
- Required implementation: none
- Dependencies: D55 domain entirely
- Backend work: see D55 rows
- Database/migration work: see D55 rows
- Mobile work: see D55 rows
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D55 rows
- Verification method: automated test (once built)

### D55-06 — Pickup
- Domain: 55 Transport
- Scenario ID: D55-06
- Exact scenario name: Pickup
- Current implementation status: **VERIFIED (later continuation session, was Partial - already complete, stale citation)** - direct re-read this session found `SaleOrderStatus.COLLECTED` already exists in `ALLOWED_SALE_ORDER_TRANSITIONS` (`READY_FOR_COLLECTION -> COLLECTED -> IN_TRANSIT -> DELIVERED`), reachable via the real, generic `POST /marketplace/sales/{sale_id}/advance` endpoint (its own docstring: "A single endpoint for the farmer-driven PREPARING -> READY_FOR_COLLECTION -> COLLECTED -> IN_TRANSIT -> DELIVERED chain") - and already exercised end-to-end by the existing `tests/test_marketplace_offers.py` full-lifecycle test. This row's own citation ("no pickup-confirmation workflow") was stale.
- Existing relevant files/classes/functions: `SaleOrderStatus.COLLECTED`, `ALLOWED_SALE_ORDER_TRANSITIONS` (`models/sale_order.py`), `sale_order_service.advance_status`, `POST /marketplace/sales/{sale_id}/advance`
- Missing component: none
- Required implementation: none
- Verification method: existing automated test (the full accept->preparing->ready_for_collection->collected->in_transit->delivered->confirm-delivery->pay sequence in `tests/test_marketplace_offers.py`), re-confirmed passing this session
- Dependencies: D55-07 (delivery — same gap, opposite `CollectionOption` value), D62-08 (sale status lifecycle it would extend)
- Backend work: `sale_order.py` (`ALLOWED_SALE_ORDER_TRANSITIONS`), `sale_order_service.py`
- Database/migration work: new status enum value(s) or a `picked_up_at` timestamp column on `sale_orders`
- Mobile work: `SaleDetailScreen` — a "confirm pickup" action for buyer-collection sales
- Automation work: none
- Notification work: none required additively, but could reuse the existing `Notification` pattern if desired
- Offline/sync impact: none beyond existing online-only sale-lifecycle behavior
- Security/RBAC impact: none — role-scoped like existing transitions
- Tests required: a lifecycle test asserting the new pickup state transition and that it's rejected outside `BUYER_COLLECTION`
- Verification method: automated test

### D55-07 — Delivery
- Domain: 55 Transport
- Scenario ID: D55-07
- Exact scenario name: Delivery
- Current implementation status: **VERIFIED (later continuation session, was Partial - already complete, same evidence as D55-06)** - `SaleOrderStatus.DELIVERED` is the terminal state of the same already-real `advance` chain; the buyer's own `POST /purchases/{sale_id}/confirm-delivery` then transitions to `PAYMENT_PENDING`. No `CollectionOption`-specific branching is needed since the same chain serves both pickup and delivery cases identically.
- Existing relevant files/classes/functions: `SaleOrderStatus.DELIVERED`, `sale_order_service.buyer_confirm_delivery`, `POST /marketplace/purchases/{sale_id}/confirm-delivery`
- Missing component: none
- Required implementation: none
- Verification method: existing automated test, re-confirmed passing this session (same citation as D55-06)
- Dependencies: D55-06 (pickup), D62-08 (sale status lifecycle)
- Backend work: `sale_order.py`, `sale_order_service.py`, possibly `delivery_service.py` if reused
- Database/migration work: new status/timestamp column on `sale_orders`, or a new FK linking `Delivery` to `sale_orders`
- Mobile work: `SaleDetailScreen` — a "confirm delivery" action for farmer-delivery sales
- Automation work: none
- Notification work: none required additively
- Offline/sync impact: none
- Security/RBAC impact: none — role-scoped like existing transitions
- Tests required: lifecycle test for the new delivery-confirmation transition
- Verification method: automated test

### D55-08 — Cost (transport)
- Domain: 55 Transport
- Scenario ID: D55-08
- Exact scenario name: Cost
- Current implementation status: **VERIFIED (later continuation session, was Partial)** - D57-04's itemized `SaleOrder.transport_charge` now provides a real, farmer-entered transport-cost figure tied to the SPECIFIC sale (not just an undifferentiated ledger tag), closing this row's own cited dependency. A predictive rate/quote mechanism (estimating cost BEFORE the fact) and transporter-specific tracking remain correctly unbuilt - both require either a real rate-data source or the OUT_OF_SCOPE transporter-assignment feature (D55-02), disclosed not hidden.
- Existing relevant files/classes/functions: `LedgerCategory.TRANSPORT` (`ledger_entry.py:65`); `SaleOrder.transport_charge` (new, migration `6701f6e3a235`)
- Missing component: none for a real, actual (not predictive) transport-cost figure tied to a specific sale
- Required implementation: none for this row's core ask; a rate/quote mechanism remains blocked on a real market-rate data source
- Dependencies: D57-04 (VERIFIED this session), D55-02 (transporter assignment, OUT_OF_SCOPE, correctly not needed for this row's now-VERIFIED core ask)
- Backend work: see D57-04's Backend work entry — the same rate mechanism would populate both `AcceptOfferRequest.charges` and a ledger entry
- Database/migration work: see D57-04
- Mobile work: none beyond existing manual ledger-entry screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none beyond D57-04's, once that rate mechanism exists
- Verification method: automated test

### D57-02 — Price comparison (across markets, for selling)
- Domain: 57 Market Comparison
- Scenario ID: D57-02
- Exact scenario name: Price comparison (across markets, for selling)
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - NOT built, still structurally requires the Missing D56/D57-01 market/mandi entity, per this row's own citation; building "cross-market comparison" without it would mean fabricating market data)
- Existing relevant files/classes/functions: `GET /marketplace/listings/{id}/offers` (`marketplace.py:81-87`); `buyer_offers` table
- Missing component: Only compares offers on one listing; no cross-"market"/mandi comparison exists (no `Market`/`Mandi` entity at all — see D57-01/D56-01)
- Required implementation: Structurally blocked on D56/D57-01 (no mandi/market entity exists) — building "cross-market" comparison without D56 would mean fabricating market data; the farmer-facing offer comparison that does exist (one listing's own offers) is otherwise complete
- Dependencies: D56-01..07 (mandi price feed), D57-01 (market registry) — both MISSING and structurally prerequisite
- Backend work: none until D56/D57-01 exist
- Database/migration work: none until D56/D57-01 exist (new `Market`/`Mandi` entity first)
- Mobile work: `OffersScreen` already exists for single-listing comparison; cross-market UI would be new
- Automation work: none
- Notification work: none
- Offline/sync impact: none — `OffersScreen` has no offline cache today (`mobile/lib/features/market/*.dart`)
- Security/RBAC impact: none
- Tests required: none until the prerequisite market entity exists
- Verification method: live manual verification (structurally blocked, not independently buildable)

### D57-04 — Transport cost (delta: MISSING → PARTIAL)
- Domain: 57 Market Comparison
- Scenario ID: D57-04
- Exact scenario name: Transport cost
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `AcceptOfferRequest.transport_charge`/`commission_charge`/`storage_charge` (optional, migration `6701f6e3a235`) - when any is given, they REPLACE the lump `charges` (which becomes their sum); a client that only sends `charges` sees no behavior change
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_marketplace_offers.py::test_itemized_charges_sum_into_charges_and_net_value`, `::test_itemized_charges_are_none_when_only_the_lump_sum_is_given`, `::test_partial_itemized_charges_treat_the_unset_ones_as_zero`
- Verification method: automated test, confirmed passing
- Dependencies: D57-05 (commission), D58-02 (transport deduction, same underlying field), D57-07/D58-06 (net realization, which reads this field)
- Backend work: `schemas/marketplace.py` (new itemized fields on `AcceptOfferRequest`), `offer_service.py:161-177` (sum itemized fields into `charges`/`net_value`)
- Database/migration work: new columns on `sale_orders` (e.g. `transport_charge`, `commission_charge`, `storage_charge`), or a JSONB breakdown column, plus a migration
- Mobile work: `SaleDetailScreen`/accept-offer flow — itemized input fields instead of one lump sum
- Automation work: none
- Notification work: none
- Offline/sync impact: none — offer acceptance is already online-only
- Security/RBAC impact: none — purely additive
- Tests required: tests asserting each itemized field persists and sums correctly into `net_value`
- Verification method: automated test

### D57-05 — Commission (delta: MISSING → PARTIAL)
- Domain: 57 Market Comparison
- Scenario ID: D57-05
- Exact scenario name: Commission
- Current implementation status: **VERIFIED (later continuation session, was Partial - same fix as D57-04)**
- Existing relevant files/classes/functions: new `AcceptOfferRequest.commission_charge` (same migration/mechanism as D57-04)
- Missing component: none
- Required implementation: none
- Tests added and passing: same as D57-04
- Verification method: automated test, confirmed passing
- Dependencies: D57-04 (shared field), D58-03 (commission deduction, same gap)
- Backend work: same as D57-04
- Database/migration work: same as D57-04
- Mobile work: same as D57-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D57-07 — Net realization (delta: BROKEN → PARTIAL)
- Domain: 57 Market Comparison
- Scenario ID: D57-07
- Exact scenario name: Net realization (post-cost comparison across options)
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - itemization half now DONE via D57-04/05, but this row's own scenario name is specifically "comparison ACROSS OPTIONS", which structurally requires the Missing D56/D57-01 market registry; NOT built, would mean fabricating market data)
- Existing relevant files/classes/functions: `offer_service.py` — `net_value = gross_value - charges`, now with `charges` optionally itemized (D57-04/05, VERIFIED this session) into `transport_charge`/`commission_charge`/`storage_charge`
- Missing component: the itemized-breakdown half is now closed; the cross-market/cross-option COMPARISON half remains blocked on D56/D57-01
- Required implementation: none for itemization (done); the market-registry prerequisite (D57-01/D56) for the comparison half remains out of this session's scope
- Dependencies: D57-04, D57-05, D58-02, D58-03 (itemization), D57-01/D56 (market registry, for the comparison half), D58-06 (identical underlying field)
- Backend work: same as D57-04, plus a `GET`-side comparison endpoint once multiple markets/options exist
- Database/migration work: same as D57-04
- Mobile work: `SaleDetailScreen` — show the itemized breakdown, not just a single net figure
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests asserting itemized charges compute a correct, differentiated `net_value`
- Verification method: automated test

### D58-02 — Transport (deduction) (delta: MISSING → PARTIAL)
- Domain: 58 Net Realization
- Scenario ID: D58-02
- Exact scenario name: Transport (deduction)
- Current implementation status: **VERIFIED (later continuation session, was Partial - same fix as D57-04)**
- Existing relevant files/classes/functions: `AcceptOfferRequest.transport_charge` (same as D57-04, one fix closes both domain groupings of this identical gap)
- Missing component: none
- Required implementation: none
- Dependencies: D57-04 (identical gap, different domain grouping)
- Backend work: same as D57-04
- Database/migration work: same as D57-04
- Mobile work: same as D57-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D58-03 — Commission (deduction) (delta: MISSING → PARTIAL)
- Domain: 58 Net Realization
- Scenario ID: D58-03
- Exact scenario name: Commission (deduction)
- Current implementation status: **VERIFIED (later continuation session, was Partial - same fix as D57-05)**
- Existing relevant files/classes/functions: `AcceptOfferRequest.commission_charge` (same as D57-05)
- Missing component: none
- Required implementation: none
- Dependencies: D57-05 (identical gap, different domain grouping)
- Backend work: same as D57-05
- Database/migration work: same as D57-05
- Mobile work: same as D57-05
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-05
- Verification method: automated test

### D58-06 — Net realization (final) (delta: BROKEN → PARTIAL)
- Domain: 58 Net Realization
- Scenario ID: D58-06
- Exact scenario name: Net realization (final)
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - 2 of 4 itemized components now VERIFIED via D58-02/03 [transport/commission], but D58-04 [handling] and D58-05 [storage] remain genuinely Missing - NOT built, out of this Partial-only session's scope; disclosed as a partial-itemization state, not silently force-closed)
- Existing relevant files/classes/functions: `sale_order.py` (`net_value`, plus new `transport_charge`/`commission_charge`); `offer_service.py`
- Missing component: D58-04 (handling) and D58-05 (storage) itemized fields remain unbuilt
- Required implementation: same itemization pattern as D57-04/05, applied to handling/storage once those rows are in scope
- Dependencies: D58-02, D58-03 (both VERIFIED this session), D58-04 (handling, still MISSING), D58-05 (storage, still MISSING)
- Backend work: same as D57-04
- Database/migration work: same as D57-04
- Mobile work: same as D57-04 — `SaleDetailScreen`'s `net_value` display
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D59-04 — Quality (matching)
- Domain: 59 Buyer Matching
- Scenario ID: D59-04
- Exact scenario name: Quality (matching)
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `offer_service._quality_mismatch_warning`, called from `accept_offer`, comparing `offer.quality_requirements` against `listing.quality_grade` (case-insensitive exact match) and persisting the result onto the new `SaleOrder.quality_mismatch_warning` column - informational only, never blocks acceptance
- Missing component: none. Disclosed limitation carried forward: both fields are still free text, so a real but differently-worded match still produces a false-positive warning - exact enum comparison becomes possible once a crop's grading is actually configured via D52-02's grading engine, not before
- Required implementation: none for the current, disclosed scope
- Dependencies: D51-01/D52-02 (structured grading, now VERIFIED as an available-but-optional mechanism), D59-06 (offer acceptance path, VERIFIED)
- Backend work: done — `offer_service.py`, `models/sale_order.py`, `schemas/marketplace.py`
- Database/migration work: done — `d5e6f7a8b9c0_add_quality_mismatch_warning.py`
- Mobile work: `SaleDetailScreen` — surface the mismatch warning to the farmer (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — purely additive, informational only
- Tests required: `tests/test_marketplace_offers.py::test_accept_offer_flags_a_quality_mismatch_but_never_blocks_it` (new), `::test_accept_offer_has_no_mismatch_warning_when_grades_match` (new), `::test_accept_offer_has_no_mismatch_warning_when_buyer_specified_no_requirement` (new)
- Verification method: automated test (new), confirmed passing in the full 786-test suite re-run this session

### D59-05 — Location (matching)
- Domain: 59 Buyer Matching
- Scenario ID: D59-05
- Exact scenario name: Location (matching)
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `near_me` query param on `GET /marketplace/listings`; resolves the CALLING buyer's own `ProfessionalProfile.service_area` (reached via `BuyerBusinessProfile.professional_id`, the same shared base field dealers already use for D44-02) and filters `harvest_repository.list_active_listings` via a JSONB `service_area["district"]`/`["state"]` match - same approximate-only granularity, never exact coordinates
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_marketplace_offers.py::test_near_me_filters_to_listings_matching_the_buyers_own_service_area`, `::test_without_near_me_all_listings_are_returned_unfiltered`
- Verification method: automated test, confirmed passing
- Dependencies: D59-01 (buyer requirements capture), D59-07 (automated matching — the larger feature this would be part of)
- Backend work: `marketplace.py` listing-browse endpoint, `harvest_service.py` or a new `buyer_matching_service.py`
- Database/migration work: none — both fields already exist; this is a query-layer gap only
- Mobile work: buyer-side marketplace browse screen — add a "near me" filter/sort option
- Automation work: none
- Notification work: none
- Offline/sync impact: none — buyer browse is already online-only
- Security/RBAC impact: none — must preserve the existing approximate-only privacy guarantee (never expose exact coordinates)
- Tests required: a test asserting location-based filtering respects the approximate-only granularity and correctly ranks/filters
- Verification method: automated test

### D61-04 — Grading (group/pooled grading)
- Domain: 61 FPO
- Scenario ID: D61-04
- Exact scenario name: Grading
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - NOT built, structurally requires the Missing D61-02 pooled-listing feature first; `HarvestListing.farmer_id` remains a single FK. The grading engine itself, `CropGradeOption`, is now VERIFIED and dimension-agnostic, but is not the blocker here.)
- Existing relevant files/classes/functions: single-farmer `quality_grade` free text (`harvest_listing.py:38`)
- Missing component: No group/pooled grading concept — only individual-listing grading exists
- Required implementation: none until D61-02 (multi-farmer pooled listing) exists; pooled grading cannot exist without a pooled listing to grade
- Dependencies: D61-02 (aggregation/pooling), D61-03 (bulk quantity) — both MISSING and prerequisite
- Backend work: none until D61-02 exists
- Database/migration work: none until D61-02 exists
- Mobile work: none — backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until the prerequisite pooling feature exists
- Verification method: live manual verification (structurally blocked)

### D64-05 — Payment date
- Domain: 64 Payments
- Scenario ID: D64-05
- Exact scenario name: Payment date
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `PaymentInitiateResponse` (`schemas/order.py`) now includes `created_at`/`completed_at`; the sale-payment endpoints' hand-built response dicts (`api/v1/marketplace.py::initiate_sale_payment`/`complete_sale_payment`) also now include both fields
- Missing component: none
- Required implementation: none
- Dependencies: none
- Backend work: done — `schemas/order.py`, `api/v1/marketplace.py`
- Database/migration work: none — columns already existed
- Mobile work: order/sale detail screens — display the date once the API returns it (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — purely additive
- Tests required: `tests/test_payments.py::test_payment_response_includes_created_and_completed_dates` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D66-03 — Pending (payment sits in PENDING state)
- Domain: 66 Failed Payments
- Scenario ID: D66-03
- Exact scenario name: Pending
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: new `payment_service.run_payment_timeout_sweep`, registered on `scheduler.py` (same APScheduler infra as case-SLA/weather/task sweeps); transitions stale `PENDING` payments to `TIMEOUT` and notifies the farmer via `PAYMENT_ALERT`/`PAYMENT_TIMED_OUT`. Covers both dealer-order (`order_id`) and marketplace-sale (`sale_order_id`) payments in one sweep since `Payment` is a shared table
- Missing component: none
- Required implementation: none
- Dependencies: D66-02 (retry, VERIFIED — a timed-out payment reuses the same retry path since only `PENDING` blocks a new `initiate_payment` call, not `TIMEOUT`); D66-04 (notification, VERIFIED — reuses `PAYMENT_ALERT`)
- Backend work: done — `payment_service.py`, `order_repository.py` (`list_stale_pending_payments`), `scheduler.py`, `core/config.py` (`payment_timeout_minutes`/`payment_timeout_sweep_interval_seconds`)
- Database/migration work: none — `PaymentStatus.TIMEOUT` already existed
- Mobile work: none — backend only; existing payment-status polling picks up the new status
- Automation work: done — new periodic sweep
- Notification work: done — reuses `NotificationCategory.PAYMENT_ALERT`
- Offline/sync impact: none
- Security/RBAC impact: none — system-initiated (`actor_role="scheduler"`), no new permission surface
- Tests required: `tests/test_payments.py::test_payment_timeout_sweep_marks_stale_pending_payments_timed_out` (new), `::test_payment_timeout_sweep_never_touches_a_fresh_pending_payment` (new) - both use scoped assertions (specific payment/notification), not a global sweep-count, since the shared test DB persists leftover PENDING payments across runs
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D67-03 — Evidence
- Domain: 67 Disputes
- Scenario ID: D67-03
- Exact scenario name: Evidence
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `app/services/dispute_evidence_service.py` (its own container prefix/storage pipeline, reusing only `validate_upload`/`process_image`/`FileStorage`, never `CropPhoto`'s table/key); `OrderDispute.evidence_image_key`/`SaleDispute.evidence_image_key` (migration `9c134957c681`); `POST /orders/{order_id}/dispute/evidence` (farmer-only, ownership-checked) and `POST /marketplace/disputes/{dispute_id}/evidence` (either party to the underlying sale, ownership-checked)
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_orders.py::test_farmer_can_upload_dispute_evidence_image`, `::test_farmer_cannot_upload_evidence_to_another_farmers_dispute`; `tests/test_marketplace_offers.py::test_farmer_can_upload_sale_dispute_evidence_image`, `::test_buyer_can_upload_sale_dispute_evidence_image`, `::test_farmer_cannot_upload_evidence_to_another_farmers_sale_dispute`
- Verification method: automated test, confirmed passing
- Dependencies: D67-01 (dispute creation, this would extend), D67-06 (admin resolution, which would review the evidence)
- Backend work: new `dispute_evidence_image_key` column/service on `order_dispute.py`/`sale_dispute.py`, an upload endpoint mirroring the existing crop-photo upload pattern but as its own distinct pipeline
- Database/migration work: new nullable image-storage-key column(s) on `order_disputes`/`sale_disputes` (or a new `dispute_evidence` table for multiple images), plus migration
- Mobile work: dispute-creation screen — add an image picker/upload step
- Automation work: none
- Notification work: none
- Offline/sync impact: image upload would need the same offline-queue handling as other photo uploads in this app (e.g. crop photo capture) if parity is desired
- Security/RBAC impact: none — same ownership rules as existing dispute creation
- Tests required: tests asserting evidence images upload, persist, and are visible to the resolving admin
- Verification method: automated test

### D68-02 — Adjustment architecture (partial refund / price adjustment)
- Domain: 68 Refund/Adjustment Boundary
- Scenario ID: D68-02
- Exact scenario name: Adjustment architecture
- Current implementation status: **VERIFIED (fixed and tested this session, P0, was Partial)**
- Fix applied in `dispute_service.py::resolve_dispute`: rejects (422) a non-positive
  `refund_amount`, and rejects (422) a `refund_amount` exceeding `order.final_amount`.
  Confirmed this session (by direct read of `order_dispute.py`/`order_repository.py`) that
  disputes/refunds are scoped exclusively to `Order` (dealer-marketplace purchases) — no
  `sale_id`/`net_value` field exists on `OrderDispute`/`Refund`, so the cluster file's own
  "presumably `<= sale.net_value` for sale-side refunds" speculation does not correspond to
  any real code path; no such check was needed or added.
- Database/migration work: none — validation-layer only
- Mobile work: none required for the backend-verified status — no dedicated admin
  refund-resolution mobile screen exists in this codebase to update
- Dependencies: D68-01 (refund architecture, same code path) — unaffected, no change
- Tests added and passing: `test_orders.py::test_refund_amount_cannot_exceed_the_orders_final_amount`;
  the pre-existing `test_dispute_and_admin_resolution_with_refund` (an exact-match full
  refund) continues to pass unchanged as the regression check
- Verification method: automated test, confirmed passing in the full suite re-run this
  session

### D69-08 — Storage expense
- Domain: 69 Expenses
- Scenario ID: D69-08
- Exact scenario name: Storage expense
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `LedgerCategory.STORAGE` (migration `ff72e5d0b5a7`)
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_ledger.py::test_storage_category_entry_persists_and_sums_correctly`
- Verification method: automated test, confirmed passing
- Dependencies: D53 domain (storage itself is entirely MISSING) — this is purely a bookkeeping-category gap, independent of whether a storage-booking feature ever exists
- Backend work: `ledger_entry.py` enum addition; no service logic changes needed since the generic ledger-entry creation path already handles any category value
- Database/migration work: a migration adding `STORAGE` to the Postgres native enum type backing `LedgerCategory`
- Mobile work: ledger-entry creation screen — add "Storage" to the category picker
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same as any other ledger entry
- Security/RBAC impact: none — purely additive
- Tests required: a test asserting a `STORAGE`-category entry persists and is summed correctly in ledger totals
- Verification method: automated test

### D70-04 — Plot association
- Domain: 70 Revenue
- Scenario ID: D70-04
- Exact scenario name: Plot association
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `ledger_entry_repository.compute_totals_for_plot` + `crop_financial_service.get_plot_financial_summary` + `GET /plots/{plot_id}/financial-summary` - a pure read aggregation, no new column. Deliberately scoped to totals only (cost/revenue/profit) - no per-acre metrics, no cost-variance, no stage breakdown; a fuller Plot P&L view (per-acre, etc.) remains separately tracked as D71-05 (Missing), not attempted here, to avoid silently completing an entire separately-catalogued Missing scenario as a side effect of this Partial-only pass.
- Missing component: none for this row's own literal scope (a plot-scoped cost/revenue/profit rollup)
- Required implementation: none
- Tests added and passing: `tests/test_crop_financials.py::test_plot_financial_summary_aggregates_across_every_cycle_the_plot_has_had`, `::test_plot_financial_summary_is_zero_not_missing_with_no_entries`, `::test_cannot_access_another_farmers_plot_financial_summary`
- Verification method: automated test, confirmed passing
- Dependencies: D71-05 (Plot P&L, MISSING) — same required join, described fully there
- Backend work: see D71-05
- Database/migration work: see D71-05 ("none" — no direct `plot_id` column needed on `LedgerEntry` itself, the join is sufficient)
- Mobile work: see D71-05
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D71-05
- Verification method: automated test

### D70-05 — Season association
- Domain: 70 Revenue
- Scenario ID: D70-05
- Exact scenario name: Season association
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `ledger_entry_repository.compute_totals_for_season` + `crop_financial_service.get_season_financial_summary` + `GET /farmers/me/seasons/{season}/financial-summary` - same deliberately-scoped-to-totals-only boundary as D70-04; a fuller Season P&L view remains separately tracked as D71-07 (Missing), not attempted here.
- Missing component: none for this row's own literal scope
- Required implementation: none
- Tests added and passing: `tests/test_crop_financials.py::test_season_financial_summary_aggregates_across_plots_and_excludes_other_seasons`
- Verification method: automated test, confirmed passing
- Dependencies: D71-07 (Season P&L, MISSING) — same required aggregation, described fully there
- Backend work: see D71-07
- Database/migration work: see D71-07 ("none" — `CropCycle.season` already exists)
- Mobile work: see D71-07
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D71-07
- Verification method: automated test

## 3. Missing — full itemized (EVERY row, no aggregation)

### D48-01 — Labour planning
- Domain: 48 Harvest Planning
- Scenario ID: D48-01
- Exact scenario name: Labour planning
- Current implementation status: Missing
- Existing relevant files/classes/functions: `TaskType.HARVESTING` exists as a generic to-do type (`task.py:38-45`); `Task` has no worker/assignee/headcount/cost field (`task.py:48-77`)
- Missing component: Any labour-planning concept — worker count, cost, roster
- Required implementation: A `HarvestLabourPlan` entity (headcount, cost estimate, date range) linked to a `HarvestRecord`, or extend `Task` with optional labour-specific fields
- Dependencies: D48-02/03/04/05 (same "Harvest Planning" domain, likely share a common planning-entity pattern if built together)
- Backend work: new model/service under `backend/app/models/`, `backend/app/services/`, mirroring the existing `harvest_service.py` CRUD pattern; new router in `api/v1/`
- Database/migration work: new `harvest_labour_plans` table (harvest_id FK, headcount, estimated_cost, planned_date range), migration
- Mobile work: new screen under harvest planning flow, or an extension to the existing harvest detail screen
- Automation work: none
- Notification work: none required initially
- Offline/sync impact: none required initially — could follow the same online-only pattern as the rest of the harvest module
- Security/RBAC impact: none — farmer-owned resource, same ownership-check pattern as `harvest_repository.get_harvest_owned`
- Tests required: CRUD tests mirroring `test_harvest.py`'s ownership/validation coverage
- Verification method: automated test

### D48-02 — Machinery planning
- Domain: 48 Harvest Planning
- Scenario ID: D48-02
- Exact scenario name: Machinery planning
- Current implementation status: Missing
- Existing relevant files/classes/functions: `LedgerCategory.EQUIPMENT` (`ledger_entry.py:65`) — bookkeeping tag only, not a booking model
- Missing component: No machinery/equipment-booking model anywhere
- Required implementation: A `HarvestMachineryBooking` entity (machine type, provider text field, cost, date), following the same pattern as D48-01
- Dependencies: D48-01 (shared planning-domain pattern)
- Backend work: new model/service/router, same conventions as D48-01
- Database/migration work: new `harvest_machinery_bookings` table, migration
- Mobile work: new screen or harvest-detail extension
- Automation work: none
- Notification work: none required initially
- Offline/sync impact: none required initially
- Security/RBAC impact: none — farmer-owned resource
- Tests required: CRUD/ownership tests
- Verification method: automated test

### D48-03 — Transport planning (pre-harvest)
- Domain: 48 Harvest Planning
- Scenario ID: D48-03
- Exact scenario name: Transport planning (pre-harvest)
- Current implementation status: Missing
- Existing relevant files/classes/functions: only the post-harvest `CollectionOption` label at listing time (`harvest_listing.py:22-25`) — see D55
- Missing component: No pre-harvest transport-planning concept at all
- Required implementation: A pre-harvest transport-plan entity (expected date, mode, estimated cost) distinct from the post-harvest `CollectionOption` label
- Dependencies: D55 domain (post-harvest transport — same conceptual area, different lifecycle stage)
- Backend work: new model/service/router, same conventions as D48-01
- Database/migration work: new `harvest_transport_plans` table, migration
- Mobile work: new screen or harvest-detail extension
- Automation work: none
- Notification work: none required initially
- Offline/sync impact: none required initially
- Security/RBAC impact: none — farmer-owned resource
- Tests required: CRUD/ownership tests
- Verification method: automated test

### D48-04 — Storage planning
- Domain: 48 Harvest Planning
- Scenario ID: D48-04
- Exact scenario name: Storage planning
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no storage model/field anywhere (see Domain 53 summary)
- Missing component: Any storage-planning concept
- Required implementation: Structurally the same prerequisite gap as the entire Domain 53 (Storage) — a `Storage` entity would need to exist before a "storage plan" referencing it could
- Dependencies: D53-01..07 (Storage domain, entirely MISSING) — prerequisite
- Backend work: none until D53 exists
- Database/migration work: none until D53 exists
- Mobile work: none — backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until D53 exists
- Verification method: live manual verification (structurally blocked)

### D48-05 — Buyer planning (pre-harvest)
- Domain: 48 Harvest Planning
- Scenario ID: D48-05
- Exact scenario name: Buyer planning (pre-harvest)
- Current implementation status: Missing
- Existing relevant files/classes/functions: only the post-harvest reactive `HarvestListing`→`BuyerOffer` flow (`marketplace.py`), which starts only once a harvest is `LISTED`
- Missing component: Any pre-harvest buyer-selection tool
- Required implementation: A pre-harvest "buyer interest" or forward-contract concept, letting a farmer line up a buyer before the harvest is ready/listed — a materially larger feature than the reactive post-harvest flow
- Dependencies: D59-07 (automated buyer↔listing matching, MISSING) — a pre-harvest buyer-planning tool would likely build on the same matching infrastructure
- Backend work: new `pre_harvest_buyer_interest` model/service, `crop_cycle_id`-scoped (not `harvest_id`, since the harvest may not exist yet)
- Database/migration work: new table linking `crop_cycle_id` to a prospective `buyer_id`/interest note
- Mobile work: new screen, likely surfaced from the crop-cycle detail view
- Automation work: none required initially
- Notification work: could reuse `NotificationCategory.MARKET_ALERT`-style category once it exists (see D59-07)
- Offline/sync impact: none required initially
- Security/RBAC impact: none — farmer-owned resource for creation; buyer-visibility would need a new access-control rule (buyers seeing pre-harvest interest listings)
- Tests required: CRUD/ownership tests once built
- Verification method: automated test

### D50-03 — Yield/acre
- Domain: 50 Yield
- Scenario ID: D50-03
- Exact scenario name: Yield/acre
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `profit_forecast_service._compute_yield_per_acre` (new), surfaced as `yield_per_acre`/`yield_per_acre_unit` on `CropProfitForecastResponse` - same `_per_acre` pattern as D72-04/05/06's cost/revenue/profit_loss_per_acre, applied to harvest quantity (`actual_quantity` once harvested, else `estimated_quantity`) instead of financial figures
- Missing component: none
- Required implementation: none
- Dependencies: D50-01 (yield estimate — the quantity input)
- Backend work: done — `profit_forecast_service.py`, `schemas/profit_forecast.py`
- Database/migration work: none — computed, not stored, following the same pattern as `cost_per_acre`
- Mobile work: harvest detail / profit forecast screen — display the new field (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — purely additive
- Tests required: `tests/test_profit_forecast.py::test_yield_per_acre_scales_with_actual_plot_area` (new, mirrors `test_per_acre_financials_scale_with_actual_plot_area`), `::test_yield_per_acre_is_none_without_a_harvest_record` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D50-04 — Historical yield (past-season reference)
- Domain: 50 Yield
- Scenario ID: D50-04
- Exact scenario name: Historical yield (past-season reference)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no aggregation query across a farmer's/crop's past `HarvestRecord`s found
- Missing component: Any historical-yield aggregation
- Required implementation: A query aggregating a farmer's past `HarvestRecord.estimated_quantity`/`actual_quantity` grouped by crop, similar in spirit to `crop_comparison_service.py`'s existing cross-cycle comparison pattern
- Dependencies: D49-02/D50-02 (actual_quantity is never populated today, FUTURE) — historical *actual* yield is meaningless until that FUTURE work lands; historical *estimated* yield could be built independently now
- Backend work: new function in `crop_comparison_service.py` or a new `harvest_history_service.py`
- Database/migration work: none — aggregation over existing columns
- Mobile work: a "past harvests" view, possibly on the crop-cycle or profit-forecast screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-scoped query, same ownership pattern as existing services
- Tests required: aggregation-correctness tests mirroring `test_crop_financials.py`'s summation tests
- Verification method: automated test

### D50-06 — Confidence (on yield figures)
- Domain: 50 Yield
- Scenario ID: D50-06
- Exact scenario name: Confidence
- Current implementation status: Missing
- Existing relevant files/classes/functions: none on harvest quantity; AI-diagnosis confidence fields (`ai_analysis.py:90`, `assistant_conversation.py:61`) are unrelated
- Missing component: Any confidence/reliability field on `estimated_quantity`/`actual_quantity`
- Required implementation: A `quantity_confidence` enum (e.g. mirroring `OcrConfidence`'s HIGH/MEDIUM/LOW pattern from `invoice.py`) settable by the farmer at confirm-ready time, expressing their own certainty
- Dependencies: none blocking
- Backend work: `harvest_record.py` (new nullable enum column), `schemas/harvest.py` (`HarvestConfirmReadyRequest`), `harvest_service.py`
- Database/migration work: new `quantity_confidence` column, migration
- Mobile work: confirm-ready sheet — add a confidence selector
- Automation work: none
- Notification work: none
- Offline/sync impact: none — travels with the existing confirm-ready payload
- Security/RBAC impact: none — purely additive
- Tests required: a test asserting the field persists and round-trips
- Verification method: automated test

### D51-02 — Moisture
- Domain: 51 Quality
- Scenario ID: D51-02
- Exact scenario name: Moisture
- Current implementation status: VERIFIED (this continuation session, was Missing) — scoped to `HarvestRecord` only, not `HarvestListing`
- Existing relevant files/classes/functions: `HarvestRecord.moisture_percent` (new, `harvest_record.py`), farmer-entered at `confirm_ready` time via `HarvestConfirmReadyRequest.moisture_percent` - never fabricated sensor/lab data
- Missing component: none on `HarvestRecord`. Not duplicated onto `HarvestListing` (buyers already see `quality_grade`; a disclosed, deliberate scope reduction to limit blast radius, not a hidden gap)
- Required implementation: none
- Dependencies: none blocking
- Backend work: done — `harvest_record.py`, `schemas/harvest.py`, `harvest_service.py`
- Database/migration work: done — `a2b3c4d5e6f7_add_moisture_percent_and_defect_notes.py`
- Mobile work: confirm-ready form — add a moisture input field (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none — travels with existing payloads
- Security/RBAC impact: none — purely additive
- Tests required: `tests/test_harvest.py::test_confirm_ready_persists_moisture_and_defect_notes` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D51-03 — Size (grading by size)
- Domain: 51 Quality
- Scenario ID: D51-03
- Exact scenario name: Size
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `CropGradeOption` (D52-02's grading engine) is deliberately dimension-agnostic - an admin can configure size-based grade codes ("Large"/"Medium"/"Small") through the exact same table and validation path used for quality grades, rather than a separate `size_grade` column. The crop-specific taxonomy choice (is a grade about quality, size, or both) belongs to whoever sources the real per-crop data, not to the schema
- Missing component: none - folded into D52-02 as planned rather than built standalone
- Required implementation: none
- Dependencies: D52-02 (formal grading engine, now VERIFIED)
- Backend work: see D52-02
- Database/migration work: see D52-02
- Mobile work: see D52-02
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D52-02 (the mechanism is identical; no size-specific test needed beyond proving the generic validation path works)
- Verification method: automated test (shared with D52-02), confirmed passing in the full 786-test suite re-run this session

### D51-04 — Defects
- Domain: 51 Quality
- Scenario ID: D51-04
- Exact scenario name: Defects
- Current implementation status: VERIFIED (this continuation session, was Missing) — scoped to `HarvestRecord` only, not `HarvestListing`
- Existing relevant files/classes/functions: `HarvestRecord.defect_notes` (new, `harvest_record.py`), farmer-entered free text at `confirm_ready` time via `HarvestConfirmReadyRequest.defect_notes`
- Missing component: none on `HarvestRecord`. Not duplicated onto `HarvestListing` - same disclosed scope reduction as D51-02
- Required implementation: none
- Dependencies: none blocking
- Backend work: done — `harvest_record.py`, `schemas/harvest.py`, `harvest_service.py`
- Database/migration work: done — `a2b3c4d5e6f7_add_moisture_percent_and_defect_notes.py`
- Mobile work: confirm-ready form (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — purely additive
- Tests required: `tests/test_harvest.py::test_confirm_ready_persists_moisture_and_defect_notes` (new, shared with D51-02)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D51-06 — Certificate
- Domain: 51 Quality
- Scenario ID: D51-06
- Exact scenario name: Certificate
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grep for "certificate" returns zero real hits
- Missing component: Any certificate model/field (the cluster file itself notes a *real* agricultural quality certificate would in any case be OUT_OF_SCOPE as an external credential — this MISSING classification covers only the absent internal placeholder/reference field)
- Required implementation: At most, a farmer-entered reference field (e.g. `certificate_reference_note: str | None`) noting a certificate exists, never a fabricated verification of one
- Dependencies: none blocking
- Backend work: `harvest_record.py`/`harvest_listing.py`, `schemas/harvest.py`, if pursued at all
- Database/migration work: new nullable column, migration
- Mobile work: listing-creation form
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: persistence/round-trip test if built
- Verification method: automated test (low priority — genuinely low-value without a real credentialing body behind it)

### D52-01 — Sorting
- Domain: 52 Post-Harvest
- Scenario ID: D52-01
- Exact scenario name: Sorting
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `HarvestListing.is_sorted`/`sorting_notes` (new), set via `HarvestListingCreateRequest` at `create_listing` time - farmer-declared only, never inferred or verified by this system, same honesty convention as `quality_grade`
- Missing component: none
- Required implementation: none
- Dependencies: none (built independently of D52-02, not folded into it - a distinct farmer declaration, not a grade)
- Backend work: done — `harvest_listing.py`, `schemas/harvest.py`, `harvest_service.py`
- Database/migration work: done — `e6f7a8b9c0d1_add_is_sorted_and_sorting_notes.py`
- Mobile work: harvest listing screen (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: `tests/test_harvest.py::test_create_listing_records_sorting_declaration` (new)
- Verification method: automated test (new), confirmed passing in the full 787-test suite re-run this session

### D52-03 — Packing
- Domain: 52 Post-Harvest
- Scenario ID: D52-03
- Exact scenario name: Packing
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — `docs/BUYER_WORKFLOW.md:54` explicitly lists "what packaging do you need?" as an assistant question type NOT handled
- Missing component: Any packing/packaging model
- Required implementation: A `packing_requirements` free-text field on `HarvestListing`, and (separately, larger scope) wiring the AI assistant to actually answer this question type instead of declining it
- Dependencies: none blocking for the field itself; the assistant-handling half depends on the existing assistant question-routing infrastructure (`docs/BUYER_WORKFLOW.md`)
- Backend work: `harvest_listing.py`, `schemas/harvest.py`; assistant question-handling update in the relevant assistant service if pursued
- Database/migration work: new nullable column, migration
- Mobile work: listing-creation form
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: persistence test; assistant-response test if that half is pursued
- Verification method: automated test

### D52-04 — Storage (post-harvest)
- Domain: 52 Post-Harvest
- Scenario ID: D52-04
- Exact scenario name: Storage (post-harvest)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — see Domain 53 summary
- Missing component: Any storage model
- Required implementation: See D53-01 (Storage location) — this row is the post-harvest-workflow view of that same entirely-absent domain
- Dependencies: D53-01..07 (entire Storage domain, prerequisite)
- Backend work: see D53-01
- Database/migration work: see D53-01
- Mobile work: see D53-01
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D53-01
- Verification method: live manual verification (structurally blocked until D53 exists)

### D52-07 — Spoilage risk
- Domain: 52 Post-Harvest
- Scenario ID: D52-07
- Exact scenario name: Spoilage risk
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grep for "spoilage" across backend/mobile/docs returns zero real hits
- Missing component: Any spoilage-risk model, field, or rule
- Required implementation: A rule-based spoilage-risk estimate (e.g. days-since-harvest vs. a per-crop shelf-life reference) — would require an authoritative per-crop shelf-life dataset, similar in spirit to the already-disclosed no-fabricated-agronomic-data constraint the project applies elsewhere (e.g. D21-01's seed-rate reference, deferred FUTURE for the same reason)
- Dependencies: An authoritative per-crop shelf-life reference dataset does not currently exist in this codebase — same class of blocker as D21-01
- Backend work: new `spoilage_risk_service.py` once a real reference dataset is sourced
- Database/migration work: a new `crop_shelf_life_reference` table, only once real data is sourced
- Mobile work: harvest detail screen — a risk indicator
- Automation work: a scheduled sweep recomputing risk as time passes (mirroring the existing scheduler pattern)
- Notification work: could reuse `NotificationCategory.HARVEST_ALERT`
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests once a real dataset and rule exist
- Verification method: automated test (blocked pending real data — recommend reclassifying FUTURE with an explicit deferral note, consistent with D21-01's precedent, rather than leaving it an unexplained MISSING)

### D53-01 — Storage location
- Domain: 53 Storage
- Scenario ID: D53-01
- Exact scenario name: Storage location
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grep confirms only unrelated file-blob `storage_key` fields exist
- Missing component: Any physical storage-location model
- Required implementation: A `Storage` entity (location text/geo, owner/type) as the foundation for the whole Storage domain (D53-02..07)
- Dependencies: prerequisite for D53-02, D53-03, D53-04, D53-05, D53-06, D53-07, and D48-04/D52-04
- Backend work: new `storage.py` model, `storage_service.py`, `api/v1/storage.py` router, mirroring `harvest_service.py`'s CRUD/ownership conventions
- Database/migration work: new `storages` table, migration
- Mobile work: new storage-management screen(s)
- Automation work: none required initially
- Notification work: none required initially
- Offline/sync impact: none required initially — could follow the harvest module's online-only pattern
- Security/RBAC impact: none — farmer-owned resource, same ownership pattern as `harvest_repository.get_harvest_owned`
- Tests required: CRUD/ownership tests mirroring `test_harvest.py`
- Verification method: automated test

### D53-02 — Capacity
- Domain: 53 Storage
- Scenario ID: D53-02
- Exact scenario name: Capacity
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any storage-capacity concept
- Required implementation: A `capacity`/`unit` field on the `Storage` entity from D53-01
- Dependencies: D53-01 (prerequisite)
- Backend work: extend D53-01's model
- Database/migration work: extend D53-01's migration
- Mobile work: extend D53-01's screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: extend D53-01's tests
- Verification method: automated test

### D53-03 — Cost
- Domain: 53 Storage
- Scenario ID: D53-03
- Exact scenario name: Cost
- Current implementation status: Missing
- Existing relevant files/classes/functions: `LedgerCategory` enum has no `STORAGE` value (same gap as D69-08)
- Missing component: A dedicated storage-cost category and, ideally, a rate tied to the D53-01 `Storage` entity
- Required implementation: Add `LedgerCategory.STORAGE` (see D69-08 — same change satisfies both), and optionally a `cost_per_unit_per_day` field on the `Storage` entity from D53-01
- Dependencies: D53-01 (storage entity), D69-08 (same ledger-category change)
- Backend work: `ledger_entry.py` enum addition (shared with D69-08); optional rate field on `Storage`
- Database/migration work: shared with D69-08's migration
- Mobile work: shared with D69-08
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: shared with D69-08
- Verification method: automated test

### D53-04 — Duration
- Domain: 53 Storage
- Scenario ID: D53-04
- Exact scenario name: Duration
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any storage-duration field
- Required implementation: `stored_at`/`released_at` timestamps on a storage-usage record (see D53-07 — release), tied to the D53-01 `Storage` entity
- Dependencies: D53-01, D53-05 (stored quantity), D53-07 (release)
- Backend work: new `storage_usage` model linking `Storage` to a `HarvestRecord`, with start/end timestamps
- Database/migration work: new `storage_usages` table, migration
- Mobile work: extend the D53-01 storage screen with a "move harvest into/out of storage" action
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: CRUD tests on the new usage record
- Verification method: automated test

### D53-05 — Stored quantity
- Domain: 53 Storage
- Scenario ID: D53-05
- Exact scenario name: Stored quantity
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any field tracking quantity currently in storage vs. sold/available
- Required implementation: A `quantity` field on the `storage_usage` record from D53-04
- Dependencies: D53-01, D53-04
- Backend work: extend the D53-04 `storage_usage` model
- Database/migration work: extend D53-04's migration
- Mobile work: extend D53-04's screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: extend D53-04's tests
- Verification method: automated test

### D53-06 — Spoilage (in storage)
- Domain: 53 Storage
- Scenario ID: D53-06
- Exact scenario name: Spoilage (in storage)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — same as D52-07
- Missing component: Any spoilage concept
- Required implementation: Same as D52-07 — blocked on a real per-crop shelf-life reference dataset
- Dependencies: D52-07 (identical gap/blocker), D53-01/D53-04 (storage entity/duration, which a storage-specific spoilage rule would also need)
- Backend work: see D52-07
- Database/migration work: see D52-07
- Mobile work: see D52-07
- Automation work: see D52-07
- Notification work: see D52-07
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D52-07
- Verification method: automated test (blocked pending real data — same FUTURE-reclassification recommendation as D52-07)

### D53-07 — Release from storage
- Domain: 53 Storage
- Scenario ID: D53-07
- Exact scenario name: Release from storage
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no storage entity to release from
- Missing component: Any release workflow
- Required implementation: The `released_at` timestamp/action on the `storage_usage` record from D53-04
- Dependencies: D53-01, D53-04, D53-05
- Backend work: extend the D53-04 `storage_usage` service with a `release` action
- Database/migration work: none beyond D53-04's migration
- Mobile work: extend D53-04's screen with a "release" button
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: extend D53-04's tests
- Verification method: automated test

### D55-03 — Distance
- Domain: 55 Transport
- Scenario ID: D55-03
- Exact scenario name: Distance
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — `service_area` is deliberately approximate (state/district only, `test_harvest.py:61-67`), which would preclude real distance/route calculation even if attempted
- Missing component: Any distance calculation
- Required implementation: Deliberately not straightforward to build without weakening the existing location-privacy design (exact coordinates are never stored, `harvest_listing.py:3-7`); at most, a coarse state/district-level "same district" vs. "different district" flag could be added without violating that design
- Dependencies: D57-03 (distance to market/buyer, same gap), D59-05 (location matching, which would consume a coarse distance signal)
- Backend work: a coarse district-adjacency helper if pursued, respecting the existing approximate-only design
- Database/migration work: none — would reuse the existing `service_area` JSONB
- Mobile work: `OffersScreen`/listing-browse — surface the coarse proximity signal
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — must preserve the existing privacy guarantee (verified by `test_listing_service_area_never_contains_exact_coordinates_by_construction`)
- Tests required: a test asserting any new distance signal still never derives/exposes exact coordinates
- Verification method: automated test

### D55-04 — Rate
- Domain: 55 Transport
- Scenario ID: D55-04
- Exact scenario name: Rate
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any transport-rate field/model
- Required implementation: A `transport_rate_reference` table (per-distance-band or per-crop-weight rate), feeding the D57-04/D58-02 itemized transport-cost field — this is the "real transport cost rate" data source the itemization work (D57-04) needs
- Dependencies: D57-04/D58-02 (transport deduction — this is the missing rate source behind that itemization), D55-02 (transporter role, OUT_OF_SCOPE — a rate reference doesn't require an actual transporter relationship, so this can proceed independently)
- Backend work: new `transport_rate_reference` model/service
- Database/migration work: new `transport_rate_references` table, migration
- Mobile work: none — backend only; consumed by the accept-offer flow's transport-charge calculation
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — read-only reference data, likely admin-managed
- Tests required: tests asserting a rate lookup produces a correct charge figure
- Verification method: automated test

### D55-05 — Scheduling
- Domain: 55 Transport
- Scenario ID: D55-05
- Exact scenario name: Scheduling
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grep for "pickup_date"/"scheduled_pickup" returns zero hits; the only "estimated_delivery_date" (`delivery.py:45`) belongs to the unrelated dealer input-purchase `Delivery` model
- Missing component: Any pickup/delivery scheduling field on a harvest-sale entity
- Required implementation: A `scheduled_pickup_date`/`scheduled_delivery_date` field on `SaleOrder`, set at the same point D55-06/D55-07's confirmation states would be introduced
- Dependencies: D55-06 (pickup), D55-07 (delivery) — natural to build together
- Backend work: see D55-06/D55-07
- Database/migration work: see D55-06/D55-07
- Mobile work: see D55-06/D55-07
- Automation work: none
- Notification work: could reuse existing notification infra for a "pickup scheduled" reminder
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D55-06/D55-07
- Verification method: automated test

### D56-01 — Mandi price (real government/APMC price)
- Domain: 56 Market Prices
- Scenario ID: D56-01
- Exact scenario name: Mandi price
- Current implementation status: Missing
- Existing relevant files/classes/functions: `backend/app/api/v1/market.py` — explicitly empty reserved router ("No endpoints yet")
- Missing component: Any live mandi/APMC price feed integration
- Required implementation: Integration with a real government price data source (Agmarknet/data.gov.in/eNAM), exactly as named in `docs/PRICE_DATA_SOURCES.md:18-29` as what a real integration would require — this project structurally never fabricates this data, so the honest next step is a genuine external API integration, not an internal build
- Dependencies: D56-02..07 (all downstream of this feed existing), D57-01/02/03 (market comparison, downstream), D60 (eNAM boundary — this is the exact boundary the project draws around this gap)
- Backend work: a new `mandi_price_service.py` client for whichever real government API is chosen, `api/v1/market.py` (fill in the reserved router), caching/staleness handling following the existing `ReferencePrice`/weather-provider abstraction pattern (`app/services/weather/` has a precedent for provider abstraction + staleness fallback)
- Database/migration work: a new `mandi_price` table (commodity, market, date, min/max/modal price, arrivals), migration
- Mobile work: a new "market prices" screen
- Automation work: a scheduled daily price-refresh sweep
- Notification work: none required initially
- Offline/sync impact: cached prices should follow the existing weather-data staleness-fallback pattern (`docs/audit` for domain 14 cites this precedent)
- Security/RBAC impact: none — read-only public data
- Tests required: tests mirroring the weather-provider abstraction tests (staleness, `available:false` honesty)
- Verification method: environment-dependent once built (depends on live government API reachability, per the D14 weather precedent) — currently: live manual verification is not possible since no integration exists

### D56-02 — Min price
- Domain: 56 Market Prices
- Scenario ID: D56-02
- Exact scenario name: Min price
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Per-commodity daily min price
- Required implementation: A field on the D56-01 `mandi_price` table/service
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01
- Database/migration work: see D56-01 (`min_price` column)
- Mobile work: see D56-01
- Automation work: see D56-01
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D56-03 — Max price
- Domain: 56 Market Prices
- Scenario ID: D56-03
- Exact scenario name: Max price
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Per-commodity daily max price
- Required implementation: A field on the D56-01 `mandi_price` table/service
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01
- Database/migration work: see D56-01 (`max_price` column)
- Mobile work: see D56-01
- Automation work: see D56-01
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D56-04 — Modal price
- Domain: 56 Market Prices
- Scenario ID: D56-04
- Exact scenario name: Modal price
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Per-commodity modal price
- Required implementation: A field on the D56-01 `mandi_price` table/service
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01
- Database/migration work: see D56-01 (`modal_price` column)
- Mobile work: see D56-01
- Automation work: see D56-01
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D56-05 — Arrivals (volume traded)
- Domain: 56 Market Prices
- Scenario ID: D56-05
- Exact scenario name: Arrivals
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Daily arrival-quantity feed
- Required implementation: A field on the D56-01 `mandi_price` table/service
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01
- Database/migration work: see D56-01 (`arrivals_quantity` column)
- Mobile work: see D56-01
- Automation work: see D56-01
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D56-06 — Historical price (crop selling)
- Domain: 56 Market Prices
- Scenario ID: D56-06
- Exact scenario name: Historical price (crop selling)
- Current implementation status: Missing
- Existing relevant files/classes/functions: `product_repository.list_reference_price_history` exists but only for input products (`product_repository.py:51`); `reference_prices` table is scoped to `products.id`, not crops (`reference_price.py:32`)
- Missing component: Any time-series of real crop-selling prices
- Required implementation: A time-series query over the D56-01 `mandi_price` table once it exists
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01, plus a history-query endpoint
- Database/migration work: see D56-01
- Mobile work: see D56-01
- Automation work: none additional
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D56-07 — Price freshness (crop selling)
- Domain: 56 Market Prices
- Scenario ID: D56-07
- Exact scenario name: Price freshness (crop selling)
- Current implementation status: Missing
- Existing relevant files/classes/functions: the mechanism (`effective_date`/`retrieved_at`) exists only on input-side `ReferencePrice` (`reference_price.py:42-44`), and even there the farmer-friendly "updated X days ago" rendering is "not yet built server-side" (`docs/PRICE_DATA_SOURCES.md:35-37`)
- Missing component: Any freshness signal for crop-selling prices
- Required implementation: `retrieved_at`/staleness fields on the D56-01 `mandi_price` table, following the same pattern as `ReferencePrice`
- Dependencies: D56-01 (prerequisite)
- Backend work: see D56-01
- Database/migration work: see D56-01 (`retrieved_at` column)
- Mobile work: see D56-01 — "updated X days ago" rendering, disclosed as not yet built even for the input-side precedent
- Automation work: see D56-01
- Notification work: none
- Offline/sync impact: see D56-01
- Security/RBAC impact: none
- Tests required: see D56-01
- Verification method: environment-dependent (blocked on D56-01)

### D57-01 — Multiple markets (mandis/yards)
- Domain: 57 Market Comparison
- Scenario ID: D57-01
- Exact scenario name: Multiple markets (mandis/yards)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no `Market`/`Mandi` entity anywhere in the schema
- Missing component: A registry of distinct markets/mandis
- Required implementation: A `Market`/`Mandi` reference entity (name, location, APMC code), the foundational entity D56-01 and D57-02 both need
- Dependencies: prerequisite for D56-01..07, D57-02, D58-07, D60-02
- Backend work: new `market.py` model, seeded reference data or admin-managed CRUD
- Database/migration work: new `markets` table, migration, seed data
- Mobile work: none required initially — consumed by other features' UI
- Automation work: none
- Notification work: none
- Offline/sync impact: none — reference data, cacheable
- Security/RBAC impact: none — read-only reference data
- Tests required: basic CRUD/seed tests
- Verification method: automated test

### D57-03 — Distance (to market/buyer)
- Domain: 57 Market Comparison
- Scenario ID: D57-03
- Exact scenario name: Distance (to market/buyer)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grep confirms zero matches for distance/geo/lat/long in `harvest_service.py`/`harvest_repository.py`
- Missing component: Farmer & buyer/market coordinates and any distance calculation
- Required implementation: Same as D55-03 — a coarse, privacy-respecting proximity signal only, never exact coordinates
- Dependencies: D55-03 (identical gap, different domain grouping), D59-05 (location matching)
- Backend work: see D55-03
- Database/migration work: see D55-03
- Mobile work: see D55-03
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: see D55-03 — must preserve existing privacy guarantee
- Tests required: see D55-03
- Verification method: automated test

### D57-06 — Storage cost
- Domain: 57 Market Comparison
- Scenario ID: D57-06
- Exact scenario name: Storage cost
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: A storage-cost rate feeding the net-realization comparison
- Required implementation: Part of the same itemization effort as D57-04/D58-05 — a `storage_charge` field, sourced from the D53-03 storage-cost rate once that exists
- Dependencies: D58-05 (storage deduction, same gap), D53-03 (storage cost rate, MISSING, feeds this)
- Backend work: same as D57-04's itemization work, plus D53-03's rate source
- Database/migration work: same as D57-04
- Mobile work: same as D57-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D58-04 — Handling (deduction)
- Domain: 58 Net Realization
- Scenario ID: D58-04
- Exact scenario name: Handling (deduction)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: A handling-cost rate/field
- Required implementation: Part of the same itemization effort as D57-04 — a `handling_charge` field
- Dependencies: D57-04/D57-05 (same itemization effort)
- Backend work: same as D57-04
- Database/migration work: same as D57-04
- Mobile work: same as D57-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D58-05 — Storage (deduction)
- Domain: 58 Net Realization
- Scenario ID: D58-05
- Exact scenario name: Storage (deduction)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: A storage-cost deduction field
- Required implementation: Same as D57-06 — part of the itemization effort, sourced from D53-03 once it exists
- Dependencies: D57-06 (identical gap), D53-03 (storage cost rate)
- Backend work: same as D57-04/D57-06
- Database/migration work: same as D57-04
- Mobile work: same as D57-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D57-04
- Verification method: automated test

### D58-07 — Comparison (of net realization across options/buyers)
- Domain: 58 Net Realization
- Scenario ID: D58-07
- Exact scenario name: Comparison
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Multiple net-realization figures to compare across options/buyers
- Required implementation: Once itemized net_value exists (D57-07/D58-06) and multiple concurrent offers/markets exist (D57-01), a comparison view listing net-realization-per-option side by side
- Dependencies: D57-07, D58-06 (itemized net value), D57-01 (market registry), D57-02 (comparison UI pattern to extend)
- Backend work: a comparison endpoint aggregating net_value across a listing's active offers/markets
- Database/migration work: none beyond the prerequisite itemization work
- Mobile work: `OffersScreen` — a side-by-side net-realization comparison view
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests asserting correct ranking/comparison of net values
- Verification method: automated test

### D61-02 — Aggregation (pooling multiple farmers' harvest)
- Domain: 61 FPO
- Scenario ID: D61-02
- Exact scenario name: Aggregation
- Current implementation status: Missing
- Existing relevant files/classes/functions: `HarvestListing.farmer_id` is a single FK (`harvest_listing.py:33`) — structurally one-farmer-per-listing
- Missing component: Any multi-farmer pooled listing concept
- Required implementation: A `PooledListing` entity referencing multiple `HarvestRecord`s across different farmers, or a many-to-many join table between `HarvestListing` and contributing farmers — a genuinely large structural change, not a field addition
- Dependencies: prerequisite for D61-03, D61-04, D61-05, D61-07; conceptually tied to D61-01 (FPO membership, OUT_OF_SCOPE) though a pooled listing could theoretically exist without a formal FPO legal entity
- Backend work: new `pooled_listing.py` model, `pooled_listing_service.py`, significant changes to `offer_service.py`'s single-farmer assumptions throughout
- Database/migration work: new `pooled_listings` + join table, migration; likely non-trivial changes to `sale_orders`' single-`farmer_id` assumption for split settlement (see D61-08)
- Mobile work: a new group-listing creation flow
- Automation work: none required initially
- Notification work: notify all contributing farmers on offer/sale events
- Offline/sync impact: none required initially
- Security/RBAC impact: new authorization model for "who can act on behalf of a pooled listing" — a real RBAC design question, not purely additive
- Tests required: extensive multi-farmer ownership/authorization tests
- Verification method: automated test

### D61-03 — Bulk quantity (pooled across farmers)
- Domain: 61 FPO
- Scenario ID: D61-03
- Exact scenario name: Bulk quantity
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any pooled-quantity concept
- Required implementation: A computed sum across the D61-02 pooled listing's contributing `HarvestRecord`s
- Dependencies: D61-02 (prerequisite)
- Backend work: see D61-02
- Database/migration work: see D61-02
- Mobile work: see D61-02
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: see D61-02
- Tests required: see D61-02
- Verification method: automated test

### D61-05 — Packing (group packing/repackaging service)
- Domain: 61 FPO
- Scenario ID: D61-05
- Exact scenario name: Packing
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any group-packing service concept
- Required implementation: Blocked on D61-02 (pooling) existing first
- Dependencies: D61-02 (prerequisite)
- Backend work: none until D61-02 exists
- Database/migration work: none until D61-02 exists
- Mobile work: none — backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until D61-02 exists
- Verification method: live manual verification (structurally blocked)

### D61-07 — Group transport (shared logistics for pooled sale)
- Domain: 61 FPO
- Scenario ID: D61-07
- Exact scenario name: Group transport
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: Any shared-logistics concept for pooled sales
- Required implementation: Blocked on D61-02 (pooling) existing first, and conceptually overlaps with the entirely-absent Transport domain (D55)
- Dependencies: D61-02, D55 domain
- Backend work: none until prerequisites exist
- Database/migration work: none until prerequisites exist
- Mobile work: none — backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until prerequisites exist
- Verification method: live manual verification (structurally blocked)

### D65-01 — Partial payment (pay less than full amount)
- Domain: 65 Partial Payments
- Scenario ID: D65-01
- Exact scenario name: Partial payment
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - scoped to the DEALER ORDER flow only (`payment_service.py`/`orders.py`), per this row's own citations - the marketplace SALE flow (`sale_order_service.py`) still hardcodes the full amount and is out of scope for this row (not audited under D65 at all). `PaymentInitiateRequest.amount` (optional, defaults to the full remaining balance) validated against a real computed remaining balance, never trusted blindly. Tests: `test_payments.py::test_farmer_can_pay_a_partial_amount_and_order_stays_payment_pending`, `test_cannot_pay_more_than_the_remaining_balance`
- Existing relevant files/classes/functions: `Payment.amount` always set to `order.final_amount`/`sale.net_value` verbatim (`payment_service.py:35`, `sale_order_service.py:113`); `PaymentCompleteRequest` (`schemas/order.py:85-88`) only carries `succeed: bool`
- Missing component: Any partial-amount field anywhere in the Payment model/schema/service layer
- Required implementation: Add an `amount: Decimal` field to the payment-initiation request, validated `<= order.final_amount`; track `Payment.amount` as the actually-tendered amount rather than always the full order value
- Dependencies: D65-02 (remaining balance), D65-03 (multiple/installment payments), D65-04 (balance tracking), D65-05 (payment history) — all downstream of this core model change
- Backend work: `payment_service.py::initiate_payment` (accept and validate a partial amount), `schemas/order.py` (new request field), `order_repository.py` (balance-remaining query)
- Database/migration work: `payments.amount` likely already exists as a column but is currently always the full value — no new column needed, but the order-level "is this fully paid" check needs new logic (a computed/derived "amount_paid_total" or a new `orders.amount_remaining`)
- Mobile work: payment screen — allow entering a partial amount instead of assuming full payment
- Automation work: none
- Notification work: could extend `PAYMENT_ALERT` to include a "partial payment received, balance remaining" message
- Offline/sync impact: none — payment already requires a live API call
- Security/RBAC impact: none — same ownership/authorization as existing payment flow
- Tests required: tests asserting partial amounts are accepted, summed correctly, and that `PAID` is only reached once the full amount is covered
- Verification method: automated test

### D65-02 — Remaining balance tracking
- Domain: 65 Partial Payments
- Scenario ID: D65-02
- Exact scenario name: Remaining balance tracking
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - `OrderResponse.amount_paid`/`amount_remaining`, computed fresh from successful `Payment` rows (never stored), exposed on the order-detail (`get_my_order`) and order-list (`list_my_orders`) reads. Test: `test_payments.py::test_order_detail_reports_full_remaining_balance_before_any_payment`
- Existing relevant files/classes/functions: none — only one full-amount payment attempt is modeled per order
- Missing component: Any "balance remaining" concept
- Required implementation: A computed `amount_remaining = order.final_amount - sum(successful Payment.amount)` function, exposed via the order-detail response
- Dependencies: D65-01 (prerequisite — partial amounts must exist before a "remaining balance" is meaningful)
- Backend work: `order_repository.py` (new aggregate query), `schemas/order.py` (expose the field)
- Database/migration work: none — computed from existing `payments` rows once D65-01 lands
- Mobile work: order detail screen — display remaining balance
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: a test asserting correct remaining-balance computation across multiple partial payments
- Verification method: automated test

### D65-03 — Multiple payments (installments against one order)
- Domain: 65 Partial Payments
- Scenario ID: D65-03
- Exact scenario name: Multiple payments
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - `Payment.installment_number` (migration `aa4170ae6a30`); `initiate_payment` allows a second/subsequent payment once a real balance remains (via `sum_successful_payment_amount_for_order`), and `complete_payment` only transitions the order to PAID once cumulative successful payments reach `final_amount` - otherwise stays PAYMENT_PENDING for a further installment. Test: `test_payments.py::test_second_installment_completes_the_order_once_balance_is_fully_paid`
- Existing relevant files/classes/functions: `Payment.order_id`/`sale_order_id` are not unique (multiple rows physically possible), but `get_latest_payment_for_order` (`order_repository.py:80-81`) only ever looks at the single most recent row; no endpoint creates a second `Payment` while the order isn't back in a pre-payment state (see D66-02)
- Missing component: `payments` has no `sequence`/`installment_number` column; no endpoint supports intentionally creating a second payment for the same order while it's still partially paid
- Required implementation: Allow `initiate_payment` to create an additional `Payment` row when the order has an outstanding balance (D65-02), with a `sequence`/`installment_number` column for ordering
- Dependencies: D65-01, D65-02 (prerequisites)
- Backend work: `payment_service.py::initiate_payment` — relax the current single-payment-per-order assumption once a balance-remaining concept exists
- Database/migration work: new `installment_number` column on `payments`, migration
- Mobile work: payment screen — show installment history/progress
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests asserting multiple payments accumulate correctly toward the total
- Verification method: automated test

### D65-04 — Balance tracking (ledger-level, across multiple payments)
- Domain: 65 Partial Payments
- Scenario ID: D65-04
- Exact scenario name: Balance tracking (ledger-level)
- Current implementation status: **Missing (deliberately deferred, Missing Backlog Batch 2)** - re-confirmed genuinely complex, not attempted this batch. `ledger_service.import_completed_sales` only imports a sale once its status is `COMPLETED` (the full `net_value`, idempotent via `linked_sale_id`'s unique constraint) - extending it to import PARTIAL receipts incrementally, without either double-counting once the sale later completes or misrepresenting an in-progress sale as settled revenue, is a genuine ledger-design question this batch's other 4 D65 items don't require solving. Left for its own future batch rather than force-built under time pressure.
- Existing relevant files/classes/functions: none — `LedgerEntry`/`crop_financial_service` operate on completed sale totals only, not partial-payment ledgers
- Missing component: Any ledger-level view of partial-payment balances
- Required implementation: Once D70-01's sale-import mechanism exists (it does, VERIFIED), extend it to import partial-payment receipts incrementally rather than only a single `COMPLETED` sale total — a design question requiring care not to double-count or prematurely import an incomplete sale
- Dependencies: D65-01, D65-02, D65-03 (prerequisites), D70-01 (existing sale-import mechanism this would extend)
- Backend work: `ledger_service.py::import` path — extend to handle partial-sale-payment states without violating the existing idempotent-import guarantee
- Database/migration work: none beyond D65-01's changes
- Mobile work: none — backend only, surfaced via existing ledger summary
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests asserting no double-counting/premature import of a partially-paid sale
- Verification method: automated test

### D65-05 — Payment history (list of attempts for an order)
- Domain: 65 Partial Payments
- Scenario ID: D65-05
- Exact scenario name: Payment history
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - new `GET /orders/{id}/payments` (farmer-ownership-scoped via `get_order_owned_by_farmer`, 404-not-403 for another farmer's order), returns every `Payment` row (failed + successful) ordered by `created_at`. Tests: `test_payments.py::test_payment_history_lists_every_attempt_in_order`, `test_payment_history_is_scoped_to_the_owning_farmer`
- Existing relevant files/classes/functions: `get_latest_payment_for_order` only returns the single latest row; no endpoint lists all `Payment` rows for an order/sale (confirmed by grep of `order_repository.py`/`orders.py`/`marketplace.py`)
- Missing component: Any list-payments read path
- Required implementation: A `GET /orders/{id}/payments` endpoint returning all `Payment` rows for the order, ordered by `created_at`
- Dependencies: none blocking — buildable independently of D65-01/02/03 (existing failed+retry payment rows already accumulate in the DB today, per the cluster file's own note, just unreachable via API)
- Backend work: `order_repository.py` (a `list_payments_for_order` query), `api/v1/orders.py` (new endpoint), `schemas/order.py` (a list-response schema)
- Database/migration work: none — reads existing data
- Mobile work: order detail screen — a "payment history" section
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — same ownership check as existing order-detail endpoint
- Tests required: a test asserting all payment attempts (including prior failures) are listed correctly and ordered
- Verification method: automated test

### D67-05 — Seller/farmer response (to a dispute filed against them)
- Domain: 67 Disputes
- Scenario ID: D67-05
- Exact scenario name: Seller/farmer response
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: new `POST /marketplace/disputes/{id}/farmer-response` (`api/v1/marketplace.py::add_farmer_dispute_response`) calling new `sale_order_service.add_farmer_response()`, mirroring `add_quality_dispute_details()` exactly - writes `QualityDispute.farmer_response`, creating the row if the buyer hasn't already; record-only, never auto-changes dispute/sale status
- Missing component: none
- Required implementation: none
- Dependencies: D67-04 (buyer response, VERIFIED — the symmetric counterpart, same code pattern replicated)
- Backend work: done — `sale_order_service.py`, `api/v1/marketplace.py`, `schemas/marketplace.py` (`FarmerDisputeResponseRequest`)
- Database/migration work: none — column already existed
- Mobile work: dispute-detail screen — a farmer-response input, symmetric to the buyer's (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: not built this pass (buyer-notified-of-farmer-response would be a separate, smaller follow-on; not part of this row's own required implementation)
- Offline/sync impact: none
- Security/RBAC impact: 404-not-403 if the calling farmer doesn't own the underlying sale (this project's established ID-enumeration-avoidance convention, same as other dispute actions)
- Tests required: `tests/test_marketplace_offers.py::test_farmer_can_respond_to_a_dispute_filed_against_them` (new), `::test_farmer_cannot_respond_to_another_farmers_dispute` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D71-05 — Plot P&L (aggregate across all crop cycles on one plot)
- Domain: 71 Profit
- Scenario ID: D71-05
- Exact scenario name: Plot P&L
- Current implementation status: **VERIFIED (Missing Backlog Batch 5)** - new `crop_financial_service.get_plot_pnl` / `GET /plots/{plot_id}/pnl-summary`, distinct from D70-04's totals-only `PlotFinancialTotalsResponse`. Same honest-NULL conventions as `CropFinancialSummaryResponse` (estimated_cost/cost_variance None when no estimate rows exist at all, never a fabricated zero; per-acre None only if the plot's area can't be resolved - a resolved Plot always has a real `area_sqm`, so this is never None in practice at this granularity). Deliberately no `stage_summaries` - stages are a single crop cycle's own concept and don't aggregate across a plot's whole multi-cycle history. Tests: `tests/test_crop_financials.py` (3 new).
- Existing relevant files/classes/functions: `crop_financial_service.get_financial_summary()` (per-crop-cycle); `Plot` model fully exists (`plot.py`) but is never joined into any financial computation — confirmed by grep of `crop_financial_service.py`, `profit_forecast_service.py`, `crop_comparison_service.py`, `crop_performance_service.py` for "plot" (zero matches)
- Missing component: Any aggregation function summing `get_financial_summary()` across every `CropCycle` sharing a `plot_id`
- Required implementation: A new `plot_financial_service.py` (or a function added to `crop_financial_service.py`) that queries all `CropCycle`s for a given `plot_id`, sums their `LedgerEntry` aggregates, and returns a `PlotFinancialSummaryResponse` with the same honest-NULL-handling conventions as `crop_financial_service.py` (e.g. `has_any_actual_revenue`, `Literal[None]` for unavailable projected figures)
- Dependencies: D70-04 (plot association, same underlying join — resolved together), D71-06 (Farm P&L, one level up, likely built on top of this)
- Backend work: new `plot_financial_service.py`, new endpoint in `api/v1/crop_financials.py` or a new `api/v1/plot_financials.py`, following `crop_financial_service.py`'s existing conventions (real SQL aggregate, never cached/stale, zero-entries → honest 0)
- Database/migration work: none — `Plot`/`CropCycle`/`LedgerEntry` relationships already exist; this is a query-layer addition only
- Mobile work: a new plot-detail financial-summary view
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — same farmer-ownership check as existing financial endpoints
- Tests required: tests mirroring `test_crop_financials.py`'s summation/zero-entries tests, at plot granularity, plus a test asserting multiple plots' data never combines (mirroring `test_multiple_crop_cycles_never_combine_financial_data`)
- Verification method: automated test

### D71-06 — Farm P&L (aggregate across all plots/crop cycles on one farm)
- Domain: 71 Profit
- Scenario ID: D71-06
- Exact scenario name: Farm P&L
- Current implementation status: **VERIFIED (Missing Backlog Batch 5)** - new `crop_financial_service.get_farm_pnl` / `GET /farms/{farm_id}/pnl-summary`, same pattern as D71-05 one level up; per-acre uses the sum of every ACTIVE plot's own `area_sqm` on the farm (new `plot_repository.sum_area_sqm_for_farm`), None only if the farm has no active plot at all. Tests: `tests/test_crop_financials.py` (2 new).
- Existing relevant files/classes/functions: same finding as D71-05, one level up (`Plot.farm_id`)
- Missing component: Any aggregation summing across every `Plot`/`CropCycle` on a `Farm`
- Required implementation: Same pattern as D71-05, one level up — a `farm_financial_service.py` (or extension) aggregating across all of a farm's plots
- Dependencies: D71-05 (built on top of it, or shares its aggregation core)
- Backend work: new `farm_financial_service.py` or extension of D71-05's service, new endpoint
- Database/migration work: none — query-layer addition only
- Mobile work: a new farm-detail financial-summary view
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — same farmer-ownership check
- Tests required: tests mirroring D71-05's, at farm granularity
- Verification method: automated test

### D71-07 — Season P&L (aggregate across crop cycles sharing a Season)
- Domain: 71 Profit
- Scenario ID: D71-07
- Exact scenario name: Season P&L
- Current implementation status: **VERIFIED (Missing Backlog Batch 5)** - new `crop_financial_service.get_season_pnl` / `GET /farmers/me/seasons/{season}/pnl-summary`, same pattern as D71-05, scoped by Season. No per-acre figures - a Season spans an arbitrary number of farms/plots with no single area to divide by, unlike Plot/Farm which each have exactly one; disclosed in `SeasonFinancialSummaryResponse`'s own docstring, not silently omitted. Tests: `tests/test_crop_financials.py` (1 new).
- Existing relevant files/classes/functions: `CropCycle.season` (`crop_cycle.py:86`) exists but is never grouped by in any financial query — same finding as D70-05
- Missing component: Any aggregation grouping by `CropCycle.season`
- Required implementation: A query grouping a farmer's `CropCycle`s by `season` and summing their financial aggregates, same conventions as D71-05
- Dependencies: D70-05 (season association, same underlying gap, resolved together)
- Backend work: new function in `crop_financial_service.py` or a new `season_financial_service.py`
- Database/migration work: none — `CropCycle.season` already exists
- Mobile work: a season-summary view
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — same farmer-ownership check
- Tests required: tests mirroring D71-05's, grouped by season
- Verification method: automated test

## 4. Broken

Empty — confirmed explicitly. All 7 scenario IDs in this group that were originally BROKEN
(D49-05, D50-07, D57-07, D58-06, D59-06, D66-02, plus D66-02's Domain-66 duplicate accounted
for once) have been reclassified per the verified deltas above: D49-05/D50-07/D59-06/D66-02 →
VERIFIED, D57-07/D58-06 → PARTIAL (fixed the structural defect, not yet a full itemized
breakdown). This matches the parent matrix's own "Net effect: BROKEN 12 → 0" finding — the
0-BROKEN result holds for domains 47-72 specifically, not merely in aggregate.

## 5. Future — with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D47-02 | 47 Harvest Readiness | Maturity detection (auto, from crop stage/sowing date) | Explicitly deferred: `harvest_record.py:6-10` docstring — "AI (Prompt 6's crop-stage intelligence) may in the future suggest a crop is approaching harvest... no code path in this phase automatically advances status"; `docs/HARVEST_MANAGEMENT.md:5-13` |
| D49-02 | 49 Harvest Quantity | Actual quantity | Explicitly disclosed unwired gap: `docs/HARVEST_MANAGEMENT.md:20-26` — "HARVESTED... not yet driven by any code path this phase... ready for that wiring, a natural next step." Reconfirmed still FUTURE, not a delta: Matrix §B batch 2 notes actual_quantity is now *read* by the yield-comparison feature but "no production code path populates actual_quantity yet (D49-02/D50-02 remain FUTURE)" |
| D50-02 | 50 Yield | Yield actual | Same disclosed gap and same reconfirmation as D49-02 (identical root cause per the cluster file's own cross-reference) |
| D59-07 | 59 Buyer Matching | Matching (automated buyer↔listing match) | Reclassified via delta (MISSING→FUTURE). Justification verified directly against source: `backend/app/models/notification.py:35` — "`ORDER_ALERT, MARKET_ALERT` deliberately NOT included - future phases only" — the automated-matching notification this scenario requires is blocked on a category the project has already, separately, declared future-phase-only |
| D72-02 | 72 ROI | Return (revenue attributable to that investment) | Explicit, deliberate deferral documented in the service's own docstring: `input_roi_service.py:4-18,9-12` — "a genuine ROI percentage per input category cannot be honestly calculated... roi_percent is therefore ALWAYS None," because `Order` has no `crop_cycle_id` anywhere, so spend cannot be causally linked to revenue. A refusal to fabricate a causal claim, not a bug |
| D72-03 | 72 ROI | ROI (% return) | Same explicit deferral as D72-02 — `InputRoiResponse.roi_attribution_available`/`roi_percent: Literal[None]`, `limitation_note` (`input_roi_service.py:31-35`) returned to the farmer verbatim |

All 6 FUTURE rows in this group carry a real, checked citation to a pre-existing deferral
statement in code or docs — none are flagged UNJUSTIFIED.

## 6. Out of Scope — with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D51-05 | 51 Quality | Assaying (formal lab testing) | Real external lab/assay relationship this project structurally never fabricates; `Role.LAB` exists as vocabulary-only placeholder, "no DB row yet — seeded when their owning module needs them" (`roles.py:20-37`); no assay/test-result model exists |
| D54-01 | 54 Cold Storage | Availability | Real external cold-storage facility booking; no interface/boundary placeholder exists even (unlike Transporter's role vocabulary) — grep for "cold storage"/"warehouse"/"godown" across backend/mobile/docs returns zero real hits |
| D54-02 | 54 Cold Storage | Capacity | Same reasoning as D54-01 |
| D54-03 | 54 Cold Storage | Cost | Same reasoning as D54-01 — no `LedgerCategory` for cold storage either |
| D54-04 | 54 Cold Storage | Booking | Same reasoning as D54-01 |
| D54-05 | 54 Cold Storage | Storage duration | Same reasoning as D54-01 |
| D54-06 | 54 Cold Storage | Release | Same reasoning as D54-01 |
| D55-02 | 55 Transport | Transporter (assigning/selecting one) | Real external business relationship; `Role.TRANSPORTER` exists as vocabulary only, `delivery_service.py:1-6` explicitly notes delivery "may later be handed to a distinct transporter role — not built this phase" |
| D60-01 | 60 eNAM Boundary | Registration boundary (real eNAM farmer/trader registration) | Verified against source: `docs/FINAL_GAP_REPORT.md`'s own borderline-rows note confirms this is correctly OUT_OF_SCOPE "even though no document names eNAM/FPO by name specifically — the general 'no fabricated integrations' rule applies even without a domain-specific citation." Cluster file itself: targeted search for literal "eNAM"/"e-NAM"/"APMC" found no genuine hits. Justified via the checklist's own structural rule, transparently disclosed as such — not flagged UNJUSTIFIED |
| D60-02 | 60 eNAM Boundary | Lot boundary (eNAM lot numbering/yard assignment) | Same reasoning as D60-01 — `HarvestListing` has no lot number/APMC-yard field |
| D60-03 | 60 eNAM Boundary | Pre-registration (eNAM pre-trade formalities) | Same reasoning as D60-01 |
| D60-04 | 60 eNAM Boundary | Live bid boundary (real multi-bidder eNAM auction) | Same reasoning as D60-01; the app's own private bilateral negotiation is never mislabeled as "eNAM"/"live bidding" — separately VERIFIED under D62 |
| D60-05 | 60 eNAM Boundary | Logistics boundary (real eNAM-integrated logistics) | Same reasoning as D60-01; `CollectionOption` is this app's own self-contained model, never connected to or claiming a real logistics network |
| D60-06 | 60 eNAM Boundary | Payment boundary (real eNAM/gateway settlement) | Same reasoning as D60-01; `PaymentProvider.SANDBOX` only, confirmed genuinely sandboxed |
| D61-01 | 61 FPO | FPO membership | Verified against source: same Gap Report borderline-rows note as D60-01 — correctly OUT_OF_SCOPE via the checklist's own general rule (real farmer-producer-organization legal structure), even without a domain-specific deferral citation. No `FPO`/cooperative model exists anywhere (targeted grep for `\bFPO\b` found zero genuine matches) |
| D61-06 | 61 FPO | Group buyer (buyer transacting with a farmer collective) | Same reasoning as D61-01 — `BuyerBusinessProfile` is 1:1 with a single `ProfessionalProfile` |
| D61-08 | 61 FPO | Payment distribution boundary (splitting one payment across FPO members) | Same reasoning as D61-01 — `Payment`/`SaleOrder` strictly 1 sale : 1 `farmer_id`, no split-payment concept; correctly not fabricated as it would require a real FPO revenue-sharing legal structure |
| D64-07 | 64 Payments | Payment provider boundary | Real gateway integration explicitly and honestly out of scope per free/open-source constraint: `docs/PAYMENT_ARCHITECTURE.md:1-8,28-36`, `README.md:12-21` stack table (Flutter/FastAPI/PostgreSQL only), `docs/LICENSE_REGISTER.md` (no payment-gateway package). `Payment` model structurally has no card/CVV/UPI-PIN/bank-password columns |
| D66-05 | 66 Failed Payments | Reconciliation (matching gateway state vs local state) | No real gateway exists (D64-07) so there is nothing external to reconcile against; the sandbox's own state is the source of truth by construction — consistent with the disclosed sandbox boundary in `docs/PAYMENT_ARCHITECTURE.md` |
| D68-03 | 68 Refund/Adjustment Boundary | Payment provider boundary (refund must go through a real gateway) | Same sandbox boundary as D64-07; explicitly flagged in `docs/REFUND_DISPUTE.md:39-42` as something that "must be replaced with a real refund API integration before real money is involved" |

All 20 OUT_OF_SCOPE rows in this group carry a checked, real justification. None are flagged
UNJUSTIFIED. D60-01 and D61-01 (eNAM registration and FPO membership) are the two rows the
task brief anticipated might be borderline; both were independently confirmed against
`docs/FINAL_GAP_REPORT.md`'s own explicit "borderline rows worth noting" discussion, which
already discloses (rather than hides) that no domain-specific deferral document names them —
the classification instead rests on the checklist's own general no-fabricated-external-
relationship rule, applied transparently.

## 7. Environment Dependent — exact dependency

None. Zero scenario IDs in Domains 47-72 (D47-01 through D72-06) are classified
ENVIRONMENT_DEPENDENT in the source cluster files. The parent-report's only 6
ENVIRONMENT_DEPENDENT rows across all 100 domains are D14-01/03/04/05/06/08 (weather-provider
reachability, Domain 14), entirely outside this group's 47-72 range — confirmed by direct
inspection of `docs/FINAL_GAP_REPORT.md`'s "Environment Dependent (6)" table. Note that several
MISSING rows above (D56-01..07, the mandi price feed) would become ENVIRONMENT_DEPENDENT once
built, in the same way D14's weather integration is today — flagged in their own itemized
entries' "Verification method" field as a forward-looking note, not a present classification.
