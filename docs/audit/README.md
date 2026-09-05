# Smart Farmer V3 — Real-World Scenario Audit (2026-09-04)

Full audit of the 100-domain, 300+-scenario checklist supplied by the user
against the actual repository, run as 13 parallel research passes (one per
cluster of related domains). Every finding below is grounded in file:line
citations and, where applicable, actual test runs — not inferred from
feature names or documentation alone.

## Methodology

Each of the 9 status values is mutually exclusive and was applied per
individual scenario, not per domain:

- **MISSING** — no code implements this at all.
- **PARTIAL** — some code exists but doesn't cover the full scenario.
- **BROKEN** — code exists but is demonstrably incorrect/non-functional.
- **IMPLEMENTED** — code fully covers the scenario, but no automated test
  specifically asserts it.
- **VERIFIED** — code fully covers the scenario AND a passing automated
  test (or a live session verification) specifically asserts it.
- **COMPLETE** — reserved but unused as a distinct bucket (auditors were
  instructed to use VERIFIED instead, to avoid double-counting); always 0.
- **FUTURE** — explicitly, deliberately deferred, with a citation to where
  the project already documented that decision.
- **OUT_OF_SCOPE** — requires a real external business/legal/regulated
  relationship this project structurally never fabricates (a real payment
  gateway, insurance underwriting, eNAM registration, a government scheme
  portal, satellite/IoT hardware). Only an interface/boundary may exist.
- **ENVIRONMENT_DEPENDENT** — code is correct/complete, but real-world
  behavior in this specific dev environment depends on something this
  session/machine lacks (e.g. no non-English TTS voice installed, no
  Android device/emulator).

Totals below were computed **mechanically** (a script parsing every table
row's Status cell across all 13 files), not hand-tallied from each
sub-agent's own prose summary, to avoid transcription drift at this scale.
`c01_foundation.md` was re-parsed a second time after its authoring agent
reported a late race condition (its own spawned helper had briefly
overwritten the file); the numbers below reflect that final, verified
version.

## Final reconciled totals

| Status | Count |
|---|---|
| VERIFIED | 223 |
| IMPLEMENTED | 63 |
| COMPLETE | 0 |
| PARTIAL | 119 |
| MISSING | 321 |
| BROKEN | 12 |
| FUTURE | 29 |
| OUT_OF_SCOPE | 25 |
| ENVIRONMENT_DEPENDENT | 6 |
| **TOTAL** | **798** |

(223+63+0+119+321+12+29+25+6 = 798, verified by script — reconciles exactly.)

**Why 798, not "300+":** the supplied checklist's 100 domains expand to
this many individual scenarios once every bullet is treated as its own
row, per the instructions. This is consistent with, not a deviation from,
"300+" as a floor.

## Automation coverage (BV-2) — honestly not computed this pass

The requested `Automatic / Manual / Hybrid / Safety-confirmation workflow`
breakdown and automation-coverage percentage could **not** be reliably
computed by mechanical parsing: the 13 sub-agents used slightly different
column layouts (embedded citations pushed some rows to 16–22 columns
instead of the specified 17), so positionally extracting the Trigger /
Automatic Action columns across all 798 rows was not trustworthy. Rather
than publish a fabricated percentage, this is flagged as a distinct
follow-up pass (a second mechanical script keyed to each file's own
header, or a targeted per-domain re-read) — not silently dropped.

## The 7 distinct real bugs found (BROKEN, not just missing)

These are genuine defects — existing, tested-looking code that is
demonstrably wrong — found across 5 separate areas. Full citations are in
the linked files; short list:

1. **Password reset has no identity verification** beyond a phone number
   (`c01_foundation.md` D1-18) — already self-documented in
   `docs/SECURITY.md:203-205` as a known account-takeover gap.
2. **`harvest_service.confirm_ready()` has no status guard** (`c08` D49-05/
   D50-07) — re-calling it to correct a quantity silently regresses an
   already-`LISTED`/`HARVESTED` record back to `READY`.
3. **"Net realization" is fake** (`c09` D57-07/D58-06) — `offer_service.py`
   hardcodes transport/commission/storage charges to `Decimal("0")`, so the
   figure presented as a real net-of-costs number can never differ from
   the gross sale value.
4. **Offer expiry is dead code** (`c09` D59-06) — `BuyerOffer.valid_until`
   and `OfferStatus.EXPIRED` exist but nothing ever checks them; a farmer
   can accept an offer after it's supposed to have expired.
5. **Payment retry is blocked** (`c10` D66-02) — the status transition map
   only allows `PAYMENT_PENDING → {PAID, CANCELLED}`, so a second `/pay`
   call after a failure gets rejected with a 409, with no path to retry.
6. **Inconsistent auth-expiry handling during photo upload** (`c12` D84-02)
   — the foreground upload path never checks for a 401, unlike the
   background sync path, so it misclassifies an expired session as a
   plain retryable network failure.
7. **Dead-letter sync items can never be revived** (`c12` D84-04/D87-04/
   D87-05/D87-06) — a code comment promises a "manual retry UI path" that
   doesn't exist anywhere; once an item hits `authenticationRequired` or
   `retriesExhausted`, it is permanently stuck with zero farmer or admin
   visibility.

**Post-audit status (2026-09-05):** all 7 are now fixed and tested; the
table rows above are left as originally written (this is a point-in-time
snapshot, not re-parsed) rather than hand-edited out of the mechanically-
verified totals. Bug 1 specifically required a real product decision this
audit deliberately did not make unilaterally (see "What happens next"
below) — it's closed via a real Twilio Verify OTP check gating
`/auth/reset-password` (see `docs/SECURITY.md`'s "Password reset" section
and `app/services/sms/`), on explicit instruction to wire up a real SMS
provider rather than a free/no-OTP alternative.

All 7 are safely fixable now — none require a new external
provider/business decision. **Next: implementing these fixes with tests.**

## Cross-cutting architectural findings (not single bugs, but systemic)

- **No scheduler/cron/background worker exists anywhere in this project**
  (confirmed independently by the weather and expert-network audits) —
  this is *why* weather alerts are pull-only and Expert SLA timeouts/
  reminders never fire, not two separate gaps.
- **`notification_service` is never invoked from marketplace, sale,
  order, or payment code** — confirmed by grep. Only expert-case and
  weather flows notify farmers today.
- **Offline/sync is 100% scoped to crop-photo uploads** — Farms, Plots,
  Crops, Tasks, Expenses, Harvest records, and Notes have zero offline
  queueing capability.
- **Everything financial is scoped to a single crop cycle** — no Plot/
  Farm/Season-level profit rollup or cost-per-acre exists, despite
  `Plot.area_value` being available to join against.
- The strongest, most rigorously tested areas in the whole app are:
  the crop-cycle/harvest/sale/order state machines, the Ledger + Invoice
  OCR + Cost Estimate + Profit Forecast system (Phases 29-32), the AI
  disease-detection pipeline's architecture (real provider abstraction,
  tested against a fake provider), and Security/RBAC/tenant isolation.
- Entirely and honestly absent, confirmed by exhaustive grep, not
  assumption: Government Schemes, Crop Insurance, Satellite, IoT, real
  Machinery/Labour marketplaces, Community/discussion features, Storage/
  Cold-Storage logistics, and a real crop-selling market-price feed.

## Cluster files (full 798-row detail, evidence-cited)

| File | Domains |
|---|---|
| [c01_foundation.md](c01_foundation.md) | 1-8: Account, Farm, Plot, Crop, Variety, Cycle, Stages, Calendar |
| [c02_lifecycle_edgecases.md](c02_lifecycle_edgecases.md) | 9-13, 99: Task Automation, Crop Failure, Re-sowing, Intercropping, Perennial, Special Scenarios |
| [c03_weather_water_soil.md](c03_weather_water_soil.md) | 14-20: Weather, Weather Risk, Weather Automation, Water, Irrigation, Soil, Soil Testing |
| [c04_inputs.md](c04_inputs.md) | 21-26: Seeds, Fertilizer, Crop Protection, Input Inventory, Purchase, Verification |
| [c05_disease_ai.md](c05_disease_ai.md) | 27-32: Disease, Pest, AI Diagnosis, Image Quality, AI Confidence, Unknown Diagnosis |
| [c06_expert_network.md](c06_expert_network.md) | 33-39: Expert Escalation, Assignment, SLA, Recommendation, Recommendation→Task, Follow-up, Reinspection |
| [c07_voice_language_community.md](c07_voice_language_community.md) | 40-46: Voice, Local Language, Education, Community, Nearby Services, Machinery, Labour |
| [c08_harvest_postharvest.md](c08_harvest_postharvest.md) | 47-55: Harvest Readiness, Planning, Quantity, Yield, Quality, Post-Harvest, Storage, Cold Storage, Transport |
| [c09_market_sales.md](c09_market_sales.md) | 56-63: Market Prices, Comparison, Net Realization, Buyer Matching, eNAM, FPO, Sales, Orders |
| [c10_payments_finance.md](c10_payments_finance.md) | 64-72: Payments, Partial/Failed Payments, Disputes, Refund Boundary, Expenses, Revenue, Profit, ROI |
| [c11_schemes_insurance_disaster_satellite_iot.md](c11_schemes_insurance_disaster_satellite_iot.md) | 73-77: Gov Schemes, Crop Insurance, Disaster Management, Satellite, IoT |
| [c12_notifications_offline_sync.md](c12_notifications_offline_sync.md) | 78-87: Notifications, Dedup, Priority, Offline, Sync, Retry, Auth Expiry, Conflict Resolution, Idempotency, Dead-letter |
| [c13_governance_farmbrain_security.md](c13_governance_farmbrain_security.md) | 88-98, 100: Data Provenance, Rule Versioning, Provider Abstraction, AI Governance, Farm Brain, Daily Brief, What Changed, Risk Dashboard, Season Comparison/Closure, Historical Learning, Security/Privacy/Audit |

## What happens next

Per the requested process (AUDIT → GAP MATRIX → IMPLEMENT → TEST →
RE-AUDIT), the 7 bugs above are being fixed now — they're safe, scoped,
and need no new product/business decision. The 318 MISSING and 123
PARTIAL scenarios are not being bulk-implemented blindly: many require
real decisions only the product owner can make (which payment provider,
whether to pursue insurance/eNAM/satellite integration, whether to build
a Machinery/Labour marketplace, etc.) — those will be brought back as a
prioritized list for explicit sign-off rather than built speculatively.

## Second pass (2026-09-05): Expert SLA automation (P0 cluster)

Per that prioritized-list plan, the priority columns across all 13 files
were mechanically re-extracted and normalized (the 13 sub-agents had used
inconsistent P0-P3 vs. Critical/High/Medium/Low labels). After
normalization, only **8 scenarios were genuine P0/CRITICAL** (safety,
data-loss, security, or financial-correctness class) — everything else in
the 318 MISSING / 119 PARTIAL backlog was Medium/Low/P2/P3, or one of the
six entirely-absent domains (Govt Schemes, Crop Insurance, Satellite,
IoT, live eNAM bidding, real Machinery/Labour/Community marketplaces)
that the product owner explicitly chose to leave FUTURE/OUT_OF_SCOPE
rather than build interface-only stubs for in this pass.

All 8 P0 items traced to **one root cause: no scheduler/background-job
system existed anywhere in the project** (the same gap this README's
"Cross-cutting architectural findings" section already flagged for
weather push and Expert SLA timeouts). That gap is now closed:
`backend/app/services/scheduler.py` (APScheduler, MIT license, in-process
— see docs/LICENSE_REGISTER.md) runs `case_sla_service.run_case_sla_sweep`
on a 5-minute interval (configurable, disabled in the `testing`
environment). Per-scenario evidence (all in `c06_expert_network.md`
unless noted):

| ID | Scenario | Was | Now | Evidence |
|---|---|---|---|---|
| D34-03 | Reassignment (timeout path) | PARTIAL — only decline-triggered reassignment worked | VERIFIED | `case_sla_service._expire_reassign_or_escalate` re-invokes `case_service._try_auto_assign`, excluding the non-responder (`case_repository.get_excluded_professional_ids` already excluded EXPIRED). `tests/test_case_sla_service.py::test_sweep_expires_stale_assignment_and_reassigns_excluding_the_non_responder` |
| D35-02 | SLA monitoring | MISSING — no background job of any kind | VERIFIED | `scheduler.py` + `case_sla_service.run_case_sla_sweep` read `CaseAssignment.expires_at` every tick |
| D35-03 | Reminder | MISSING | VERIFIED | `case_sla_service._send_expiry_reminders`, `CASE_ASSIGNMENT_REMINDER` message key (`farmer_messages.py`), deduplicated per-assignment. `test_sweep_sends_one_reminder_before_expiry_and_never_duplicates` |
| D35-04 | Escalation on SLA breach | MISSING | VERIFIED | After `case_sla_max_reassignment_attempts` (default 2) timeouts, case → `ESCALATED`, `CASE_SLA_BREACH_ESCALATED` audit entry, CRITICAL notification. `test_sweep_escalates_after_repeated_timeouts_with_critical_notification` |
| D35-05 | Expert unavailable | PARTIAL — no automatic detection | VERIFIED (case-level scope) | A non-responding professional is detected via expiry and permanently excluded from that case's reassignment pool; a project-wide `availability_status` flip was deliberately NOT added — a professional-facing side effect like that needs its own confirmation/appeal path, out of scope for this pass |
| D38-06 | Follow-up escalation | MISSING | VERIFIED | `case_service.escalate_case_for_worsened_treatment` (`treatment_service.py`'s `get_effectiveness`), idempotent, CRITICAL notification. `tests/test_treatments.py::test_worsened_outcome_with_linked_case_auto_escalates`, `::test_worsened_outcome_escalation_is_idempotent` |
| D39-07 | Reinspection → expert escalation | MISSING | VERIFIED (same fix as D38-06) | Same evidence; when no case is linked yet, `recommended_action="request_expert_review"` guides the farmer to the existing consent-gated `POST /cases` flow rather than a case being silently created. `test_worsened_outcome_with_no_linked_case_recommends_expert_review` |
| D80-01 (`c12_notifications_offline_sync.md`) | CRITICAL notification priority reachable | PARTIAL — mechanism implemented but unreachable | VERIFIED | Both escalation paths above use `NotificationPriority.CRITICAL`; verified by asserting `priority == "critical"` in the treatment and SLA sweep tests |

Full backend suite after this pass: **633/633 passed** (was 611 at the
first audit's snapshot date — the difference includes these new tests
plus unrelated work between the two dates). `docs/CASE_MANAGEMENT.md` and
`docs/NOTIFICATION_ARCHITECTURE.md` were updated in place (not as a
frozen snapshot, since they are living architecture docs, not audit
tables) to remove the now-stale "no background scheduler" disclosures.

**Delta against the original totals table above:** 8 rows move to
VERIFIED (5 previously MISSING: D35-02/03/04, D38-06, D39-07; 3
previously PARTIAL: D34-03, D35-05, D80-01). This addendum does NOT
re-publish a corrected 798-row reconciliation — a second, independent
mechanical extraction pass (done to find and normalize the P0/High/Medium
priority labels for this session) produced slightly different MISSING/
PARTIAL counts (318/123) than the table above (321/119) even before any
code changed, which means the original per-file tables likely already
had 2-4 rows whose status text didn't cleanly match a single bucket on
re-parse (e.g. compound cells like "MISSING (feature itself); ... IMPLEMENTED").
That pre-existing small discrepancy is disclosed here rather than papered
over with new arithmetic; the 8 VERIFIED-now rows above are each
individually citation- and test-backed regardless of it. A follow-up pass
should re-run the ORIGINAL per-file mechanical parser against the
now-updated files before the next scope decision, to restore one
authoritative total.

**Scope explicitly not attempted this pass** (by the product owner's own
choice, not oversight): the ~82 remaining High/P1-tagged scenarios across
the other 12 clusters, and the six FUTURE/OUT_OF_SCOPE domains (Govt
Schemes, Crop Insurance, Satellite, IoT, live eNAM bidding, real
Machinery/Labour/Community marketplaces). No mobile/Flutter changes were
made this pass — the Expert SLA and treatment-escalation notifications
surface through the existing generic in-app notification list, which
already renders arbitrary categories/priorities; no crop-photo-effectiveness
UI (e.g. surfacing `recommended_action`) was added.

## Third pass (2026-09-05, continued): High/P1 backlog — batch 1 & 2

Starting on the ~82-row High/P1 backlog (product owner asked to continue
past the P0 cluster). Given how heterogeneous this backlog is (12
different clusters, many unrelated to each other, unlike the P0 cluster's
single root cause), work proceeds in coherent batches rather than one
pass — each batch fully audited, implemented, tested, and recorded here
before moving to the next.

### Batch 1 — Daily Farm Brief aggregation (7 rows, `c13_governance_farmbrain_security.md`)

D92-01/02/06/08 and D93-01/04/09 all pointed at one function,
`assistant_extras_service.get_daily_summary()`, which already composed
weather/crop/harvest/marketplace/delivery/expert-case/overdue-task lines
but never called `crop_risk_service.get_risk_score`,
`tools.get_disease_status`, or `crop_financial_service.get_financial_summary`
— all three already existed and were already tested elsewhere. Now added,
each following the summary's own "only report what's actually there"
discipline: disease only surfaces on a genuine `disease_detected` result;
risk only surfaces at medium/high (never low/insufficient_data noise);
finance only surfaces once something has actually been spent. 3 new
`daily_summary_*` message keys added in all 7 already-supported languages
(matching this specific key family's existing full-translation
convention — unlike the CASE_*/assistant_* key families elsewhere in the
same file, which are deliberately English-only pending native-speaker
review; these 3 follow the same mechanical, not-independently-reviewed
convention already established for their 7 sibling `daily_summary_*`
keys). Verified: `tests/test_assistant_chat.py::test_daily_summary_includes_disease_and_risk_lines_when_disease_detected`,
`::test_daily_summary_includes_finance_line_once_expenses_recorded`.

### Batch 2 — Yield in season comparison & learning (2 rows)

D96-03 (`crop_comparison_service.compare_crop_cycles`) and D98-02
(`learning_foundation_service.get_learning_summary`) both wanted
`HarvestRecord.actual_quantity` wired into comparison/learning outputs.
Both now sum/read `actual_quantity` correctly, guarded to report
`insufficient_data`/`None` (never a fabricated zero) when absent.

**Important finding, disclosed rather than hidden:** while implementing
this, `grep -rn "actual_quantity" app/` confirmed `c08_harvest_postharvest.md`'s
own D49-02/D50-02 finding — **no service function anywhere in the entire
backend ever writes `HarvestRecord.actual_quantity`**. It is declared on
the model, read by `profit_forecast_service.py`, and now also read by
this pass's two fixes, but there is no "mark harvested with an actual
quantity" endpoint at all. D49-02/D50-02 are correctly marked **FUTURE**
in `c08` (disclosed at `docs/HARVEST_MANAGEMENT.md:20-26`) — but tagged
**Critical** priority, a combination worth the product owner's attention:
these two "High" fixes are code-correct and tested (via direct DB
insertion simulating the future write path — see
`test_comparison_correctly_identifies_higher_yield_once_harvest_quantities_exist`),
but **produce zero visible farmer value today** since the field they
depend on is never populated through any reachable flow. This is not a
new gap introduced by this pass — it is the same disclosed FUTURE item,
surfaced here because two unrelated High-priority fixes turned out to be
silently blocked by it.

Full backend suite after batches 1-2: **637 passed, 1 error** (the error,
`test_ai_analysis_security.py::test_farmer_a_cannot_analyze_farmer_bs_photo`,
does not reproduce in isolation — 6/6 pass standalone — and is unrelated
to any file this pass touched; pre-existing full-suite flakiness, not a
regression).

### Batch 3 — Farmer Input Inventory (9 of 11 rows, `c04_inputs.md`)

Unlike batches 1-2 (wiring already-existing services together), this
cluster's dominant gap was a genuinely missing feature: 9 of 11 rows
(D21-06, D22-04, D22-06, D23-05, D24-01, D24-02, D24-05, D24-08, D24-09)
all trace to the same root cause — **no farmer-side input inventory
existed anywhere** (`DealerProduct.stock_quantity` is the dealer's
sellable stock; nothing tracked what a farmer actually holds). Per the
product owner's explicit choice (asked directly given the size of this
one), built as a new feature rather than deferred:

- New model `InputInventoryItem` + migration `fb6859bdd48d` (table +
  a new `NotificationCategory.STOCK_ALERT` enum value).
- `app/services/input_inventory_service.py`: create, list, get, record
  usage (decrements, rejects usage greater than remaining), restock
  (increments), and an audited quantity correction (a free-text reason
  required).
- Low-stock alert (D22-06/D24-08): fires once per "episode" via a
  `low_stock_alerted_at` gate — not just the Notification table's own
  dedup_key — so repeated usage calls while still low don't spam, but
  restocking above threshold and dropping low again correctly re-alerts.
- Expiry warning (D24-09): a **second** scheduler job
  (`input_inventory_expiry_sweep`, hourly by default) alongside the P0
  pass's Expert SLA sweep — proactive, not farmer-screen-triggered,
  skips already-depleted items, gated by `expiry_alerted_at`.
- Full API: `POST/GET /input-inventory`, `GET /input-inventory/{id}`,
  `POST .../usage`, `POST .../restock`, `POST .../correct`. Ownership
  enforced (cross-farmer access → 404).
- Documented in `docs/INPUT_INVENTORY.md`. 14 new tests
  (`tests/test_input_inventory.py`), all passing.

**Two rows in this cluster needed no change:** D22-07 (expired-listing
checkout block) was already VERIFIED with its own test; its previously-noted
"no proactive expiry warning" gap is exactly what D24-09 above now closes.
D26-04 (product authenticity/counterfeit verification) remains
**correctly MISSING, not built** — no QR/barcode/manufacturer-registry
integration exists anywhere in this project
(`docs/PROMPT9_ASSUMPTIONS_RISKS.md:80-89` already discloses this), and
per this project's explicit "never fabricate a provider integration"
rule, a real authenticity claim requires a real external registry this
pass does not invent.

**Explicitly deferred, disclosed rather than silently skipped:**
automatic "purchase → stock increase" (marketplace order delivery does
not yet auto-create/restock an inventory row) — inventory creation and
restocking are farmer-initiated only this phase, using the same
functions a future automatic hook would call.

Full backend suite after batch 3: **652 passed, 0 errors** (the batch
1-2 flaky error did not reproduce this run).

### Batch 4 — Crop Failure & Re-sowing (7 of 9 rows, `c02_lifecycle_edgecases.md`)

D9-15, D10-01, D10-02, D10-03, D10-09, D10-10, D11-01 addressed together
as one coherent feature (D99-01/D99-02 are cross-reference rollups of
these same rows, not independently actionable):

- **D9-15 (orphaned tasks):** `task_service.cancel_all_pending_for_crop_cycle`
  now runs whenever a crop cycle reaches CANCELLED or HARVESTED (both
  `update_my_crop_cycle` and `close_my_crop_cycle`) - a PENDING task tied
  to an ended cycle no longer inflates the overdue-task count or the Crop
  Risk Score's "Operational Task Risk" factor forever. Cancelled, not
  deleted.
- **D10-01/D10-02/D10-03 (failure reporting + reason taxonomy):** new
  `POST /crops/{id}/report-failure` (`CropCycle.failure_reason`, a
  `FailureReason` enum: disease/pest/drought/flood/weather_damage/
  market_conditions/other), distinct from the pre-existing generic `PUT`
  cancel - a plain "changed my mind" cancel leaves `failure_reason` null,
  so a reported failure stays traceably different.
- **D10-09/D11-01 (recovery/re-sow recommendation):** `report_crop_failure`
  returns a `recommended_next_action` - category-driven, still
  deliberately generic/non-prescriptive (no product, dosage, or variety
  name), consistent with `crop_risk_service._build_recommendation`'s own
  convention, which was intentionally NOT modified.
- **D10-10 (re-sowing linkage):** `CropCycleCreateRequest.resown_from_crop_cycle_id`
  (optional) links a new cycle back to the cancelled one it replaces -
  validated to be the farmer's own, CANCELLED, and on the SAME plot.

Migration `d7557ced4b7b`. 9 new tests in `tests/test_crop_cycles.py`.
Full suite: **660 passed, 1 failed** — the failure,
`test_products.py::test_admin_can_list_pending_products_to_discover_what_needs_review`,
passes 11/11 in isolation and touches code this batch never modified
(products/admin listing pagination against the shared, accumulating test
database) - pre-existing full-suite-scale flakiness, not a regression
(this is the third distinct pre-existing flaky test observed across the
three full-suite runs so far this session, each unrelated to the files
changed in its own run - worth a dedicated look eventually, but out of
scope for this backlog pass).

**Not built this batch, disclosed:** automatic reason detection (e.g.
auto-inferring "disease" from a recent AI diagnosis rather than the
farmer selecting it) - `failure_reason` is farmer-selected only; and no
notification is sent for the recovery recommendation (it's a synchronous
response field on the report-failure call, not a proactive alert).

### Batch 5 — Expert case routing/escalation (4 of 11 rows, `c06_expert_network.md`)

D33-02, D34-01, D33-06, D36-02 fixed. Three rows deliberately NOT
"fixed," with reasoning (not silently skipped):

- **D31-05/D32-05 (AI low-confidence/unknown should auto-open a case):**
  on inspection this is the CORRECT existing design, not a gap - creating
  a case shares the farmer's photo with a professional, and this
  project's own `CaseConsent`-before-sharing rule means that requires the
  farmer's explicit action. The farmer IS already proactively prompted
  (`ai_next_action_review` message, wired via `ai_result_localization_service.py`) -
  automating the case-creation step itself would remove a real consent
  boundary, not close a gap. Left as PARTIAL-by-design.
- **D28-03/D28-04/D29-05 (pest detection):** confirmed the model provider
  abstraction has no pest/disease distinction at all (`predict_disease`
  returns arbitrary `class_name` strings with no category signal) -
  building this would mean guessing which class names are "pest" via a
  hardcoded lookup table, which is fabricating a distinction the model
  itself doesn't make. Left MISSING, requires a real model capability
  this project doesn't have, not an oversight.
- **D37-01/D37-02/D37-04 (Recommendation -> Task) and D38-01/D38-02
  (scheduled follow-up date + reminder):** genuinely buildable, but each
  is its own small feature (Task needs a `case_id`/`treatment_id` FK it
  doesn't have; a scheduled-follow-up date is a new concept distinct from
  `observation_date`) - deferred to a future batch rather than rushed
  into this one.
- **D34-04 (no professional-facing mobile UI):** out of scope for this
  backend-only pass, as previously established.

Fixes:
- **D33-02:** `case_service._build_match_criteria` now actually resolves
  crop_id (from the case's crop cycle), farmer language, and state/district
  (from the farm's location) into `MatchCriteria` - previously only
  `role` + exclusions were ever populated, so real scoring logic in
  `nearby_professional_service.py` was dead weight. `disease_category` is
  deliberately still unpopulated (same reasoning as the pest-detection
  item above - no real taxonomy exists on `AIAnalysis` to draw from).
- **D34-01:** OFFLINE professionals are now a hard exclusion in
  `find_ranked_candidates`, not just a zero score - previously an OFFLINE
  professional could still win and be auto-assigned if ranked
  highest/sole candidate.
- **D33-06:** a `field_visit_required` review outcome now logs a distinct
  `CASE_ESCALATED` audit action and sends a distinct HIGH-priority
  notification, instead of silently reusing the generic `CASE_REVIEWED`
  path. Real auto-reassignment to a different/senior professional was
  deliberately NOT added - what that would concretely mean is undesigned.
- **D36-02:** `GET /cases/{id}` (the single-case farmer detail view) now
  returns `latest_review_notes` - previously the farmer-facing
  `CaseResponse` had no field to surface a professional's explanation at
  all, despite it being stored (`CaseReview.notes`).

**A real test-contamination bug found and fixed while writing tests for
this batch:** the test database is a real, persistent Postgres instance
- rows are never rolled back, not between tests, and not between
separate `pytest` invocations. An early draft of
`test_crop_specialization_match_is_preferred` gave a test professional a
permanent crop-match scoring advantage for Tomato (`sample_crop_id`,
the crop nearly every test in this suite uses) and left it AVAILABLE -
this silently hijacked auto-assignment away from unrelated tests'
own fixture-created professionals across the whole suite, breaking 10
tests in `test_cases.py` that assumed their own professional would be
the one auto-assigned. Fixed two ways: (1) every test professional that
could bias future routing now flips itself OFFLINE in a `finally` block
before the test ends (harmless afterward, per D34-01's hard exclusion);
(2) the shared test database itself was directly remediated (7 leftover
"specialist" rows and 4 leftover available `field_agent` rows from this
debugging process, set OFFLINE) since code fixes alone don't undo rows
already committed by earlier interrupted runs. Verified stable across
two repeated full runs of the affected files after the fix.

New test file `tests/test_case_routing_and_escalation.py` (9 tests). Full
suite: **666 passed, 0 failed.**

### Batch 6 — Market/Sales (1 of 11 rows fixed, 6 more reclassified with reasoning, `c09_market_sales.md`)

This cluster turned out to be mostly items that should NOT be silently
built, once actually investigated - not oversight, but genuine
boundaries:

- **D59-03 (buyer's own min/max quantity never cross-checked) - FIXED.**
  `offer_service.create_offer` now rejects (422) an offer whose quantity
  falls outside the buyer's own registered `BuyerBusinessProfile.min_quantity`/
  `max_quantity`, when set. 3 new tests in `tests/test_marketplace_offers.py`.
- **D57-04/D57-05/D58-02/D58-03 (transport/commission deduction) -
  STALE EVIDENCE, already fixed before this session.** The audit's own
  citation (`offer_service.py:123` hardcoded `Decimal("0")`) predates
  this session entirely - `AcceptOfferRequest.charges` is already a real,
  farmer-entered deduction (part of the original 7-bug fix pass, see this
  file's "Post-audit status" section from 2026-09-05). What remains is
  only a cosmetic itemization gap (`charges` is one lump sum, not broken
  into separate transport/commission/storage fields) - the underlying bug
  ("net realization structurally incapable of differing from gross") is
  resolved, not this specific itemization.
- **D56-01/02/03/04 (live mandi/APMC prices), D57-01 (multi-market
  registry) - correctly MISSING, requires a product decision.** No live
  market-price data exists in this project at all (`market.py` is an
  intentional empty placeholder). A free government API exists in
  principle (data.gov.in / Agmarknet), but building the provider
  abstraction now would only ever return "unavailable" without a real,
  user-provided API key - not attempted this pass, flagged for the
  product owner rather than built as an always-empty shell.
- **D59-07 (automatic buyer<->listing match notification) -
  RECLASSIFIED MISSING -> FUTURE.** The audit missed a directly relevant,
  already-disclosed decision: `NotificationCategory`'s own code comment
  states `"ORDER_ALERT, MARKET_ALERT deliberately NOT included - future
  phases only"` (`app/models/notification.py`). Building automated
  marketplace-match notifications now would directly contradict that
  already-made, disclosed scope decision - this is not an oversight to
  silently fix, it's a decision to respect or explicitly revisit with the
  product owner.

Full suite: **669 passed, 0 failed.**

### Batch 7 — Proactive weather push + harvest notifications (2 rows, `c03_weather_water_soil.md` + `c08_harvest_postharvest.md`)

- **D16-10:** a new scheduler job (`run_proactive_weather_alert_sweep`,
  `weather_alert_orchestration_service.py`) checks every farm with a
  location on a timer (default 30 min), reusing the exact same
  `generate_alerts_for_farm_weather` function the pull-based
  `GET .../weather` endpoint already calls - no duplicated rule logic.
  Closes the previously-disclosed "a farmer who never opens the app never
  gets warned of a heavy rain event" safety gap. `farm_repository.list_active_with_location`
  gained an optional `farm_ids` filter for a targeted manual re-run (and
  for tests - see below).
- **D47-05:** `NotificationCategory.HARVEST_ALERT` was registered (title +
  preference mapping) since an earlier phase but grep confirmed zero call
  sites ever created one. `harvest_service.mark_approaching`/`confirm_ready`
  now send `HARVEST_APPROACHING`/`HARVEST_READY`, exactly once per real
  status transition (a later quantity correction while already READY
  does not re-send it - verified by test).

**A real operational discovery made while testing D16-10's sweep:** the
shared test database currently holds **12,020 farms with a location**,
accumulated across this session's repeated full-suite runs (the DB is
real Postgres and is never truncated between runs). An unscoped call to
the new sweep against this database took long enough to need killing
during test-writing - not a bug in the sweep logic, but a real
"unbounded sweep over an ever-growing dataset" scaling characteristic
worth the team's awareness before this ships against a real production
database that could also grow large. Not fixed here (would need
pagination/rate-limiting design, a batch-size product decision, or a
test-database reset strategy - out of scope for this pass); worked
around for testing via the new `farm_ids` filter, which every new sweep
test now uses to stay fast regardless of the shared database's size.

Deferred, not attempted this pass: D40-01/02/03 (voice input/STT -
mobile-only, out of scope for this backend pass), D44-02 (proximity-based
dealer search - lower priority given time, a catalog/price-comparison
marketplace already exists and works, just not geo-ranked), D64-06/D66-04
(payment failure should notify the farmer, not just audit-log - a clean,
buildable fix using the same `notification_service` pattern as this
batch, simply not reached this pass).

Full suite: **675 passed, 0 failed.**

### Batch 8 — Payment failure notifications (2 rows, `c10_payments_finance.md`)

D64-06/D66-04: a failed payment previously produced only an audit log
entry, never a farmer-visible notification. Fixed in both payment paths:

- `payment_service.complete_payment` (dealer-order purchase) - the
  farmer is the payer, so this matters mainly once a real gateway's
  asynchronous webhook replaces the current sandbox callback (today the
  farmer is watching the response anyway).
- `sale_order_service.complete_payment` (marketplace sale) - here the
  BUYER pays and the FARMER is notified, which is genuinely new
  information today, not just future-proofing - the farmer has no other
  synchronous way to learn the buyer's payment failed.

New `NotificationCategory.PAYMENT_ALERT` (migration `b8069da2cd90`).
Confirmed via `docs/PAYMENT_ARCHITECTURE.md`/`docs/PAYMENT_AND_SETTLEMENT.md`
that (unlike `MARKET_ALERT`) no prior decision had explicitly deferred
payment notifications - this was a genuine oversight, not a boundary to
respect.

Full suite: **676 passed, 0 failed.**

### Batch 9 — Governance/security: rate limiting, rule version, AI farmer correction (3 rows fixed, `c13_governance_farmbrain_security.md`)

- **D100-14:** `rate_limit.py`'s own docstring named image-upload
  endpoints as an intended target from the start; grep confirmed it was
  never actually wired in. `crop_photo_service.upload_photo` now enforces
  20 uploads/5min per `farmer_id` (account-scoped, not IP-scoped - a
  farmer legitimately taking several photos in one session must not be
  blocked by a same-IP/shared-network limiter).
- **D88-07:** `CropRiskScoreResponse` now carries `rule_version`
  (`crop_risk_v1`) - lets a historical score stay explainable/reproducible
  even after `_aggregate`'s actual logic changes in a future release.
  Not extended to `weather_action_rules.py`/`weather_alert_rules.py` this
  pass (same pattern, smaller marginal value, deferred).
- **D91-07/D91-09/D91-10:** new `AIAnalysis.farmer_correction`/
  `farmer_correction_notes`/`farmer_corrected_at` fields + `POST
  /ai/analysis/{id}/correction` - a farmer's own correction of a SPECIFIC
  disease-detection result (`confirmed_correct`/`actually_healthy`/
  `actually_diseased`/`wrong_disease_name`), distinct from
  `AdvisoryFeedback`/`AssistantFeedback` which the earlier audit confirmed
  never covered the photo/disease AI pipeline at all. This is the raw
  false-positive/false-negative signal D91-09/10 asked for - a query
  away, not yet a dashboard endpoint (disclosed, not built this pass).

**Investigated and deliberately NOT built, with reasoning:**
- **D88-09** (confidence field on weather/market outputs) - Open-Meteo
  doesn't expose a confidence figure to attach, and fabricating one would
  violate the "no invented precision" rule that already governs AI
  confidence elsewhere in this project.
- **D90-10** (formal `PaymentProvider` ABC mirroring `WeatherProvider`) -
  a pure internal refactor with no farmer-facing behavior change; lower
  value than the other items given the time available this pass.
- **D100-09** (GDPR/DPDP-style data export & account deletion) - a
  genuine compliance gap, but building even a partial version risks
  looking more complete than it is on a legally sensitive feature; this
  needs explicit product/legal scoping (what "export" and "delete" mean
  across dozens of tables, retention requirements) rather than a
  best-guess implementation.

Full suite: **680 passed, 1 failed** (the failure,
`test_products.py::test_admin_can_list_pending_products_to_discover_what_needs_review`,
is the same pre-existing pagination/shared-database-order flakiness noted
in batch 4 - passes 11/11 in isolation, touches nothing this batch
modified).

### Batch 10 — GDPR/DPDP data export & account deletion (D100-09, `c13_governance_farmbrain_security.md`)

Tackled at the product owner's explicit request, after being deliberately
deferred in batch 9 pending exactly this kind of direct instruction (the
legal sensitivity warranted not guessing at scope unprompted).

New `app/services/data_privacy_service.py` — see its module docstring
for the full, honest scoping disclosure (repeated in
`docs/SECURITY.md`'s new "Data privacy" section): this is a good-faith
MVP implementation, explicitly NOT a certified DPDP Act/GDPR compliance
review. Two endpoints:

- `GET /farmers/me/data-export` — aggregates profile, consents, farms/
  plots, crop cycles (+ tasks/treatments/AI analyses/crop-photo metadata
  scoped to them), harvests/listings, expert cases, dealer orders,
  marketplace sales, notifications, input inventory, cost estimates,
  invoices, and ledger entries into one JSON response. Deliberately
  excludes raw photo file bytes (metadata only), `AuditLog` rows, and
  other parties' own data - each exclusion disclosed in the response's
  own `not_included` field, not silently omitted.
- `POST /farmers/me/delete-account` — deactivates (`AccountStatus.INACTIVE`,
  a previously-unused enum value confirmed by grep before this change),
  scrubs direct PII (phone/email/name), and revokes every refresh token.
  Does NOT hard-delete or cascade-delete farms/orders/sales/notifications
  - retained, now tied to an anonymized account, since this codebase has
  no authority to unilaterally decide what tax/audit/dispute-resolution
  retention period is legally sufficient. A known, disclosed limitation:
  an already-issued access token still works for up to
  `jwt_access_token_minutes` after deletion (`current_user.py` never
  re-checks `User.status`, true of every account status already, not
  introduced here) - refresh tokens are revoked immediately, bounding it.

8 new tests (`tests/test_data_privacy.py`) exercising every export
category with real data, not just empty-list happy paths - this caught
two real bugs before they shipped: a wrong model import path
(`HarvestListing` actually lives in `app.models.harvest_listing`, not
`harvest_record`) and calling the input-inventory REPOSITORY instead of
its SERVICE (the repository returns bare ORM rows with no resolved
`product_name`, unlike `input_inventory_service.list_items`).

688/689 backend tests pass (the same pre-existing flaky
`test_products.py` failure, unrelated).
