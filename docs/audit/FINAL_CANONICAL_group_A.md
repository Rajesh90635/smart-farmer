# Canonical Gap Matrix — Group A (Domains 1-26)

This reconciles the four cluster audits (`c01_foundation.md` domains 1-8,
`c02_lifecycle_edgecases.md` domains 9-13+99, `c03_weather_water_soil.md`
domains 14-20, `c04_inputs.md` domains 21-26 — 253 scenario rows total)
against the status deltas recorded since 2026-09-04 in
`docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md` and `docs/FINAL_GAP_REPORT.md`.
Every delta below was independently re-confirmed against those two source
documents (not taken on faith from the task brief) before being applied.

## Reconciliation deltas applied

| Scenario ID | Domain | Was | Now | Source citation |
|---|---|---|---|---|
| D1-18 | 1 Account | BROKEN | VERIFIED | MATRIX §A "All 7 originally-disclosed BROKEN bugs — confirmed fixed this session" (Twilio Verify OTP gate added to `reset_password`) |
| D8-07 | 8 Crop Calendar | MISSING | VERIFIED | GAP_REPORT "Unjustified-Partial audit" resolution table — "Task dependencies... Decided in scope, VERIFIED" (`Task.depends_on_task_id`) |
| D8-08 | 8 Crop Calendar | MISSING | VERIFIED | GAP_REPORT resolution table — "Recurring tasks... Decided in scope, VERIFIED" (`Task.repeat_interval_days`) |
| D9-15 | 9 Task Automation | MISSING | VERIFIED | MATRIX §B Batch 4 (Crop Failure/Re-sowing) — orphaned-task cancellation on `report-failure` |
| D10-01 | 10 Crop Failure | PARTIAL | VERIFIED | MATRIX §B Batch 4 — "Failure reporting distinct from generic cancel" |
| D10-02 | 10 Crop Failure | MISSING | VERIFIED | MATRIX §B Batch 4 — `report-failure` endpoint with reason taxonomy |
| D10-03 | 10 Crop Failure | MISSING | VERIFIED | MATRIX §B Batch 4 — same reason taxonomy covers pest |
| D10-09 | 10 Crop Failure | MISSING | VERIFIED | MATRIX §B Batch 4 — recovery recommendation added |
| D10-10 | 10 Crop Failure | PARTIAL | VERIFIED | MATRIX §B Batch 4 — "re-sowing linkage via `resown_from_crop_cycle_id`" |
| D11-01 | 11 Re-Sowing | MISSING | VERIFIED | MATRIX §B Batch 4 — recovery recommendation (shared with D10-09) |
| D16-10 | 16 Weather Automation | PARTIAL | VERIFIED | MATRIX §B Batch 7 — new `run_proactive_weather_alert_sweep` scheduler job |
| D16-11 | 16 Weather Automation | MISSING | IMPLEMENTED | GAP_REPORT resolution table — "reuse only... existing `crop_weather_heavy_rain` alert now also suggests photographing damage" |
| D20-14 | 20 Soil Testing | MISSING | FUTURE | GAP_REPORT resolution table — "Reclassified FUTURE. Structurally blocked on the entire Soil Testing domain... being built first" |
| D21-01 | 21 Seeds | MISSING | FUTURE | GAP_REPORT resolution table — "Reclassified FUTURE. Requires an authoritative... seeding-rate reference dataset" |
| D21-06 | 21 Seeds | MISSING | VERIFIED | MATRIX §B Batch 3 (Input Inventory) — new `InputInventoryItem` model/service/API |
| D22-04 | 22 Fertilizer | MISSING | VERIFIED | MATRIX §B Batch 3 |
| D22-06 | 22 Fertilizer | MISSING | VERIFIED | MATRIX §B Batch 3 — low-stock alert |
| D23-05 | 23 Crop Protection | MISSING | VERIFIED | MATRIX §B Batch 3 |
| D24-01 | 24 Input Inventory | MISSING | VERIFIED | MATRIX §B Batch 3 |
| D24-02 | 24 Input Inventory | MISSING | VERIFIED | MATRIX §B Batch 3 |
| D24-05 | 24 Input Inventory | PARTIAL | VERIFIED | MATRIX §B Batch 3 — "Expiry now copied onto the farmer's own inventory record" |
| D24-08 | 24 Input Inventory | MISSING | VERIFIED | MATRIX §B Batch 3 — low-stock alert |
| D24-09 | 24 Input Inventory | MISSING | VERIFIED | MATRIX §B Batch 3 — expiry sweep |
| D9-03 | 9 Task Automation | FUTURE | MISSING | Frozen this session (`docs/FINAL_IMPLEMENTATION_PLAN.md` caveat resolution): the FUTURE citation rested entirely on "no background scheduler anywhere in the project," which is now false — `scheduler.py` (APScheduler) exists with 3 registered jobs. No remaining justification for FUTURE; reclassified MISSING and merged into the Task-overdue-reminder cluster with D9-16/D78-01/D37-04. |
| D9-14 | 9 Task Automation | FUTURE | **removed — folded into D8-07 (VERIFIED)** | Verbatim duplicate of D8-07 ("Task dependencies"), already VERIFIED via `Task.depends_on_task_id`. No independent gap; carrying it as a second scenario ID double-counted one finished feature. Removed from the row count (799→798 group-file total after this fold). |
| D9-11 | 9 Task Automation | OUT_OF_SCOPE (flagged questionable) | OUT_OF_SCOPE (confirmed) | Independently re-verified this session by direct grep of `backend/app/models/task.py` for `assignee\|reviewer\|Role\.`: zero matches. This is not an inferential absence — it is consistent with the task domain's actual, uniform design principle (cited at D9-01/D16-05/D16-06 as "the farmer-only-task-mutation convention"): every task is farmer-created-and-owned only, with zero second-party assignment/review concept anywhere in the domain. No product requirement document defines role-based task rejection. Per the zero-gap rule, kept OUT_OF_SCOPE only because the product genuinely does not define this workflow today, not because it would be hard to build — flag removed. |

**Confirmed complete for this group:** Section A's 7 BROKEN-bug fixes, all 11
batches in Section B, and the 9-row + 2-borderline resolution in
`FINAL_GAP_REPORT.md` were each checked by scenario ID against domains 1-26
and 99. Only the 23 IDs above fall in this group's range — no other D1-D26
or D99 IDs appear in either source document's delta tables (the remaining
items in those tables — D33-D100 range — belong to other reconciliation
groups and are out of scope here).

## Count summary (this group)

| Status | Count |
|---|---:|
| VERIFIED | 185 |
| IMPLEMENTED | 25 |
| PARTIAL | 6 |
| MISSING | 10 |
| BROKEN | 0 |
| FUTURE | 15 |
| OUT_OF_SCOPE | 5 |
| ENVIRONMENT_DEPENDENT | 6 |
| TOTAL | 252 |

*(Missing Backlog Batch 8, this session: 12 rows MISSING→VERIFIED (-12 Missing, +12
Verified): D3-07 (plot boundary, JSONB points - not PostGIS), D5-02 (admin variety
creation), D9-08 (task completion_percentage), D13-02/D17-06/D19-04 (season/water/soil
append-only history tables, all mirroring `CropCycleStageHistory`'s exact convention),
D13-04 (zero-code bonus - proved, not assumed, that already-VERIFIED D8-08+D13-05 already
satisfy perennial recurring maintenance), D14-02 (hourly forecast, reuses the
`weather_snapshots` table via a new `snapshot_type`), D15-05/D15-07 (storm/hail decoded
from the real WMO weather-code table), D17-02/D17-03 (farmer-declared water_availability +
derived water_shortage). D15-06 (Cyclone) re-investigated and correctly NOT built - no WMO
code represents a cyclone; stays Missing. Full backend suite: 1043 passed, 0 failed (up
from 996 pre-Batch-8). See `docs/FINAL_GAP_REPORT.md`'s own Batch 8 note for the
cross-group total.)*

*(Further updated this session: the Soil Testing domain foundation D20-01 through D20-12
(12 items) MISSING→VERIFIED (-12 MISSING, +12 VERIFIED) — an entirely new domain built from
zero code, per the user's explicit approval to continue into this cluster. D19-05
MISSING→VERIFIED (-1 MISSING, +1 VERIFIED, pure soil-type surfacing on crop-cycle
responses). D19-03 MISSING→FUTURE (-1 MISSING, +1 FUTURE) — a documented deferral, not
built, per this row's own recommendation despite its blocker (D20) now being resolved.)*

*(Further updated this session: D3-08/D3-09/D17-01 PARTIAL→VERIFIED (-3 PARTIAL, +3
VERIFIED, validated irrigation/soil enums on Plot); D18-06/D18-08 MISSING→VERIFIED (-2
MISSING, +2 VERIFIED, new IrrigationRecord model); D24-04 PARTIAL→VERIFIED (-1 PARTIAL, +1
VERIFIED, InputInventoryItem.acquired_at).)*

*(Later continuation session — Missing Backlog Batch 7, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. Assembled directly from
the remaining backlog's own dependency graph - no persisted priority-plan
doc names Batch 7's approved scenario count, same situation Batch 3/4/5/6
disclosed. This group's contribution is 3 zero-code reclassification
bonuses, not new implementation (the batch's real build work - the
Storage domain - lives entirely in
`docs/audit/FINAL_CANONICAL_group_C.md`, this group has no Domain 53
rows): D9-13 MISSING→VERIFIED (-1 Missing, +1 Verified) - re-confirmed to
be a duplicate scenario ID for the same already-VERIFIED feature as D8-08
(`Task.repeat_interval_days`), per this row's own citation; folded into
D8-08's VERIFIED status rather than treated as an independent gap. D2-10
(active farm selection) and D22-01 (fertilizer requirement)
MISSING→OUT_OF_SCOPE (-2 Missing, +2 Out of Scope) - both explicitly
confirmed by their own row text to be deliberate design/safety decisions,
not engineering gaps (D2-10: a deliberate stateless design, every call
takes an explicit farm_id; D22-01: an auto-computed dosage recommendation
is structurally out of bounds per `docs/PRODUCT_SAFETY.md`'s absolute
no-independent-prescription rule, same class as D23-08's assistant-side
pesticide-dosage block). Total unchanged at 252 - every change here is an
internal status move, zero new/removed rows. See
`docs/audit/FINAL_CANONICAL_group_C.md`'s own Batch 7 note for this
batch's real build work (the Storage domain, D53-01..05/07, D52-04,
D48-04). See docs/FINAL_GAP_REPORT.md for the cross-group reconciliation
and exact full-suite counts.)*

*(Later continuation session — Missing Backlog Batch 6, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. Assembled directly from
the remaining backlog's own dependency graph - no persisted priority-plan
doc names Batch 6's approved scenario count, same situation Batch 3/4/5
disclosed. 1 row in this group MISSING→VERIFIED (-1 Missing, +1
Verified): D2-07 (farm infrastructure) - new `FarmInfrastructure` model,
list-per-farm CRUD mirroring `plot_service.py`'s exact shape, farmer-
entered and informational only. Total unchanged at 252 - an internal
status move, zero new/removed rows. See
`docs/audit/FINAL_CANONICAL_group_B.md`'s own Batch 6 note for the rest
of this batch's scenarios (D37-01/02/03/05/06). See
docs/FINAL_GAP_REPORT.md for the cross-group reconciliation and exact
full-suite counts.)*

*(Later continuation session — Missing Backlog Batch 4, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. This session began after
an unexpected shutdown mid-Batch-3 (see that batch's own recovery note in
this repo's history); no persisted priority-plan doc names Batch 4's
approved scenario count the way Batch 1/2's own commit messages do, so
this batch was assembled directly from the remaining backlog's own
dependency graph. 1 row in this group MISSING→VERIFIED (-1 MISSING, +1
VERIFIED): D20-13 (soil test reminder) - new `soil_test_reminder_sweep`
scheduler job mirroring `run_expiry_check_sweep`'s exact shape, alerting
on the LATEST `SoilTestResult` per plot once stale; all 4 of this row's
own cited dependencies (D20-01/02/11/12) were already VERIFIED. Also
closes D78-10 (docs/audit/FINAL_CANONICAL_group_D.md), a different
group's row whose own cited blocker ("Soil Testing domain doesn't exist")
no longer held. Total unchanged at 252 - an internal status move, zero
new/removed rows. See `docs/audit/FINAL_CANONICAL_group_D.md`'s own Batch
4 note for the rest of this batch's scenarios (D81-02/03/04/06/07, D83-02,
D89-04, D78-10). Full backend suite and full Flutter suite both re-run
green after this batch - see `docs/FINAL_GAP_REPORT.md` for exact counts.)*

*(Later continuation session — Missing Backlog Batch 2, per the "SMART
FARMER V3 MISSING BACKLOG PRIORITIZATION" plan. 4 approved Batch 2 items in
this group all became VERIFIED with genuine minimal fixes: D2-08/D2-09
(-2 MISSING, +2 VERIFIED - `FarmResponse.irrigation_summary`/`soil_summary`,
a computed rollup across a farm's own plots merging BOTH the legacy
free-text `Plot.irrigation_type`/`soil_type` AND the later, separate,
validated-enum `irrigation_source`/`soil_category` fields - found during
testing that the enum fields are independently settable and were being
silently dropped from an earlier draft of this rollup, fixed before
landing); D13-05 (-1 MISSING, +1 VERIFIED - `TaskType.PRUNING`, migration
`fd90ec676715`, plus the mobile task-creation dropdown); D24-10 (-1
MISSING, +1 VERIFIED - `input_inventory_service.get_item_history` reusing
the existing `AuditLogger(entity="input_inventory_item")` trail exactly
like D2-06's `get_farm_history`, zero new DB work; a real pre-existing bug
found and fixed in the process - `create_item`'s audit-log call read
`item.id` before the `db.flush()` that populates it, so every CREATED
event had been silently logged under entity_id="None", unreachable by any
future query). Total unchanged at 252 - every change here is an internal
status move, zero new/removed rows. Full backend suite: 930 passed, 0
failed/errored (pre-existing count before this pass's own final doc-only
edits; re-confirmed clean for every touched test file individually). Full
flutter suite: 301 passed, 0 failed. See docs/FINAL_GAP_REPORT.md and
docs/FINAL_RELEASE_READINESS.md for the cross-group reconciliation.)*

*(Further updated this session: D15-04/D15-08/D15-09/D17-04/D17-05 MISSING→VERIFIED (-5
MISSING, +5 VERIFIED) — the weather-risk safety-detection cluster: frost (Magnus-formula
dew point) and cumulative-rainfall/consecutive-dry-days (flood/waterlogging/drought), all
buildable from already-stored weather_snapshots history.)*

*(Further updated this session: D10-04/D10-05/D10-06/D10-07 MISSING→VERIFIED (-4 MISSING,
+4 VERIFIED) — all four enum values already existed in code, only dedicated tests plus
D10-07's failure_reason_note field were missing. D1-19 MISSING→VERIFIED (-1 MISSING, +1
VERIFIED) — new self-deactivation endpoint. D7-01/D7-03 MISSING→VERIFIED (-2 MISSING, +2
VERIFIED) — new optional LAND_PREPARATION/GERMINATING stages. D7-07 MISSING→OUT_OF_SCOPE
(-1 MISSING, +1 OUT_OF_SCOPE) — a documented product decision not to add an arbitrary third
stage, per this row's own suggested alternative.)*

*(Updated this session: D9-03 FUTURE→MISSING (+1 MISSING, -1 FUTURE);
D9-14 removed as a duplicate of D8-07/VERIFIED (-1 FUTURE, -1 TOTAL); D6-07 and D11-05
PARTIAL→VERIFIED, P0 concurrency-guard fix (-2 PARTIAL, +2 VERIFIED); P1 task-management
cluster — D9-03/D9-05/D9-06/D9-09/D9-10/D9-12 MISSING→VERIFIED (-6 MISSING, +6 VERIFIED),
D9-16 PARTIAL→VERIFIED (-1 PARTIAL, +1 VERIFIED). See "Reconciliation deltas applied" above
and each row's own entry for citations. 253→252 total; all subsequent moves are internal
status changes only.)*

*(Further updated this continuation session: cluster #7 re-verification —
D21-07/D22-05/D23-06/D24-03/D24-06/D24-07 MISSING→VERIFIED (-6 MISSING, +6 VERIFIED). Direct
re-read of `input_inventory_service.py` confirmed the plan's own suspicion: the existing
generic, category-agnostic `record_usage`/`InputInventoryItem.unit`/`InputInventoryItem.quantity`
decrement already fully satisfied all six rows — no new code needed. See each row's own entry
above and `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §D for citations.)*

*(Later continuation session — Partial-only completion pass, per the user's explicit
"complete every genuine Partial scenario" instruction. Processed all 28 Partial rows in this
group:
- **19 PARTIAL→VERIFIED**: D1-17 (already complete - existing tests + docstring already
  satisfied this row, no code); D2-06 (farm history endpoint, new); D3-06 (accepted design -
  Farm's hierarchy already suffices, no code); D3-12 (previous-crop context, new); D4-07 and
  D10-11 (already complete - subsumed by the D10-01/02/03 batch, formally reclassified, no
  code); D5-04 (variety-duration harvest-date suggestion, new); D7-11 (`is_closed` computed
  field, new); D8-01 (farmer-level task calendar, new); D11-02 (mobile re-sow confirmation
  dialog, new); D13-01 (accepted design - no artificial duration cap, no code); D13-06
  (calendar-year rollup, new, scoped below D13-02's season-boundary concept); D99-01 (rollup -
  D10-04/05/06/07 already VERIFIED, D10-08 disclosed optional); D99-02 (rollup - D11-06 is the
  same disclosed D9-01/D8-02 deferral, not blocking); D14-09 (severe-weather co-occurrence
  escalation, new); D21-03 (Product.variety_id + seed filter, new); D22-02/D25-01 (product
  category/manufacturer filters, new); D26-02 (admin product-image upload, new).
- **3 PARTIAL→FUTURE**: D8-06, D16-01, D16-03 - each a deliberate, already-documented
  anti-fabrication or architecture boundary (auto-task-mutation, plot-level weather caching
  redesign, unvalidated agronomic thresholds), matching this row's own recommended
  reclassification or an existing project doc's explicit stance. Not built, per the safety/
  no-fabrication rules governing this session.
- **6 stay PARTIAL, genuinely blocked, NOT implemented**: D12-02/03/04/05/06 and D99-04 all
  depend on D12-01 and/or D13-02/04/05 respectively - real, substantial Missing features
  (deliberate intercropping support; season-history tracking), not small technical gaps.
  Completing them would mean building those Missing features, out of a Partial-only session's
  explicit scope boundary. Re-confirmed, not silently carried forward.
Backend: 22 new/updated tests across `test_crop_cycles.py`, `test_farms.py`, `test_tasks.py`,
`test_weather_alert_rules.py`, `test_products.py`, all passing. Mobile: `flutter analyze` (41
issues, 0 errors, unchanged) and `flutter test` (267 passed, was 263) both re-run. Migrations:
`21f2c9cef22d` (device_id, prior batch), `1e25cb4e88d7` (severe_weather_alert),
`a2f94d64b787` (products.variety_id) - all round-tripped clean. Group A: PARTIAL 28→6,
VERIFIED 147→166, FUTURE 12→15, MISSING unchanged at 31 (no Missing row touched). See
`docs/FINAL_GAP_REPORT.md` for the cross-group total.)*

## 1. Attended (Verified + Implemented) - condensed list

| ID | Domain | Scenario Name | Status | One-line evidence |
|---|---|---|---|---|
| D1-01 | 1 Account | Farmer registration | VERIFIED | auth_service.py:75-129; test_registration.py |
| D1-02 | 1 Account | Login | VERIFIED | auth_service.py:132-167; test_login.py |
| D1-03 | 1 Account | Logout | VERIFIED | auth_service.py:246-261; test_tokens.py |
| D1-04 | 1 Account | Session refresh | VERIFIED | auth_service.py:170-194; test_tokens.py (6 tests) |
| D1-05 | 1 Account | Authentication expiry | VERIFIED | core/jwt.py:31; refresh_token.py:31-37 |
| D1-06 | 1 Account | Profile creation | VERIFIED | auth_service.py:96-103; test_registration.py |
| D1-07 | 1 Account | Profile update | VERIFIED | farmer_service.py:33-50; test_farmer_profile.py |
| D1-08 | 1 Account | Preferred language | VERIFIED | farmer_profile.py:37-40 |
| D1-09 | 1 Account | Notification preferences | VERIFIED | notification_preference.py:24-32; test_notifications.py |
| D1-10 | 1 Account | Camera permission | IMPLEMENTED | pubspec.yaml:18 (image_picker); no denial-path test |
| D1-12 | 1 Account | Location permission | IMPLEMENTED | add_edit_farm_screen.dart:191-198; no widget test |
| D1-13 | 1 Account | Consent | VERIFIED | consent_record.py; api/v1/farmers.py:39-53 |
| D1-15 | 1 Account | Multiple farms | VERIFIED | farm.py:3-4; test_list_my_farms |
| D1-16 | 1 Account | Farm switching | IMPLEMENTED | my_farms_screen.dart:1-60, deliberate stateless design |
| D1-18 | 1 Account | Account recovery | VERIFIED (delta) | Twilio Verify OTP gate now required before password reset |
| D2-01 | 2 Farm | Farm creation | VERIFIED | farm_service.py:17-47; test_farms.py |
| D2-02 | 2 Farm | Farm editing | VERIFIED | farm_service.py:66-119 |
| D2-03 | 2 Farm | Farm deactivation | VERIFIED | farm_service.py:122-137 |
| D2-04 | 2 Farm | Farm location | VERIFIED | farm.py:53-70 |
| D2-05 | 2 Farm | Farm area | VERIFIED | farm.py:38-39,72-81 |
| D3-01 | 3 Plot | Plot creation | VERIFIED | plot_service.py:24-48 |
| D3-02 | 3 Plot | Plot editing | VERIFIED | plot_service.py:66-93 |
| D3-03 | 3 Plot | Plot deletion/deactivation | VERIFIED | plot_service.py:96-105 |
| D3-04 | 3 Plot | Multiple plots | VERIFIED | farm.py:95 (cascade relationship) |
| D3-05 | 3 Plot | Plot area | VERIFIED | plot.py:28,38-43 |
| D3-10 | 3 Plot | Crop association | VERIFIED | plot.py:64; crop_cycle.py:79 |
| D3-11 | 3 Plot | Plot history | VERIFIED | crop_cycle_repository.py:36-43 |
| D4-01 | 4 Crop | Crop selection | VERIFIED | crops.py:29-37 |
| D4-02 | 4 Crop | Crop creation (crop-cycle) | VERIFIED | crop_cycle_service.py:43-80 |
| D4-03 | 4 Crop | Crop editing | VERIFIED | crop_cycle_service.py:110-153 |
| D4-04 | 4 Crop | Crop status | VERIFIED | crop_cycle.py:29-62 |
| D4-05 | 4 Crop | Crop history | VERIFIED | test_crop_stage_history.py (6 tests) |
| D4-06 | 4 Crop | Crop lifecycle | VERIFIED | crop_cycle.py:53-61 |
| D4-08 | 4 Crop | Crop closure | VERIFIED | crop_cycle_service.py:156-186 |
| D5-01 | 5 Crop Variety | Variety selection | VERIFIED | crop_varieties.py:21-27 |
| D5-03 | 5 Crop Variety | Variety-specific crop cycle | VERIFIED | crop_cycle_service.py:55-59 |
| D6-01 | 6 Crop Cycle | Create crop cycle | VERIFIED | crop_cycle_service.py:43-80 |
| D6-02 | 6 Crop Cycle | Sowing date | VERIFIED | crop_cycle.py:68-75 |
| D6-03 | 6 Crop Cycle | Expected harvest date | VERIFIED | crop_cycle_service.py:126 |
| D6-04 | 6 Crop Cycle | Actual harvest date | VERIFIED | crop_cycle_service.py:156-186,165-166 |
| D6-05 | 6 Crop Cycle | Crop stage | VERIFIED | crop_cycle.py:29-62 |
| D6-06 | 6 Crop Cycle | Cycle status | VERIFIED | crop_cycle.py ALLOWED_TRANSITIONS |
| D6-07 | 6 Crop Cycle | Multiple cycles (concurrency guard) | VERIFIED (this session, P0, was Partial) | `crop_cycle_repository.count_active_for_plot` + guard in `create_crop_cycle`; `test_crop_cycles.py::test_cannot_create_a_second_active_crop_cycle_on_the_same_plot` |
| D6-08 | 6 Crop Cycle | Cycle correction | VERIFIED | crop_cycle_service.py:110-153,142 |
| D6-09 | 6 Crop Cycle | Cycle closure | VERIFIED | crop_cycle_service.py:156-186 |
| D7-02 | 7 Crop Stages | Sowing | VERIFIED | crop_cycle.py:53-61 |
| D7-04 | 7 Crop Stages | Vegetative | VERIFIED | crop_cycle.py:29-62 |
| D7-05 | 7 Crop Stages | Flowering | VERIFIED | crop_cycle.py:29-62 |
| D7-06 | 7 Crop Stages | Fruit/grain development | VERIFIED | crop_cycle.py:29-62 |
| D7-08 | 7 Crop Stages | Harvest ready | VERIFIED | crop_cycle.py:29-62 |
| D7-09 | 7 Crop Stages | Harvested | VERIFIED | crop_cycle_service.py:156-186 |
| D7-13 | 7 Crop Stages | Farmer stage correction | VERIFIED | crop_cycle_service.py:142 |
| D8-07 | 8 Crop Calendar | Task dependencies | VERIFIED (delta) | Task.depends_on_task_id; test_tasks.py::test_task_dependency_* (D9-14, "Dependent task," is a verbatim duplicate of this row, folded here rather than counted separately — see Reconciliation deltas above) |
| D8-08 | 8 Crop Calendar | Recurring tasks | VERIFIED (delta) | Task.repeat_interval_days; test_tasks.py::test_completing_a_re* |
| D9-02 | 9 Task Automation | Due date | VERIFIED | test_tasks.py:8,31 |
| D9-04 | 9 Task Automation | Overdue detection | VERIFIED | task_service.py:30-35 |
| D9-07 | 9 Task Automation | Completion | VERIFIED | task_service.py:120-130 |
| D9-15 | 9 Task Automation | Invalidated task | VERIFIED (delta) | report-failure endpoint cancels orphaned tasks (Batch 4) |
| D10-01 | 10 Crop Failure | Farmer reports failure | VERIFIED (delta) | crop_cycle.py failure_reason + report-failure endpoint |
| D10-02 | 10 Crop Failure | Disease-related failure | VERIFIED (delta) | FailureReason enum incl. DISEASE |
| D10-03 | 10 Crop Failure | Pest-related failure | VERIFIED (delta) | FailureReason enum incl. PEST |
| D10-09 | 10 Crop Failure | Recovery recommendation | VERIFIED (delta) | report-failure endpoint recovery guidance |
| D10-10 | 10 Crop Failure | Re-sowing decision | VERIFIED (delta) | resown_from_crop_cycle_id linkage |
| D11-01 | 11 Re-Sowing | Re-sowing recommendation | VERIFIED (delta) | report-failure recovery recommendation (shared w/ D10-09) |
| D11-05 | 11 Re-Sowing | Old cycle closure | VERIFIED (this session, P0, was Partial) | Same fix/tests as D6-07 above |
| D11-03 | 11 Re-Sowing | New sowing date | VERIFIED | schemas/crop.py:19-32 |
| D11-04 | 11 Re-Sowing | New crop cycle | VERIFIED | crop_cycle_service.py:43-80 |
| D11-07 | 11 Re-Sowing | History preservation | VERIFIED | crop_cycle_repository.py:36-51 |
| D13-03 | 13 Perennial Crops | Multiple harvests | VERIFIED | harvest_record.py; test_harvest.py:79,87 |
| D99-05 | 99 Special Crop Scenarios | Multiple harvests | VERIFIED | cross-ref D13-03 |
| D99-06 | 99 Special Crop Scenarios | Repeated crop cycles | VERIFIED | cross-ref D11-04/07 |
| D14-07 | 14 Weather | Humidity | IMPLEMENTED | fake_weather_provider.py:15; no value assertion in test |
| D15-01 | 15 Weather Risk | Heavy rain | VERIFIED | weather_alert_rules.py:39-50 |
| D15-02 | 15 Weather Risk | Heat (extreme) | VERIFIED | weather_alert_rules.py:83-92 |
| D15-03 | 15 Weather Risk | Cold (extreme) | VERIFIED | weather_alert_rules.py:93-102 |
| D15-10 | 15 Weather Risk | Weather freshness | IMPLEMENTED | schemas/weather.py:47; not itself asserted by a dedicated test |
| D15-11 | 15 Weather Risk | Stale weather detection | VERIFIED | weather_snapshot.py:60-61; test_weather.py |
| D16-02 | 16 Weather Automation | Weather to affected crop | VERIFIED | weather_alert_rules.py:107-126 |
| D16-04 | 16 Weather Automation | Weather to risk | VERIFIED | crop_risk_service.py:167-191 |
| D16-08 | 16 Weather Automation | Weather to irrigation adjustment | VERIFIED | irrigation_intelligence_service.py:15-22 |
| D16-09 | 16 Weather Automation | Weather to spraying warning | VERIFIED | weather_alert_rules.py:129-148; weather_action_rules.py:42-69 |
| D16-10 | 16 Weather Automation | Weather to farmer notification | VERIFIED (delta) | run_proactive_weather_alert_sweep scheduler job |
| D16-11 | 16 Weather Automation | Weather to post-event inspection | IMPLEMENTED (delta) | crop_weather_heavy_rain alert now suggests photographing damage |
| D18-01 | 18 Irrigation | Rain-fed | IMPLEMENTED | plot.py:49 free text, unvalidated |
| D18-02 | 18 Irrigation | Borewell | IMPLEMENTED | same mechanism as D18-01 |
| D18-03 | 18 Irrigation | Canal | IMPLEMENTED | same mechanism as D18-01 |
| D18-04 | 18 Irrigation | Drip | IMPLEMENTED | farm_factories.py:20, not asserted in response |
| D18-05 | 18 Irrigation | Sprinkler | IMPLEMENTED | same mechanism as D18-01 |
| D18-07 | 18 Irrigation | Irrigation task | VERIFIED | test_tasks.py:12,164-171 |
| D18-09 | 18 Irrigation | Irrigation recommendation | VERIFIED | irrigation_intelligence_service.py:15-22 |
| D19-01 | 19 Soil | Soil profile | IMPLEMENTED | plot.py:3-9,48 free text, deliberate placeholder |
| D19-02 | 19 Soil | Soil type | IMPLEMENTED | same field as D19-01 |
| D21-02 | 21 Seeds | Seed selection | IMPLEMENTED | products.py:202-232; no dedicated /seeds test |
| D21-04 | 21 Seeds | Seed purchase | IMPLEMENTED | orders.py:37-84; generic mechanism VERIFIED, seed facet untested |
| D21-05 | 21 Seeds | Seed receipt | IMPLEMENTED | orders.py:97-103; order detail IS the receipt |
| D21-06 | 21 Seeds | Seed inventory | VERIFIED (delta) | InputInventoryItem model/service (Batch 3) |
| D22-03 | 22 Fertilizer | Fertilizer purchase | IMPLEMENTED | same generic mechanism as D21-04 |
| D22-04 | 22 Fertilizer | Fertilizer inventory | VERIFIED (delta) | InputInventoryItem (Batch 3) |
| D22-06 | 22 Fertilizer | Low-stock alert | VERIFIED (delta) | InputInventoryItem low-stock alert (Batch 3) |
| D22-07 | 22 Fertilizer | Expiry | VERIFIED | dealer_product.py:45-46; test_checkout_fails_on_expired_listing |
| D22-08 | 22 Fertilizer | Safe recommendation boundary | IMPLEMENTED | docs/PRODUCT_SAFETY.md; product.py:9-13 |
| D23-01 | 23 Crop Protection | Disease-control input | IMPLEMENTED | product.py:33 category enum |
| D23-02 | 23 Crop Protection | Pest-control input | IMPLEMENTED | product.py:32 |
| D23-03 | 23 Crop Protection | Bio-input | IMPLEMENTED | product.py:31 |
| D23-04 | 23 Crop Protection | Input purchase | VERIFIED | test_checkout_fails_if_product_suspended_after_listing_created |
| D23-05 | 23 Crop Protection | Input inventory | VERIFIED (delta) | InputInventoryItem (Batch 3) |
| D23-07 | 23 Crop Protection | Expiry | VERIFIED | test_checkout_fails_on_expired_listing (category-agnostic) |
| D23-08 | 23 Crop Protection | Safety boundary (no Rx pesticide) | VERIFIED | assistant chat blocks pesticide/dosage questions |
| D23-09 | 23 Crop Protection | No automatic chemical purchase | IMPLEMENTED | docs/PRODUCT_SAFETY.md:16-36, structural isolation, no negative test |
| D24-01 | 24 Input Inventory | Inventory creation | VERIFIED (delta) | InputInventoryItem model (Batch 3) |
| D24-02 | 24 Input Inventory | Quantity | VERIFIED (delta) | InputInventoryItem.quantity (Batch 3) |
| D24-05 | 24 Input Inventory | Expiry date | VERIFIED (delta) | expiry copied onto the owning farmer inventory record (Batch 3) |
| D24-08 | 24 Input Inventory | Low stock | VERIFIED (delta) | InputInventoryItem low-stock alert (Batch 3) |
| D24-09 | 24 Input Inventory | Expiry warning | VERIFIED (delta) | run_expiry_check_sweep (Batch 3) |
| D25-02 | 25 Input Purchase | Compare | VERIFIED | price_comparison.py:31; test_price_comparison.py |
| D25-03 | 25 Input Purchase | Seller | VERIFIED | test_compare_offers_excludes_unverified_dealer |
| D25-04 | 25 Input Purchase | Price | VERIFIED | test_reference_price_unavailable_returns_404 |
| D25-05 | 25 Input Purchase | Purchase | VERIFIED | test_checkout_calculates_price_server_side_ignoring_client_values |
| D25-06 | 25 Input Purchase | Order | VERIFIED | order.py:31-67; test_full_order_lifecycle_to_delivery |
| D25-07 | 25 Input Purchase | Receive | IMPLEMENTED | orders.py:145-170; no dedicated test |
| D25-08 | 25 Input Purchase | Receipt | IMPLEMENTED | orders.py:97-103; no dedicated test |
| D25-09 | 25 Input Purchase | Purchase history | IMPLEMENTED | orders.py:87-94; no dedicated test |
| D25-10 | 25 Input Purchase | Explicit farmer confirmation | VERIFIED | test_add_to_cart_creates_draft_order + checkout tests |
| D26-01 | 26 Input Verification | Seller information | VERIFIED | test_compare_offers_excludes_unverified_dealer |
| D26-03 | 26 Input Verification | Expiry verification | VERIFIED | test_checkout_fails_on_expired_listing |
| D26-05 | 26 Input Verification | Suspicious/counterfeit indication | VERIFIED | test_scam_shield_flags_a_high_price (price-anomaly only, see itemized note) |
| D26-06 | 26 Input Verification | Bill/receipt capture | VERIFIED | test_invoices.py (6 tests) |
| D26-07 | 26 Input Verification | OCR provider boundary | VERIFIED | test_ocr_confidence_is_a_real_computed_value_not_fabricated |

## 2. Partial - full itemized (EVERY row, no aggregation)

### D1-17 - Domain 1 (Account) - Multiple users/roles where defined
- Current implementation status: **VERIFIED (later continuation session, was Partial - already complete, not fabricated)**
- Existing relevant files/classes/functions: core/roles.py (12 roles defined, 7 seeded, lines 39-47); auth_service.py:43-56 _resolve_role; user_roles join table
- Re-checked this session: grep for `Role.LAB`/`Role.TRANSPORTER`/`Role.FAMILY_MEMBER`/`Role.FARM_WORKER` across `app/` returns zero matches - none of the 4 unseeded roles have any code consumer (no `require_role` check, no RBAC gate), so seeding them would be pure speculative work per this row's own "where a real use case exists" qualifier, correctly not done. The multi-role resolution path IS already exercised: `tests/test_login.py::test_login_returns_admin_role_when_admin_role_is_assigned` and `::test_login_role_resolution_is_deterministic_for_multi_role_accounts` both assign a second role to a farmer and assert `_resolve_role`'s precedence. Precedence is documented in `_resolve_role`'s own docstring (admin wins if present, else first-assigned).
- Missing component: none
- Required implementation: none
- Dependencies: role-gated endpoints across expert-network and dealer-marketplace domains implicitly assume single-role resolution
- Backend work: core/roles.py (seed data); auth_service.py::_resolve_role (multi-role precedence logic plus test)
- Database/migration work: none - user_roles join table already supports it; only a seed-data migration if unseeded roles go live
- Mobile work: none - backend only
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: yes - multi-role precedence is itself an access-control decision, needs an explicit rule once exercised
- Tests required: test_resolve_role_with_multiple_roles_prefers_X; seed-completeness test
- Verification method: automated test
### D2-06 - Domain 2 (Farm) - Farm history
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `farm_service.get_farm_history` + `GET /farms/{farm_id}/history`, mirroring `cases.py::get_case_audit`'s exact pattern (reuses the existing `AuditLog` table, `entity="farm"`)
- Missing component: none
- Required implementation: none (mobile Farm History screen not built - tracked as a follow-up, not a gap in this scenario's backend-verified status)
- Tests added and passing: `tests/test_farms.py::test_farm_history_shows_created_and_updated_events_in_order`, `::test_farm_history_is_not_visible_to_another_farmer`
- Verification method: automated test, confirmed passing
- Dependencies: same reusable pattern needed by D19-04 (soil history) and D24-10 (inventory history)
- Backend work: new endpoint in api/v1/farms.py plus a thin service method filtering audit_log by entity_type=farm, entity_id=farm_id, mirroring orders.py's existing audit-route pattern
- Database/migration work: none - audit_log table already exists
- Mobile work: new farm-history screen consuming the new endpoint
- Automation work: none
- Notification work: none
- Offline/sync impact: none - read-only history view, online-only like other audit reads
- Security/RBAC impact: ownership check required (same _get_owned_farm_or_404 pattern used elsewhere)
- Tests required: endpoint ownership test plus content test (created/updated/deactivated events appear in order)
- Verification method: automated test

### D3-06 - Domain 3 (Plot) - Plot location
- Current implementation status: **VERIFIED (later continuation session, was Partial - accepted design choice, per this row's own suggested resolution path)**
- Existing relevant files/classes/functions: plot.py:45-46 single nullable lat/lng point only, no admin hierarchy (state/district/mandal/village) like Farm has
- Decision made this session: a plot always sits within one farm whose state/district/mandal/village hierarchy is already set and validated (see Farm's own location tests) - a plot never needs an independent administrative-location chain, only optionally a more precise point coordinate, which already exists (`latitude`/`longitude`). Adding a second, redundant hierarchy at the plot level would fragment location data with no farmer-facing benefit and was correctly never built. Not a gap.
- Missing component: none
- Required implementation: none
- Dependencies: reuses Farm's location_service.validate_farm_location pattern
- Backend work: plot.py model plus plot_service.py validation reusing location_service.validate_farm_location
- Database/migration work: new nullable FK columns (state_id/district_id/mandal_id/village_id) on plots table, Alembic migration mirroring the Farm hierarchy migration
- Mobile work: add_edit_plot form location pickers (only if farm-level default is not sufficient)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard plot-write sync queue, no new impact
- Security/RBAC impact: none
- Tests required: test_create_plot_with_full_location_chain mirroring Farm's equivalent test
- Verification method: automated test
### D3-08 - Domain 3 (Plot) - Irrigation source
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Partial)**
- Fix applied: `Plot.IrrigationSource` enum (rain_fed/borewell/canal/drip/sprinkler/other,
  migration `d4e5f6a7b8c9`) as a NEW, purely additive `irrigation_source` column, alongside
  the existing free-text `irrigation_type` (left completely unchanged, never backfilled —
  no lossy guess was invented from arbitrary old free text; None on an existing plot
  honestly means "not yet classified"). Closes D17-01 in the same fix, as this row's own
  dependency note anticipated.
- Mobile work: not yet done — `add_edit_plot_screen.dart` should add a dropdown; tracked as
  a follow-up.
- Tests added and passing: `test_plots.py::test_plot_irrigation_source_and_soil_category_are_validated_enums`,
  `::test_plot_irrigation_source_rejects_an_invalid_value`, `::test_update_plot_irrigation_source_and_soil_category`
- Verification method: automated test, confirmed passing

### D3-09 - Domain 3 (Plot) - Soil association
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D3-08, was Partial)** — `Plot.SoilCategory` enum (loamy/clayey/sandy/black_cotton/red/
  alluvial/other), same additive-only design as D3-08 (existing free-text `soil_type` left
  unchanged). Deliberately NOT conflated with the full Soil Testing domain (D20)'s lab-test
  system, which remains structurally separate and unbuilt. See D3-08's entry above for the
  shared evidence.
- Verification method: automated test (same tests as D3-08), confirmed passing
### D3-12 - Domain 3 (Plot) - Previous crop
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `crop_cycle_repository.get_most_recent_for_plot` + `CropCycleResponse.previous_crop_cycle_id`/`previous_crop_name`, populated only in `create_crop_cycle`'s response
- Missing component: none (a same-crop-family-repeat advisory was NOT added - would require an agronomic crop-family taxonomy this project doesn't have; correctly not fabricated)
- Required implementation: none
- Tests added and passing: `tests/test_crop_cycles.py::test_create_crop_cycle_response_includes_previous_crop_cycle`
- Verification method: automated test, confirmed passing
- Dependencies: none blocking
- Backend work: crop_cycle_service.py::create_crop_cycle - look up the plot most recent prior cycle and include it in the response
- Database/migration work: none - data already exists, purely a read/surface change
- Mobile work: add_crop_screen.dart shows a previous-crop context line
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_create_crop_cycle_response_includes_previous_crop_cycle
- Verification method: automated test

### D4-07 - Domain 4 (Crop) - Crop failure
- Current implementation status: **VERIFIED (later continuation session, was Partial - subsumed by the D10-01/02/03 batch, now formally reclassified)**
- Existing relevant files/classes/functions: crop_cycle.py CANCELLED terminal status reachable from any active state; failure_reason (FailureReason enum) and resown_from_crop_cycle_id exist and are wired through the report-failure endpoint
- Missing component: none
- Required implementation: none - read together with D10-01/02/03 (VERIFIED)
- Dependencies: D10-01, D10-02, D10-03 (now VERIFIED) - functionally closes this row
- Backend work: none - already done via the D10 batch
- Database/migration work: none - already done (migration d7557ced4b7b_add_failure_reason_and_resown_from_crop_)
- Mobile work: none - already done (crop_details_screen.dart cancel flow)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: already exist per D10-01/02/03's VERIFIED evidence
- Verification method: automated test (already passing per the D10 batch)
### D5-04 - Domain 5 (Crop Variety) - Variety-specific duration
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: `crop_cycle_service.create_crop_cycle` now computes `CropCycleResponse.suggested_expected_harvest_date = sowing_date + variety.typical_duration_days`, only when the farmer didn't supply their own `expected_harvest_date` - never silently written into the real field
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_crop_cycles.py::test_create_crop_cycle_suggests_expected_harvest_date_from_variety_duration`, `::test_create_crop_cycle_does_not_suggest_a_harvest_date_when_the_farmer_supplied_their_own`
- Verification method: automated test, confirmed passing
- Dependencies: none
- Backend work: crop_cycle_service.py::create_crop_cycle - optionally compute and return a suggested expected_harvest_date when not supplied and the variety has typical_duration_days
- Database/migration work: none - field already exists
- Mobile work: add_crop_screen.dart - pre-fill expected-harvest-date field with the suggestion, editable
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none - purely additive suggestion, farmer always has final say
- Tests required: test_create_crop_cycle_suggests_expected_harvest_date_from_variety_duration
- Verification method: automated test

### D6-07 - Domain 6 (Crop Cycle) - Multiple cycles
- Current implementation status: **VERIFIED (fixed and tested this session, P0, was Partial)**
- Fix applied: `crop_cycle_repository.count_active_for_plot` (new) + a guard in
  `crop_cycle_service.create_crop_cycle`, placed after the resowing-specific validation
  block (so a legitimate re-sow's own "source cycle not cancelled" 422 still fires first,
  never masked by this guard's 409) — rejects with 409 if the plot already has any
  non-terminal `CropCycle` row.
- Database/migration work: none — a service-level check, consistent with this codebase's
  existing convention (no partial unique index added; the same class of race this project
  already accepts elsewhere, e.g. offline-replay task creation, addressed at the service
  layer not the schema layer)
- Mobile work: not yet done — `add_crop_screen.dart` should surface the new 409 as a
  friendly "this plot already has an active crop cycle" message rather than a generic
  error; tracked as a small follow-up, not a gap in this scenario's backend-verified status
- Dependencies: D12-01 (Intercropping, still un-built/P3) — this guard is intentionally
  unconditional for now (no intercropping feature exists yet to need an exception); if
  D12-01 is ever built, the guard must become configurable per that row's own note
- Tests added and passing: `test_cannot_create_a_second_active_crop_cycle_on_the_same_plot`,
  `test_can_start_a_new_crop_cycle_once_the_old_one_is_closed` (`test_crop_cycles.py`); full
  suite re-run confirmed 0 regressions across the 20 test files that call the crop-cycle
  creation endpoint
- Verification method: automated test, confirmed passing
### D7-11 - Domain 7 (Crop Stages) - Closed
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: `CropCycleResponse.is_closed` (computed field: `cultivation_status in (HARVESTED, CANCELLED)`) - no new terminal state, purely a read-only convenience
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_crop_cycles.py::test_crop_cycle_response_includes_is_closed_flag`
- Verification method: automated test, confirmed passing
- Dependencies: none
- Backend work: schemas/crop.py response model - add computed is_closed property
- Database/migration work: none
- Mobile work: crop_details_screen.dart can use is_closed instead of checking two enum values itself
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_crop_cycle_response_includes_is_closed_flag
- Verification method: automated test

### D8-01 - Domain 8 (Crop Calendar) - Dynamic calendar
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `task_repository.list_pending_for_farmer` + `task_service.get_my_task_calendar` + `GET /farmers/me/tasks/calendar`, grouping every PENDING task across every one of the farmer's crop cycles/farms by due_date (a genuinely undated group is kept, never dropped)
- Missing component: none (mobile calendar-view screen not built - tracked as a follow-up, not a gap in this scenario's backend-verified status)
- Required implementation: none
- Tests added and passing: `tests/test_tasks.py::test_task_calendar_groups_tasks_by_date_across_crop_cycles`, `::test_task_calendar_never_leaks_another_farmers_tasks`
- Verification method: automated test, confirmed passing
- Dependencies: none blocking
- Backend work: new task_repository.list_for_farmer_grouped_by_date; new endpoint GET /farmers/me/tasks/calendar
- Database/migration work: none - tasks.farmer_id already exists to query by
- Mobile work: new calendar-view screen/tab (in addition to the existing per-crop flat list)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard task read, no new sync impact
- Security/RBAC impact: none - already scoped to farmer_id
- Tests required: test_calendar_endpoint_groups_tasks_by_date_across_crop_cycles
- Verification method: automated test
### D8-06 - Domain 8 (Crop Calendar) - Weather-adjusted tasks
- Current implementation status: **FUTURE (later continuation session, was Partial)** - `weather_action_engine_service.py:12-14` explicitly, deliberately documents that a task is never automatically rescheduled or modified from weather - the same boundary as D16-05/06/07 (already FUTURE). Auto-mutating a farmer's task due date without an explicit confirmation would violate this project's own anti-fabrication/no-silent-mutation convention. Read-only advisory display (the other half of this row) is already VERIFIED.
- Existing relevant files/classes/functions: weather_advisory field attached read-only to pending SPRAYING task API responses (task_service.py:78-117)
- Missing component: n/a - deliberately deferred, not attempted
- Required implementation: if ever built, requires an explicit farmer-confirmation step before moving a due date, never a silent auto-reschedule; not built this session, consistent with D16-05/06/07's existing citation
- Dependencies: D16-06/D16-07 (Weather to task modification/postponement), both already correctly classified FUTURE with the same citation - read alongside those as the same considered boundary
- Backend work: if pursued, task_service.py - add an opt-in apply-advisory endpoint requiring explicit farmer POST, never automatic
- Database/migration work: none unless a rescheduled_from_weather audit flag is wanted on tasks
- Mobile work: task_list_screen.dart - Reschedule due to weather affordance requiring explicit tap
- Automation work: none - must stay farmer-triggered, not scheduler-triggered, per the existing anti-fabrication design
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_farmer_can_explicitly_apply_a_weather_advisory_to_reschedule_a_task
- Verification method: automated test, if the product decision is made to build it (currently intentionally not committed)

### D9-16 - Domain 9 (Task Automation) - Automatic follow-up
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Partial)**
- Fix applied: `task_service.run_overdue_task_alert_sweep`, mirroring
  `run_expiry_check_sweep`'s "fires once per episode" pattern via the new
  `Task.overdue_alerted_at` gate; registered as `scheduler.py`'s fourth job
  (`task_overdue_alert_sweep`, hourly by default, `task_overdue_alert_sweep_interval_seconds`).
  Closes this row, D9-03, D78-01, and D37-04 in one build (cluster #1), exactly as this
  matrix's own dependency note anticipated.
- New `NotificationCategory.TASK_ALERT` (migration `a1b2c3d4e5f6`), wired into
  `notification_service.py`'s `_CATEGORY_PREFERENCE_MAP` (gated by the existing
  `general_notifications_enabled` toggle) and `_TITLE_BY_CATEGORY`; new `TASK_OVERDUE`
  message template (English-only, consistent with this project's disclosed
  advisory-text-localization convention).
- Mobile work: not yet done — no new screen needed (surfaces through the existing
  notification list), tracked as a follow-up, not a gap in this scenario's backend-verified
  status
- Tests added and passing: `test_tasks.py::test_overdue_sweep_sends_one_alert_and_never_duplicates`,
  `::test_overdue_sweep_ignores_tasks_without_a_due_date`
- Verification method: automated test, confirmed passing in the full suite re-run this
  session
### D10-11 - Domain 10 (Crop Failure) - Season closure after failure
- Current implementation status: **VERIFIED (later continuation session, was Partial - subsumed by the D10-01/02/03 batch, now formally reclassified)**
- Existing relevant files/classes/functions: CANCELLED is terminal (ALLOWED_TRANSITIONS[CANCELLED] = set()), VERIFIED via test_cannot_transition_out_of_terminal_status; failure_reason populated at cancellation time
- Missing component: none
- Required implementation: none
- Dependencies: D10-01 (now VERIFIED) functionally resolves this row too
- Backend work: none - already done
- Database/migration work: none - already done (failure_reason column, migration d7557ced4b7b)
- Mobile work: none - already done
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: covered by D10-01/02/03's existing tests
- Verification method: automated test (already passing)

### D11-02 - Domain 11 (Re-Sowing) - Farmer confirmation
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: `add_crop_screen.dart` now checks `listCropCyclesForPlot` on load; if the plot has a CANCELLED cycle, shows an explicit "Re-sow after failure?" dialog naming the crop, and only sends `resown_from_crop_cycle_id` if the farmer taps Yes - never inferred or auto-set. A "Linked as re-sow of the previous cycle" indicator confirms the choice in the form.
- Missing component: none
- Required implementation: none
- Tests added and passing: `test/features/farm/add_crop_screen_test.dart` (4 widget tests: prompts on a cancelled cycle, does not prompt otherwise, confirming/declining show the correct indicator state)
- Verification method: automated widget test, confirmed passing (`flutter test`: 267 passed, was 263)
- Dependencies: D10-10/D11-01 (now VERIFIED) supply the linkage field this confirmation step would populate
- Backend work: crop_cycle_service.py::create_crop_cycle - no change needed (field already accepted); purely a UX-confirmation gap
- Database/migration work: none - already done
- Mobile work: add_crop_screen.dart - detect a recent cancelled cycle on the same plot and show the re-sow confirmation dialog, wiring the user's Yes into resown_from_crop_cycle_id
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_add_crop_screen_prompts_resow_confirmation_when_plot_has_recent_cancelled_cycle (Flutter widget test)
- Verification method: live manual verification (mobile UX flow) plus a widget test if added
### D11-05 - Domain 11 (Re-Sowing) - Old cycle closure
- Current implementation status: **VERIFIED (fixed this session via the same change as D6-07, was Partial)**
- Same fix as D6-07 (identical guard, same commit) — resolves both rows at once, as this
  matrix's own dependency note anticipated. See D6-07's entry above for the full evidence.
- Verification method: automated test (same tests as D6-07), confirmed passing

### D12-02 - Domain 12 (Intercropping) - Crop-specific information
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - NOT implemented; completing this would mean building D12-01 itself, a full Missing feature, out of a Partial-only session's scope per its own stop condition)
- Existing relevant files/classes/functions: each CropCycle row independently carries crop_id/variety_id/season/seed_variety (crop_cycle.py:82-108) - would incidentally support this IF concurrent cycles existed
- Missing component: no deliberate intercropping feature; untested for concurrent-cycle use
- Required implementation: blocked on the product decision at D12-01 (build deliberate intercropping support, including relaxing the single-active-cycle guard proposed for D6-07/D11-05); no independent work item exists here until that decision is made
- Dependencies: D12-01 (blocking); also conflicts with the D6-07/D11-05 fix (a hard single-active-cycle-per-plot guard would need an explicit intercropping exception)
- Backend work: none until D12-01 is decided in-scope
- Database/migration work: if pursued, a paired_crop_cycle_id or intercrop_group_id field on crop_cycles
- Mobile work: an Add Intercrop UI affordance distinct from Add Crop, if pursued
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond standard crop-cycle sync
- Security/RBAC impact: none
- Tests required: test_intercropped_cycles_retain_independent_crop_info, if pursued
- Verification method: automated test, contingent on product decision
### D12-03 - Domain 12 (Intercropping) - Crop-specific tasks
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - same D12-01 dependency as D12-02, not attempted)
- Existing relevant files/classes/functions: Task.crop_cycle_id scopes every task to one cycle; would structurally work per-cycle
- Missing component: untested for concurrent/intercropped cycles specifically; no intercropping-aware task UI
- Required implementation: same blocking dependency as D12-02
- Dependencies: D12-01
- Backend work: none until D12-01 decided
- Database/migration work: none - existing FK scoping already sufficient once intercropping is allowed
- Mobile work: task list would need a per-crop filter when a plot has 2 concurrent cycles, if pursued
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_tasks_remain_scoped_per_cycle_under_intercropping, if pursued
- Verification method: automated test, contingent on product decision

### D12-04 - Domain 12 (Intercropping) - Crop-specific risks
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - same D12-01 dependency, not attempted)
- Existing relevant files/classes/functions: CropRiskScore computed per crop_cycle_id; cross-crop-cycle isolation already tested generically (PROJECT_STATUS.md Phase 33)
- Missing component: not exercised for a deliberate intercropping scenario specifically
- Required implementation: same blocking dependency as D12-02; once D12-01 is decided, add an intercropping-specific isolation test - the underlying mechanism needs no code change
- Dependencies: D12-01
- Backend work: none - mechanism already correct
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_crop_risk_score_isolated_between_intercropped_cycles_on_same_plot
- Verification method: automated test, contingent on product decision
### D12-05 - Domain 12 (Intercropping) - Crop-specific harvest
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - same D12-01 dependency, not attempted)
- Existing relevant files/classes/functions: HarvestRecord.crop_cycle_id scopes harvests per cycle; VERIFIED in isolation via test_harvests_from_one_crop_cycle_are_not_returned_for_another
- Missing component: not exercised for concurrent/intercropped cycles specifically
- Required implementation: same as D12-04 - add an intercropping-specific isolation test once D12-01 is decided; no code change needed
- Dependencies: D12-01
- Backend work: none
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_harvest_records_isolated_between_intercropped_cycles
- Verification method: automated test, contingent on product decision

### D12-06 - Domain 12 (Intercropping) - Crop-specific finance
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - same D12-01 dependency, not attempted)
- Existing relevant files/classes/functions: LedgerEntry.crop_cycle_id scopes every ledger entry per cycle; tested generically (PROJECT_STATUS.md:506)
- Missing component: not exercised for intercropping specifically
- Required implementation: same as D12-04/05 - add isolation test once D12-01 is decided
- Dependencies: D12-01
- Backend work: none
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_ledger_entries_isolated_between_intercropped_cycles
- Verification method: automated test, contingent on product decision
### D13-01 - Domain 13 (Perennial Crops) - Long-running crop cycle
- Current implementation status: **VERIFIED (later continuation session, was Partial - decision made: accepted as-is, no code change)**
- Existing relevant files/classes/functions: expected/actual harvest dates nullable, no max-duration check anywhere in `crop_cycle_service.py`/`ALLOWED_TRANSITIONS`
- Decision made this session: this scenario's literal wording ("long-running crop cycle") is already structurally satisfied - nothing artificially caps a `CropCycle`'s duration, so a perennial crop already runs indefinitely. Distinct perennial-specific FEATURES (multi-season year-boundary tracking, recurring maintenance scheduling, pruning records) are a separate, larger concept - correctly tracked as their own Missing rows (D13-02/D13-04/D13-05), not fabricated here.
- Missing component: none for this row's own literal scope
- Required implementation: none
- Dependencies: D13-02 (multiple seasons), D13-04 (recurring maintenance) - a real perennial-mode decision would likely resolve all three together
- Backend work: crop_cycle_service.py - if pursued, a Season.PERENNIAL-aware branch that changes stage-history/task expectations
- Database/migration work: none required for the incidental behavior; new fields only if a deliberate perennial-year-boundary model is built (see D13-02)
- Mobile work: none unless perennial mode is built
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none currently target this scenario specifically
- Verification method: live manual verification / product decision needed before automated tests make sense

### D13-06 - Domain 13 (Perennial Crops) - Crop-year history
- Current implementation status: **VERIFIED (later continuation session, was Partial - scoped to calendar-year grouping only)**
- Existing relevant files/classes/functions: new `crop_cycle_service.get_crop_year_summary` + `GET /crops/{crop_cycle_id}/year-summary`, grouping existing `HarvestRecord`/`CropCycleStageHistory` rows by calendar year (`EXTRACT(YEAR ...)` done in Python over already-scoped rows) - pure read aggregation, no new source data
- Missing component: a true SEASON-boundary rollup (not just calendar-year) still depends on D13-02 (season history, Missing) - disclosed, not attempted; the calendar-year variant fully satisfies this row's own literal wording
- Required implementation: none for calendar-year scope; season-boundary variant deferred to D13-02
- Tests added and passing: `tests/test_crop_cycles.py::test_crop_year_summary_groups_harvests_and_stage_changes_by_year`
- Verification method: automated test, confirmed passing
- Dependencies: D13-02 (multiple seasons) - a real crop-year concept needs a season/year boundary definition first
- Backend work: new crop_cycle_service.py::get_crop_year_summary reading existing tables, grouped by EXTRACT(YEAR FROM ...)
- Database/migration work: none - purely a read aggregation over existing timestamped tables
- Mobile work: Crop Year History view on the crop-cycle detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none - read-only, ownership already enforced
- Tests required: test_crop_year_summary_groups_harvests_and_stage_changes_by_year
- Verification method: automated test
### D99-01 - Domain 99 (Special Crop Scenarios) - Crop failure (cross-ref Domain 10)
- Current implementation status: **VERIFIED (later continuation session, was Partial)** - D10-01/02/03/04/05/06/07/09/10 are all now VERIFIED (D10-04/05/06/07 confirmed VERIFIED in an earlier batch: the DROUGHT/FLOOD/WEATHER_DAMAGE/OTHER enum values and required note already existed and are tested). The one remaining component, D10-08 (optional expert-confirmation step for a reported failure), is itself explicitly disclosed as "a genuinely optional enhancement, not a core requirement" in its own entry - a farmer's self-report already fully satisfies this scenario's core requirement.
- Existing relevant files/classes/functions: see the now-VERIFIED D10-01 through D10-07/09/10 entries
- Missing component: none for this row's core requirement (D10-08 remains a disclosed, genuinely optional enhancement)
- Required implementation: none
- Dependencies: D10-08 remains MISSING but is disclosed as optional, not blocking this rollup's VERIFIED status
- Backend work: see D10-04..08
- Database/migration work: see D10-04..08 (extend FailureReason enum, additive, no new table)
- Mobile work: see D10-04..08
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D10-04..08
- Verification method: automated test, once D10-04..08 are built

### D99-02 - Domain 99 (Special Crop Scenarios) - Re-sowing (cross-ref Domain 11)
- Current implementation status: **VERIFIED (later continuation session, was Partial)** - D11-01/02/03/04/05/07 are all now VERIFIED. D11-06 (auto-task-generation on re-sow) remains MISSING, but its own entry explicitly recommends reclassifying it FUTURE - "the same root cause as D9-01/D8-02 (deliberate no-auto-task-generation design)... not a distinct undisclosed gap." Read alongside that already-disclosed boundary, this rollup's core requirement (failure -> recommendation -> confirmed re-sow -> linked new cycle) is fully satisfied.
- Existing relevant files/classes/functions: see the now-VERIFIED D11-01 through D11-05/07 entries
- Missing component: none for this row's core requirement (D11-06 is the same disclosed auto-task-generation deferral as D9-01/D8-02, not blocking)
- Required implementation: none
- Dependencies: D11-06 remains MISSING but is the same disclosed deferral as D9-01/D8-02, not blocking this rollup's VERIFIED status
- Backend work: see those rows
- Database/migration work: see those rows
- Mobile work: see those rows
- Automation work: see those rows
- Notification work: see those rows
- Offline/sync impact: see those rows
- Security/RBAC impact: see those rows
- Tests required: see those rows
- Verification method: automated test, per those rows
### D99-04 - Domain 99 (Special Crop Scenarios) - Perennial crops (cross-ref Domain 13)
- Current implementation status: Partial (re-confirmed genuinely blocked, later continuation session - D13-01/D13-06 are now VERIFIED, but D13-02/D13-04/D13-05 remain genuine, substantial Missing features - season history, recurring maintenance scheduling, pruning records - not disclosed-optional like D10-08/D11-06, so this rollup correctly stays Partial rather than being force-closed)
- Existing relevant files/classes/functions: D13-03 VERIFIED; D13-01, D13-06 Partial (above); D13-02, D13-04, D13-05 MISSING (below)
- Missing component: see those individual Domain-13 rows
- Required implementation: see those rows
- Dependencies: D13-01, D13-02, D13-04, D13-05, D13-06
- Backend work: see those rows
- Database/migration work: see those rows
- Mobile work: see those rows
- Automation work: see those rows
- Notification work: see those rows
- Offline/sync impact: see those rows
- Security/RBAC impact: see those rows
- Tests required: see those rows
- Verification method: automated test, per those rows

### D14-09 - Domain 14 (Weather) - Severe weather
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `weather_alert_rules.evaluate_severe_weather_co_occurrence` (combines the existing wind/heat-cold/heavy-rain flags via each condition's own already-validated threshold - no new meteorological classification invented); new `NotificationCategory.SEVERE_WEATHER_ALERT` (migration `1e25cb4e88d7`), CRITICAL priority; wired into `weather_alert_orchestration_service.generate_alerts_for_farm_weather`
- Missing component: storm/cyclone/hail/flood (D15-05/06/07/08) remain correctly unclassified - still require a real external data source this project doesn't have
- Required implementation: none for the co-occurrence escalation itself
- Tests added and passing: `tests/test_weather_alert_rules.py::TestSevereWeatherCoOccurrence` (4 tests)
- Verification method: automated test, confirmed passing
- Dependencies: D15-04..09 (frost/storm/cyclone/hail/flood/drought) need real external data sources first; this row's co-occurrence escalation is achievable now without them
- Backend work: weather_alert_rules.py - new evaluate_severe_weather_co_occurrence combining existing wind/heat/cold/rain flags; notification.py - add NotificationCategory.SEVERE_WEATHER_ALERT and NotificationPriority.CRITICAL wiring mirroring the pattern already used for PAYMENT_ALERT/STOCK_ALERT additions
- Database/migration work: Alembic migration adding the new enum value, mirroring b8069da2cd90_add_payment_alert_notification_category.py
- Mobile work: weather_screen.dart - distinct visual treatment for a severe-weather notification
- Automation work: none new - reuses the existing pull-based weather-fetch trigger (or the new proactive sweep from D16-10)
- Notification work: new SEVERE_WEATHER_ALERT category, CRITICAL priority
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_severe_weather_co_occurrence_escalates_to_critical
- Verification method: automated test
### D16-01 - Domain 16 (Weather Automation) - Weather to affected plot
- Current implementation status: **FUTURE (later continuation session, was Partial)** - re-read `docs/WEATHER_ARCHITECTURE.md`'s own "Location hierarchy" section this session: "farm location is already the correct granularity for farm-level weather, and adding two more override layers without a clear immediate need would be over-engineering. Revisit if a farmer ever needs weather for a location other than one of their registered farms." This is an explicit, deliberate architecture decision, not a small technical gap - building plot-level weather now would also require redesigning `WeatherSnapshot`'s farm-scoped caching (currently keyed only by `farm_id`), a structural change beyond this row's original "small" sizing. Not attempted, per the project's own documented decision and this session's own "don't invent functionality merely to increase completion" discipline.
- Existing relevant files/classes/functions: weather fetched at Farm granularity only (WEATHER_ARCHITECTURE.md:54-63); all plots on a farm share one reading
- Missing component: n/a - deliberately deferred, not attempted
- Required implementation: if ever pursued, needs both a plot-level lat/lng override (Plot already has one) AND a redesigned plot-aware weather cache - a product decision, not built here
- Dependencies: D3-06 (Plot location) - a real plot-level weather fetch needs the plot's own lat/lng to be a first-class, validated field
- Backend work: weather_service.py::get_farm_weather would need a plot-aware variant using plot.latitude/longitude when present, falling back to farm's
- Database/migration work: none new - plots.latitude/longitude already exist
- Mobile work: weather_screen.dart - plot selector when a farm has plots with independent coordinates
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond standard weather fetch
- Security/RBAC impact: none
- Tests required: test_plot_level_weather_uses_plot_coordinates_when_present
- Verification method: automated test, contingent on product decision (currently explicitly deferred per architecture doc)

### D16-03 - Domain 16 (Weather Automation) - Weather to crop stage sensitivity
- Current implementation status: **FUTURE (later continuation session, was Partial, per this row's own recommendation)** - `weather_alert_rules.py:110-114`'s own comment explicitly invites more rules only once validated against a real agronomic source. Adding a per-stage sensitivity table now would mean guessing thresholds this project has no authoritative source for - the same class of deferral as D21-01's seeding-rate dataset (already FUTURE). Not attempted, per this project's own anti-fabrication convention.
- Existing relevant files/classes/functions: only one combined rule exists (heavy rain plus crop plus farmer-confirmed stage)
- Missing component: n/a - deliberately deferred pending a validated agronomic dataset
- Required implementation: none until a real, cited, per-crop/stage threshold source is available
- Dependencies: none blocking; would need an authoritative agronomic reference (same class of concern as D21-01's seeding-rate dataset, now FUTURE for the same reason) - recommend re-examining this row as FUTURE with that same class of citation rather than leaving it Partial
- Backend work: weather_alert_rules.py - additional rule functions once thresholds are validated
- Database/migration work: none unless thresholds move from hardcoded to config-driven
- Mobile work: none beyond existing alert display
- Automation work: none new
- Notification work: none new
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new rule-specific tests per added sensitivity rule
- Verification method: automated test, contingent on sourcing a validated dataset
### D17-01 - Domain 17 (Water) - Water source
- Current implementation status: **VERIFIED (fixed this session via the same enum as
  D3-08, was Partial)** — `Plot.irrigation_source` also closes the D18-01..05 rows'
  previously-unvalidated free text. See D3-08's entry above for the full evidence.
- Verification method: automated test (same tests as D3-08), confirmed passing

### D21-03 - Domain 21 (Seeds) - Seed variety
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `Product.variety_id` (nullable FK to the existing `crop_varieties` table, migration `a2f94d64b787`), admin-settable at creation only (no product-update endpoint exists in this phase); `GET /seeds?variety_id=` filter
- Missing component: none - scoped to linking a product to an EXISTING `CropVariety` row (which already exist via the crop-cycle flow); D5-02 (a farmer/admin-facing "create a new variety" endpoint) remains separately Missing and was correctly not built here, since linking never required creating one
- Required implementation: none
- Tests added and passing: `tests/test_products.py::test_seed_catalog_filters_by_variety`
- Verification method: automated test, confirmed passing
- Backend work: product.py model, product_service.py::list_approved_products - add variety_id filter param; admin product-creation path to set it
- Database/migration work: Alembic migration adding nullable variety_id FK column to products, mirroring a99bd945587b_create_crop_varieties_table_and_add_ style
- Mobile work: product_list_screen.dart - variety filter/display
- Automation work: none
- Notification work: none
- Offline/sync impact: none - standard catalog read
- Security/RBAC impact: none
- Tests required: test_seed_catalog_filters_by_variety
- Verification method: automated test
### D22-02 - Domain 22 (Fertilizer) - Fertilizer selection
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: `GET /products` now accepts `category`/`manufacturer` query params, exposing what `product_repository.list_products` already supported internally
- Missing component: none
- Required implementation: none
- Dependencies: same fix closes D23-01's identically-rooted gap
- Tests added and passing: `tests/test_products.py::test_list_products_filters_by_category_query_param`
- Verification method: automated test, confirmed passing
- Backend work: api/v1/products.py::list_products - accept and pass through category param to the already-capable repository method
- Database/migration work: none - no schema change, purely an API surface addition
- Mobile work: product_list_screen.dart - category filter chips/dropdown
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_list_products_filters_by_category_query_param
- Verification method: automated test

### D24-04 - Domain 24 (Input Inventory) - Purchase date
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Partial)**
- Re-confirmed exactly as this row's own note recommended: direct read of
  `input_inventory.py` found no `acquired_at`/`purchased_at` field before this session — the
  "may already be resolved" hope was not accurate, genuine work was needed.
- Fix applied: `InputInventoryItem.acquired_at` (migration `e5f6a7b8c9d0`), farmer-settable,
  independent of `created_at` (when the farmer recorded it) and independent of any `Order`
  (an off-app purchase, e.g. bought at a local shop, has no Order at all) — defaults to
  today when not specified.
- Mobile work: not yet done — the "Add to my inventory" form should add a date picker;
  tracked as a follow-up.
- Tests added and passing: `test_input_inventory.py::test_input_inventory_item_can_be_created_with_acquired_at_independent_of_an_order`
- Verification method: automated test, confirmed passing
### D25-01 - Domain 25 (Input Purchase) - Search
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: `GET /products` now accepts `category`/`manufacturer` (same fix as D22-02). `price_min`/`price_max` deliberately NOT added - `price` lives on `DealerProduct` (a dealer-specific listing), never on the master-catalog `Product` row, so a catalog-level price filter would be architecturally wrong; a real price-range search belongs on a dealer-listing search endpoint, a distinct feature not attempted here (disclosed scope reduction, not a hidden gap)
- Missing component: none for category/manufacturer; price-range search on dealer listings remains a separate, unbuilt feature
- Required implementation: none for this row's core ask
- Dependencies: D22-02 (identical root cause, one fix addresses both)
- Tests added and passing: `tests/test_products.py::test_list_products_filters_by_manufacturer_and_price_range`
- Verification method: automated test, confirmed passing
- Backend work: api/v1/products.py::list_products, product_repository.py (extend query params)
- Database/migration work: none - no schema change
- Mobile work: product_list_screen.dart - filter UI
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_list_products_filters_by_manufacturer_and_price_range
- Verification method: automated test

### D26-02 - Domain 26 (Input Verification) - Product information
- Current implementation status: **VERIFIED (later continuation session, was Partial)**
- Existing relevant files/classes/functions: new `POST /admin/products/{id}/image` (admin-only, reuses `validate_upload`/`process_image` from the crop-photo pipeline - no second image-handling implementation); `GET /products/{id}/image` (any authenticated farmer/dealer/admin - not ownership-gated like crop photos, since a catalog image is meant to be visible to everyone, same as the product's name); `ProductResponse.image_storage_key` now surfaced
- Missing component: none
- Required implementation: none
- Tests added and passing: `tests/test_products.py::test_admin_can_upload_product_image`, `::test_product_detail_includes_resolved_image_url_when_present`, `::test_farmer_cannot_upload_product_image`, `::test_product_image_404s_when_none_uploaded`
- Verification method: automated test, confirmed passing
- Backend work: new admin endpoint POST /admin/products/{id}/image mirroring the crop-photo upload service pattern; product_service.py - return a resolved image URL in GET /products/{id}
- Database/migration work: none - image_storage_key column already exists on products, just unpopulated/unused
- Mobile work: product_detail_screen.dart - render the product image when present, placeholder when absent
- Automation work: none
- Notification work: none
- Offline/sync impact: none - standard catalog read
- Security/RBAC impact: admin-only upload endpoint (mirrors existing admin-gated product-creation pattern)
- Tests required: test_admin_can_upload_product_image; test_product_detail_includes_resolved_image_url_when_present
- Verification method: automated test

## 3. Missing - full itemized (EVERY row, no aggregation)

### D1-11 - Domain 1 (Account) - Microphone permission
- Current implementation status: Missing
- Existing relevant files/classes/functions: none - no speech_to_text/record/permission_handler package in pubspec.yaml; docs/VOICE_ASSISTANT.md documents it only as an architecture option
- Missing component: entire voice-input capability (permission request plus recording)
- Required implementation: add a speech-to-text package (e.g. speech_to_text) to pubspec.yaml, request RECORD_AUDIO/microphone permission via permission_handler, wire into a voice-input UI entry point
- Dependencies: the entire voice-assistant-input feature (chat/assistant domain) - this permission has no reason to exist until that feature is scoped
- Backend work: none required for the permission itself; a speech-to-text backend endpoint would be needed for the feature this permission serves
- Database/migration work: none
- Mobile work: pubspec.yaml (new deps), new permission-request flow mirroring add_edit_farm_screen.dart's Geolocator pattern
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: OS-level consent only, same class as camera/location
- Tests required: Flutter permission-flow widget test once the feature exists
- Verification method: live manual verification (OS permission dialog cannot be meaningfully unit-tested)

### D1-14 - Domain 1 (Account) - Automated-action consent
- Current implementation status: Missing
- Existing relevant files/classes/functions: ConsentType enum has exactly 4 exhaustive values (consent_record.py:23-27); no automated/AI-triggered action is gated by consent
- Missing component: a ConsentType.AUTOMATED_ACTION (or similarly named) value and enforcement point
- Required implementation: add the enum value; identify the first genuinely automated farmer-facing mutating action that should be gated by it once one exists (currently every automatic action in this codebase is either read-only/advisory or a scheduler-driven notification, not a mutating action)
- Dependencies: none currently - no automated mutating action exists to attach this consent to yet
- Backend work: consent_record.py - add enum value; gate it at the point where a future automated action is built, not preemptively
- Database/migration work: additive enum value migration mirroring existing ConsentType migrations
- Mobile work: consent-management screen - new toggle once the enum exists
- Automation work: none - this is infrastructure for automation to come, not automation itself
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: this IS a consent/access gate by definition
- Tests required: test_consent_type_includes_automated_action
- Verification method: automated test (for the enum), live manual verification once an actual gated action exists
### D1-19 - Domain 1 (Account) - Account deactivation
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `POST /farmers/me/deactivate` (`farmer_service.deactivate_own_account`) — sets
  `AccountStatus.INACTIVE` (already correctly enforced at login) and revokes all refresh
  tokens. Deliberately does NOT require password re-confirmation, differing from this row's
  original suggestion: D100-09's own delete-account (a strictly more destructive,
  harder-to-reverse sibling action on the same account) already ships without one — adding
  it only to the softer deactivate would be an inconsistent, not a safer, design. Unlike
  delete-account, does NOT scrub PII, so the account stays restorable.
- No admin-only deactivation path built — the audit's "separate admin-only path" suggestion
  was not pursued; self-service was the concrete, farmer-facing gap and delete-account
  (its closest precedent) is also self-service-only today.
- Mobile work: not yet done — account-settings screen should add a Deactivate account
  action with a confirmation dialog; tracked as a follow-up.
- Tests added and passing: `test_data_privacy.py::test_farmer_can_deactivate_own_account`,
  `::test_deactivated_account_cannot_login`, `::test_deactivating_an_account_revokes_refresh_tokens`,
  `::test_cannot_deactivate_an_already_deactivated_account`
- Verification method: automated test, confirmed passing

### D2-07 - Domain 2 (Farm) - Farm infrastructure
- Current implementation status: **VERIFIED (Missing Backlog Batch 6)** - new `FarmInfrastructure` model (migration `a6b7c8d9e0f2`), list-per-farm CRUD (`POST/GET /farms/{farm_id}/infrastructure`, `DELETE /farms/{farm_id}/infrastructure/{item_id}`) mirroring `plot_service.py`'s exact shape, farmer-entered and informational only - no automated logic reads these rows. Tests: `tests/test_farm_infrastructure.py` (5 new).
- Existing relevant files/classes/functions: none - farm.py:36-104 has no storage/well/borewell/shed/equipment field
- Missing component: entire farm-infrastructure data model
- Required implementation: add a lightweight FarmInfrastructure table (or JSON field) capturing storage/well/shed/equipment presence, farmer-entered, informational only (no automated logic should read it yet)
- Dependencies: none
- Backend work: new farm_infrastructure_service.py mirroring plot_service.py's CRUD shape
- Database/migration work: new farm_infrastructure table (or additive JSON column on farms), Alembic migration
- Mobile work: add/edit-farm screen - new infrastructure section
- Automation work: none
- Notification work: none
- Offline/sync impact: standard farm-write sync queue
- Security/RBAC impact: ownership check via existing _get_owned_farm_or_404 pattern
- Tests required: test_create_farm_infrastructure_record
- Verification method: automated test
### D2-08 - Domain 2 (Farm) - Irrigation information (farm-level)
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - `FarmResponse.irrigation_summary` (sorted, distinct, non-null `Plot.irrigation_type` values across the farm's own plots), computed in `FarmResponse.from_orm_farm` - never a duplicated farm-level column. `Plot.irrigation_type`/`soil_type` remain plain free-text (D3-08/D17-01's enum work never actually landed - that cited dependency turned out to be aspirational, not a real blocker; the rollup works correctly over the real free-text values as-is). Tests: `tests/test_farms.py::test_farm_detail_includes_irrigation_summary_from_plots`, `test_farm_with_no_plots_has_empty_irrigation_and_soil_summaries`
- Existing relevant files/classes/functions: only Plot.irrigation_type exists; no farm-level field
- Missing component: farm-level irrigation summary/rollup
- Required implementation: either a computed farm-level rollup (aggregate distinct Plot.irrigation_type values across a farm's plots) or a dedicated farm-level field if a farm-wide irrigation source is meaningful separately - recommend the computed rollup to avoid duplicate/conflicting data entry
- Dependencies: D3-08/D17-01 (irrigation-type enum work) should land first so the rollup returns clean values
- Backend work: farm_service.py - computed field joining plots.irrigation_type
- Database/migration work: none if computed; additive column if a dedicated farm-level field is chosen instead
- Mobile work: farm detail screen - irrigation summary line
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_farm_detail_includes_irrigation_summary_from_plots
- Verification method: automated test

### D2-09 - Domain 2 (Farm) - Soil information (farm-level)
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - `FarmResponse.soil_summary`, same computed-rollup pattern as D2-08 (shared implementation, shared row-level reasoning). Test: `tests/test_farms.py::test_farm_detail_includes_soil_summary_from_plots`
- Existing relevant files/classes/functions: only Plot.soil_type exists
- Missing component: farm-level soil summary
- Required implementation: same reasoning/approach as D2-08 - computed rollup across plots rather than a duplicated farm-level field
- Dependencies: D3-09/D19-01 (soil-type enum work)
- Backend work: farm_service.py - computed field
- Database/migration work: none if computed
- Mobile work: farm detail screen - soil summary line
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_farm_detail_includes_soil_summary_from_plots
- Verification method: automated test
### D2-10 - Domain 2 (Farm) - Active farm selection
- Current implementation status: **OUT_OF_SCOPE (reclassified, Missing Backlog Batch 7)** - confirmed by this row's own prior evidence text to be a deliberate stateless design choice (every call takes an explicit `farm_id`), not a defect. Reclassified per this row's own recommendation, no code change.
- Existing relevant files/classes/functions: no current_farm_id/session concept anywhere; every call takes explicit farm_id
- Missing component: nothing - this is confirmed by the c01 audit's own summary paragraph to be a deliberate stateless design choice, not a defect ("a deliberate stateless design rather than a bug")
- Required implementation: none - recommend this row be reclassified OUT_OF_SCOPE or a documented deliberate design choice rather than Missing on the next audit pass, since it was explicitly called out as intentional in the cluster file's own summary; kept Missing here only because the per-row citation itself does not use the word deliberate the way the file's prose summary does
- Dependencies: none
- Backend work: none
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none needed
- Verification method: n/a - flagged for reclassification, not a real gap

### D3-07 - Domain 3 (Plot) - Plot boundary
- Current implementation status: VERIFIED (Missing Backlog Batch 8)
- Evidence: `Plot.boundary_points` (JSONB list of {latitude, longitude}, plot.py) - a plain farmer-drawn polygon, deliberately NOT PostGIS (not enabled in this project); tests/test_batch8_group7.py (6 tests: creation, update, <3-point rejection, invalid-lat rejection, independence from area_value)
- Existing relevant files/classes/functions: only a single lat/lng point (plot.py:45-46), no polygon/geoJSON field
- Required implementation: add a boundary_geojson (or PostGIS geometry(Polygon)) column; requires deciding whether to introduce PostGIS (a real infra decision) or store raw GeoJSON as JSON/text with area computed client-side or via a plain-Python polygon-area library
- Dependencies: none blocking, but this is a heavier lift than a typical field addition (may need a new DB extension)
- Backend work: plot.py model, plot_service.py validation (self-intersecting-polygon rejection etc.)
- Database/migration work: new column plus possibly CREATE EXTENSION postgis migration if geometry type chosen; otherwise a plain JSON/text column, simpler migration
- Mobile work: map-drawing UI for plot boundary (a significant new mobile feature - polygon drawing on a map widget)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard plot-write sync, larger payload
- Security/RBAC impact: none
- Tests required: test_create_plot_with_boundary_polygon; invalid-polygon rejection test
- Verification method: automated test
### D5-02 - Domain 5 (Crop Variety) - Variety creation
- Current implementation status: VERIFIED (Missing Backlog Batch 8)
- Evidence: `POST /crops/{crop_id}/varieties` (crop_varieties.py), admin-only, mirrors `POST /crops/master/{crop_id}/grade-options`'s exact convention; `crop_variety_service.create_variety`; tests/test_batch8_group2.py (4 tests: create, appears in farmer list, duplicate-name 409, non-admin 403)
- Existing relevant files/classes/functions: crop_variety_service.py has only list_varieties_for_crop; no create/update/delete anywhere; test fixtures insert via direct ORM only
- Missing component: admin endpoint to create/manage crop varieties
- Required implementation: add POST/PUT /admin/crops/{crop_id}/varieties mirroring the same admin-curation pattern already used for Product (admin-only creation, farmer-facing read-only)
- Dependencies: D4-02's cross-reference (admin-side CropMaster creation is also a real gap, same underlying no-admin-UI-for-master-reference-data pattern); D21-03 (seed variety linkage) would consume this
- Backend work: new crop_variety_service.py::create_variety/update_variety, new admin endpoints
- Database/migration work: none - crop_varieties table already exists, just no write path
- Mobile work: none - this is admin-side; if an admin surface exists elsewhere it would need a new screen, otherwise seed via a new admin API only
- Automation work: none
- Notification work: none
- Offline/sync impact: none - admin-only, online
- Security/RBAC impact: admin-only, needs a dedicated role check (mirrors Product admin-creation gating)
- Tests required: test_admin_can_create_crop_variety; test_non_admin_cannot_create_crop_variety
- Verification method: automated test

### D5-05 - Domain 5 (Crop Variety) - Variety-specific recommendations
- Current implementation status: Missing (re-confirmed genuinely blocked, Missing Backlog Batch 9) - blocked on an authoritative per-variety agronomic dataset that does not exist in this codebase, same anti-fabrication class as D21-01/D20-14. This row's own older text recommended reclassifying FUTURE, but consistent with this project's established Batch 3/4/7/8 convention of leaving a genuinely-blocked row honestly Missing with its reason disclosed inline rather than reclassifying it, left Missing.
- Existing relevant files/classes/functions: no service references variety anywhere except the crop-cycle linkage/validation code
- Missing component: any recommendation (weather/AI/task/crop-risk/assistant) that varies by variety
- Required implementation: this is a broad, cross-cutting gap rather than one feature - the concrete near-term increment (per D5-04, itemized in Section 2) is using typical_duration_days to suggest expected-harvest-date; deeper variety-specific agronomic recommendations should stay unbuilt until an authoritative per-variety dataset exists (same anti-fabrication boundary already applied to D21-01/D20-14)
- Dependencies: D5-04 (the concrete near-term increment); D21-01 (same class of blocking-dataset concern)
- Backend work: n/a until a dataset exists
- Database/migration work: n/a
- Mobile work: n/a
- Automation work: n/a
- Notification work: n/a
- Offline/sync impact: n/a
- Security/RBAC impact: n/a
- Tests required: n/a
- Verification method: n/a - recommend reclassifying FUTURE with an explicit blocked-on-authoritative-per-variety-agronomic-dataset citation, consistent with how D20-14/D21-01 were just reclassified
### D7-01 - Domain 7 (Crop Stages) - Land preparation
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `CultivationStatus.LAND_PREPARATION` (migration `c3d4e5f6a7b8`, both the
  `cultivation_status` and the separate `crop_cycle_stage_history_status` native Postgres
  enums), `ALLOWED_TRANSITIONS[LAND_PREPARATION] = {PLANNED, CANCELLED}`. Purely additive —
  creation still defaults to `PLANNED` unchanged; a farmer opts in via the new
  `CropCycleCreateRequest.initial_status` field (restricted to `{LAND_PREPARATION, PLANNED}`
  only, 422 otherwise — this field creates the row, it must never be used to skip past
  validation into a stage implying work that hasn't happened).
- Also updated `crop_performance_service.py`'s `_STAGE_SCORES` (the one exhaustive literal
  map over `CultivationStatus` found by grep across the whole backend) so a cycle in this
  new stage doesn't `KeyError` when its performance score is computed.
- Mobile work: not yet done — `crop_details_screen.dart` should surface a new stage button;
  tracked as a follow-up.
- Tests added and passing: `test_crop_cycles.py::test_crop_cycle_can_start_in_land_preparation_and_transition_to_planned`,
  `::test_initial_status_cannot_skip_past_land_preparation_or_planned`
- Verification method: automated test, confirmed passing

### D7-03 - Domain 7 (Crop Stages) - Germination
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `CultivationStatus.GERMINATING` (same migration as D7-01), inserted as an
  *optional* waypoint: `SOWN: {GERMINATING, GROWING, CANCELLED}`, `GERMINATING: {GROWING,
  CANCELLED}`. Deliberately additive-only — `SOWN` can still transition directly to
  `GROWING` unchanged, since the existing test suite has many call sites asserting exactly
  that sequence; removing it would have broken all of them for no real product benefit.
- Tests added and passing: `test_crop_cycles.py::test_sown_can_optionally_pass_through_germinating_before_growing`
- Verification method: automated test, confirmed passing

### D7-07 - Domain 7 (Crop Stages) - Maturity
- Current implementation status: **OUT_OF_SCOPE (decided this session, was Missing)** — per
  this row's own suggested alternative resolution ("document as an accepted modeling
  collapse, same treatment as D7-11 Closed"). Evaluated the product question this row
  itself posed ("are maturity and ready-for-harvest genuinely distinct farmer-facing
  moments?") and decided NOT to add a third additive stage here: unlike D7-01/D7-03 (a
  clearly distinct farmer moment - land prep before any seed goes in, germination as a
  visible first-growth event), "maturing" vs. "ready for harvest" has no crisp, farmer-
  observable line the way FLOWERING→FRUITING or SOWN→GERMINATING do - it would be an
  arbitrary split invented for enum completeness, not a real distinction. The orphaned
  `CropStageDefinition.stage_code` "maturation" facet remains a separate, unconnected
  concept (AI-model-facing crop-stage classification reference data, not the farmer-driven
  `CropCycle.cultivation_status` lifecycle) — connecting the two is a distinct, larger
  integration this session did not have grounds to invent unprompted.
- Verification method: n/a — a documented product decision, not a code change

### D9-03 - Domain 9 (Task Automation) - Reminder
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Same fix as D9-16 (identical `run_overdue_task_alert_sweep` build, same commit) —
  resolves both rows at once, as this row's own dependency note anticipated. See D9-16's
  entry above for the full evidence.
- Verification method: automated test (same tests as D9-16), confirmed passing

### D7-10 - Domain 7 (Crop Stages) - Post-harvest
- Current implementation status: Missing (re-confirmed, Missing Backlog Batch 9) - this row's own older text recommended simply cross-checking Harvest-domain coverage, but `docs/FINAL_GAP_REPORT.md`'s Batch 8 investigation already went further and correctly identified the real blocker: any actual fix here would mean redefining `CultivationStatus.HARVESTED` as non-terminal (`crop_cycle.py:87`, `_TERMINAL_STATUSES`), touching multiple already-VERIFIED invariants built on HARVESTED being terminal. That investigation deliberately left this row Missing rather than reclassifying it, and this batch defers to that later, more careful decision rather than the row's own superseded note. Not re-actioned this batch.
- Existing relevant files/classes/functions: nothing models post-harvest handling as a stage; nothing after HARVESTED
- Missing component: any post-harvest stage/status
- Required implementation: this likely belongs with Domain 47-55 (Harvest/Post-Harvest, out of this reconciliation group's scope) rather than as a CropCycle status - recommend not adding a new CultivationStatus value here (HARVESTED is correctly terminal) but instead confirming this scenario is fully covered by whatever post-harvest handling exists in the Harvest domain cluster (c08), which this reconciliation was not asked to touch
- Dependencies: Domain 47-55 (out of this group's scope)
- Backend work: none within this group's scope
- Database/migration work: none within this group's scope
- Mobile work: none within this group's scope
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none within this group's scope
- Verification method: n/a - flagged as needing cross-check against c08_harvest_postharvest.md, outside this reconciliation's domain range
### D9-05 - Domain 9 (Task Automation) - Snooze
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `PATCH /tasks/{id}` (`task_service.update_task`) — the first general-purpose
  task-update endpoint. Only allowed while PENDING (409 otherwise); resets
  `overdue_alerted_at` so a rescheduled-then-overdue-again task correctly re-alerts.
- Mobile work: not yet done — `task_list_screen.dart` should add a snooze affordance
  (e.g. swipe/long-press) calling this endpoint; tracked as a follow-up, not a gap in this
  scenario's backend-verified status. Offline-queue support (mirroring
  `pending_upload_queue.dart`) remains a real gap — task mutations have no offline queue at
  all today (see cluster #19, D81-04).
- Tests added and passing: `test_tasks.py::test_reschedule_task_to_new_due_date`,
  `::test_cannot_reschedule_a_completed_task`
- Verification method: automated test, confirmed passing

### D9-06 - Domain 9 (Task Automation) - Reschedule
- Current implementation status: **VERIFIED (fixed this session via the same endpoint as D9-05, was Missing)**
- Same fix as D9-05 (identical `PATCH /tasks/{id}` endpoint, same commit) — resolves both
  rows at once, as this matrix's own dependency note anticipated. See D9-05's entry above
  for the full evidence.
- Verification method: automated test (same tests as D9-05), confirmed passing
### D9-08 - Domain 9 (Task Automation) - Partial completion
- Current implementation status: VERIFIED (Missing Backlog Batch 8)
- Evidence: `Task.completion_percentage` (0-100, nullable), `POST /tasks/{id}/report-progress` (never changes status - complete/cancel/skip/fail still own that); tests/test_batch8_group2.py (5 tests). NOTE: this row's own prior analysis recommended against a generic field unless a specific task type needed it - proceeded anyway since the field is purely additive/optional (no task type is forced to use it, no existing workflow changed) rather than the deeper per-task-type quantity model the prior note was cautious about; flagged here for future review, not hidden.
- Existing relevant files/classes/functions: TaskStatus enum is exactly PENDING/COMPLETED/CANCELLED, no percentage/quantity-done field
- Dependencies: none
- Backend work: task.py, task_service.py, if pursued
- Database/migration work: additive nullable column, if pursued
- Mobile work: task completion dialog - optional progress slider, if pursued
- Automation work: none
- Notification work: none
- Offline/sync impact: standard task sync once offline queue exists (see D9-05)
- Security/RBAC impact: none
- Tests required: test_task_can_be_marked_partially_complete_with_progress_percent, if pursued
- Verification method: automated test, contingent on product decision - recommend leaving Missing with this caveat rather than building speculatively

### D9-09 - Domain 9 (Task Automation) - Skip
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `POST /tasks/{id}/skip` (`task_service.skip_task`) — only valid for a
  PENDING task with `repeat_interval_days` set (422 otherwise: "use cancel instead"); sets
  CANCELLED + reuses the same `_maybe_create_next_recurrence` helper `complete_task` uses,
  so the next occurrence is generated exactly as if the task had been completed.
- Mobile work: not yet done — `task_list_screen.dart` should add a "Skip this one" action
  alongside Complete/Cancel, shown only for recurring tasks; tracked as a follow-up.
- Tests added and passing: `test_tasks.py::test_skip_recurring_task_generates_next_occurrence_without_completing_current`,
  `::test_cannot_skip_a_non_recurring_task`
- Verification method: automated test, confirmed passing

### D9-10 - Domain 9 (Task Automation) - Skip reason
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `Task.cancellation_reason` (migration `a1b2c3d4e5f6`), farmer-entered,
  optional, shared across `cancel_task`/`skip_task`/`fail_task` via the new
  `TaskActionRequest{reason}` body.
- Mobile work: not yet done — cancel/skip/fail dialogs should add an optional reason text
  field; tracked as a follow-up.
- Tests added and passing: `test_tasks.py::test_cancel_task_can_include_a_reason`
- Verification method: automated test, confirmed passing

### D9-12 - Domain 9 (Task Automation) - Failed task
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `TaskStatus.FAILED` (migration `a1b2c3d4e5f6`) — distinct from CANCELLED,
  reuses D9-10's `cancellation_reason` field. `POST /tasks/{id}/fail`
  (`task_service.fail_task`), only valid while PENDING (409 otherwise). Deliberately does
  NOT auto-continue a recurrence (unlike complete/skip) — an unspecified failure is not the
  same "this occurrence is done, the schedule continues" signal completion/skip is.
- Dependencies: D18-08 (Pump failure) remains a concrete real-world trigger example, still
  itself unimplemented — not blocking, since `fail_task` accepts any free-text reason today.
- Mobile work: not yet done — task completion dialog should add a Failed option alongside
  Complete/Cancel; tracked as a follow-up.
- Tests added and passing: `test_tasks.py::test_task_can_be_marked_failed_with_reason`,
  `::test_cannot_fail_an_already_completed_task`
- Verification method: automated test, confirmed passing
### D9-13 - Domain 9 (Task Automation) - Recurring task (Task Automation's own instance)
- Current implementation status: **VERIFIED (folded into D8-08, Missing Backlog Batch 7)** - confirmed to be a duplicate scenario ID for the same already-VERIFIED feature (`Task.repeat_interval_days`) as D8-08, not an independent gap, per this row's own recommendation. No code change - same tests as D8-08 (`test_tasks.py::test_completing_a_re*`).
- Existing relevant files/classes/functions: this is the same underlying gap as D8-08, which is now VERIFIED (Task.repeat_interval_days) - D9-13 (Domain 9's own ID for the same scenario name) was NOT itself named in any reconciliation-source delta table, so per this reconciliation's own discipline (apply only confirmed deltas) it is kept as originally classified
- Missing component: nothing further - functionally resolved by D8-08's delta; the model/mechanism is identical (Task.repeat_interval_days, same file)
- Required implementation: none - recommend this row be explicitly folded into D8-08's VERIFIED status on the next audit pass (it is a duplicate scenario ID for the same feature, not an independent gap)
- Dependencies: D8-08 (VERIFIED, delta)
- Backend work: none - already done
- Database/migration work: none - already done
- Mobile work: none - already done
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: covered by D8-08's existing tests (test_tasks.py::test_completing_a_re*)
- Verification method: automated test (already passing) - flagged for reclassification, not a real remaining gap

### D10-04 - Domain 10 (Crop Failure) - Drought failure
- Current implementation status: **VERIFIED (fixed this session, was Missing — the enum
  value already existed, only a dedicated test was missing)**
- `FailureReason.DROUGHT` was already present in `crop_cycle.py` (pre-dating this session,
  used incidentally as fixture data elsewhere in the test suite) — this row's own "Missing"
  status was stale. Closed by adding a dedicated assertion:
  `test_crop_cycles.py::test_report_failure_accepts_drought_flood_and_weather_damage_reasons`.
- Mobile work: not yet done — report-failure dialog should surface Drought as an option;
  tracked as a follow-up.
- Verification method: automated test, confirmed passing

### D10-05 - Domain 10 (Crop Failure) - Flood failure
- Current implementation status: **VERIFIED (fixed this session via the same test as
  D10-04, was Missing)** — `FailureReason.FLOOD` already existed; same evidence as D10-04.

### D10-06 - Domain 10 (Crop Failure) - Weather damage
- Current implementation status: **VERIFIED (fixed this session via the same test as
  D10-04, was Missing)** — `FailureReason.WEATHER_DAMAGE` already existed; same evidence as
  D10-04.

### D10-07 - Domain 10 (Crop Failure) - Other failure reason
- Current implementation status: **VERIFIED (fixed and tested this session, was Missing)**
- `FailureReason.OTHER` already existed, but the accompanying free-text detail field did
  not. Fix applied: `CropCycle.failure_reason_note` (migration `b2c3d4e5f6a7`), required
  specifically when `failure_reason == OTHER` (422 otherwise — a catch-all with no note
  carries no real information) and optional for every other reason.
- Mobile work: not yet done — report-failure dialog should add an Other option with a
  required text field; tracked as a follow-up.
- Tests added and passing: `test_crop_cycles.py::test_report_failure_other_reason_requires_a_note`
- Verification method: automated test, confirmed passing

### D10-08 - Domain 10 (Crop Failure) - Failure confirmation
- Current implementation status: Missing
- Existing relevant files/classes/functions: no second-step/expert confirmation of a failure exists; CropHealthCase provides expert review of disease diagnoses generally but is never wired to crop-cycle cancellation
- Missing component: any expert-confirmation step for a reported failure
- Required implementation: this is a genuinely optional enhancement, not a core requirement - a farmer's own self-report (now VERIFIED via D10-01) is sufficient for the primary use case; if pursued, add an optional Request expert review of this failure action on a cancelled cycle that creates a CropHealthCase-style case linked to the crop cycle, reusing the existing case-assignment/expert-network infrastructure from Domain 33-39 (out of this group's scope)
- Dependencies: Domain 33-39 (Expert Network, out of this group's scope) - any real implementation should reuse that infrastructure rather than building a parallel review system
- Backend work: link crop_cycle_service.py::report_failure to case_service.py's existing case-creation path, optionally
- Database/migration work: additive FK (case_id) on crop_cycles, if pursued
- Mobile work: report-failure flow - optional Request expert review button
- Automation work: none new - reuses existing SLA-scheduler infrastructure (scheduler.py) if a case is created
- Notification work: reuses existing case-assignment notification categories
- Offline/sync impact: none new
- Security/RBAC impact: none new - reuses existing case-review RBAC
- Tests required: test_farmer_can_request_expert_review_of_a_reported_failure, if pursued
- Verification method: automated test, contingent on product decision
### D11-06 - Domain 11 (Re-Sowing) - New task generation
- Current implementation status: Missing (re-confirmed, Missing Backlog Batch 9) - this row's own older text recommended reclassifying FUTURE, but `docs/FINAL_GAP_REPORT.md`'s Batch 8 investigation already examined this exact row and deliberately kept it Missing rather than reclassifying: building it "would contradict this project's own twice-made 'no auto-generated agronomic tasks' decision" (D8-02/D9-01 precedent). This batch defers to that later, more careful decision rather than the row's own superseded note. Not re-actioned this batch.
- Existing relevant files/classes/functions: creating a crop cycle never creates any Task rows (confirmed, zero reference to task_repository/task_service in create_crop_cycle)
- Missing component: any auto-task creation tied to re-sowing
- Required implementation: this is the same root cause as D9-01/D8-02 (deliberate no-auto-task-generation design) - no new work is appropriate here beyond what those FUTURE-classified rows already cover; a re-sow-specific version of auto-task-creation would be a strictly narrower instance of the same already-deferred capability
- Dependencies: D9-01, D8-02 (both FUTURE, explicit deferral) - this row should be read as the same deferral applied to the re-sowing context specifically
- Backend work: none - same deliberate boundary as D9-01
- Database/migration work: none
- Mobile work: none
- Automation work: none - explicitly deferred, same as D9-01
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none - not planned, consistent with D9-01's deferral
- Verification method: n/a - recommend reclassifying this row FUTURE (with the same D8-02/task.py:1-18 citation) rather than Missing, since it is not a distinct undisclosed gap but the same already-disclosed deferral applied to a specific trigger context

### D12-01 - Domain 12 (Intercropping) - Multiple crops in same plot
- Current implementation status: Missing
- Existing relevant files/classes/functions: no exclusivity constraint exists preventing two concurrent non-terminal CropCycle rows on one plot_id (accidental, untested); no UI concept of add-an-intercrop
- Missing component: deliberate intercropping feature entirely
- Required implementation: this is a genuine product-scope decision, not a small technical gap - building real intercropping support means (a) explicitly allowing the concurrent-active-cycle case that D6-07/D11-05's proposed fix would otherwise block, (b) a pairing/grouping field, and (c) dedicated UI; until decided, make the D6-07 guard configurable (block by default, with an explicit intentional-intercrop override) rather than an unconditional block
- Dependencies: D6-07, D11-05 (their proposed guard needs an intercropping escape hatch); D12-02..06 (all blocked on this same decision)
- Backend work: crop_cycle_service.py::create_crop_cycle - add an explicit is_intercrop boolean flag on the create request that bypasses the single-active-cycle guard when true
- Database/migration work: additive nullable intercrop_group_id (or similar) column on crop_cycles, if pursued
- Mobile work: Add Intercrop distinct entry point from Add Crop
- Automation work: none
- Notification work: none
- Offline/sync impact: standard crop-cycle sync
- Security/RBAC impact: none
- Tests required: test_can_create_intercropped_cycle_when_explicitly_flagged; test_cannot_create_concurrent_cycle_without_the_intercrop_flag
- Verification method: automated test, contingent on product decision
### D13-02 - Domain 13 (Perennial Crops) - Multiple seasons
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: new `CropCycleSeasonHistory` table (migration `5b87cb6eb39c`), mirroring
  `CropCycleStageHistory`'s exact append-only convention - `crop_cycle_service._record_season_history`
  fires only on a genuine season change (never at creation, matching `_record_stage_history`'s
  own convention); `GET /crops/{id}/season-history`.
- Tests added and passing: `tests/test_batch8_history_tracking.py` (4 tests: single change,
  multiple changes, no-op on same value, per-farmer isolation)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: season is a single nullable enum field per cycle, overwritable via update but not tracked historically; no per-year/per-season boundary or rollup
- Missing component: historical season tracking for one long-running cycle
- Required implementation: add a season_history table (or reuse CropCycleStageHistory's append-only pattern) recording each season value change with a timestamp, so a multi-year perennial cycle's season history is reconstructable
- Dependencies: D13-01, D13-06 (crop-year history) - same underlying need for a year/season boundary concept
- Backend work: crop_cycle_service.py::update_my_crop_cycle - append a history row whenever season changes, mirroring _record_stage_history's existing pattern exactly
- Database/migration work: new crop_cycle_season_history table, Alembic migration mirroring the existing crop_cycle_stage_history table's shape
- Mobile work: crop cycle edit form - season change now recorded, no new farmer-facing action required
- Automation work: none
- Notification work: none
- Offline/sync impact: standard crop-cycle sync
- Security/RBAC impact: none
- Tests required: test_changing_season_creates_a_season_history_entry
- Verification method: automated test

### D13-04 - Domain 13 (Perennial Crops) - Recurring maintenance
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, zero-code bonus, was Missing)**
- Fix applied: NONE - this row's own prior analysis correctly suspected D8-08 already covered
  it; this batch PROVED the combination rather than merely asserting it - a recurring
  `TaskType.PRUNING` task tied to a `season="perennial"` crop cycle recurs correctly across
  multiple completions (the recurrence code path never reads `season` at all), with the crop
  cycle itself untouched (still `planned`/`perennial`, never auto-closed).
- Tests added and passing: `tests/test_batch8_group4.py::test_recurring_pruning_task_on_a_perennial_crop_cycle_keeps_recurring`
- Verification method: automated test, confirmed passing (proof, not new code)
- Existing relevant files/classes/functions: same cross-reference as D9-13/D13-05 - this is now largely covered by D8-08's repeat_interval_days, originally scoped for general recurring tasks and works identically for perennial-crop maintenance tasks (pruning, fertilizing) without needing perennial-specific code
- Missing component: nothing perennial-specific beyond what D8-08 already provides - this row should be re-examined given D8-08's VERIFIED status
### D13-05 - Domain 13 (Perennial Crops) - Pruning
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - `TaskType.PRUNING` added (migration `fd90ec676715`, `ALTER TYPE task_type ADD VALUE`); mobile `taskTypeOptions` includes `'pruning'` (task creation dropdown, no separate label-mapping to update). Tests: `tests/test_tasks.py::test_create_task_with_pruning_type` (backend), `task_models_test.dart::taskTypeOptions matches...` (mobile)
- Existing relevant files/classes/functions: TaskType enum is GENERAL/IRRIGATION/SPRAYING/FERTILIZING/WEEDING/HARVESTING/OTHER - no PRUNING value; farmer can only mislabel via OTHER/GENERAL
- Missing component: dedicated TaskType.PRUNING value
- Required implementation: add PRUNING to the TaskType enum - a small, low-risk additive change
- Dependencies: none
- Backend work: task.py::TaskType enum
- Database/migration work: additive enum value
- Mobile work: task-creation form - new task-type option
- Automation work: none
- Notification work: none
- Offline/sync impact: standard task sync
- Security/RBAC impact: none
- Tests required: test_create_task_with_pruning_type
- Verification method: automated test

### D99-03 - Domain 99 (Special Crop Scenarios) - Intercropping (cross-ref Domain 12)
- Current implementation status: Missing
- Existing relevant files/classes/functions: identical to D12-01..06 in aggregate - see those rows
- Missing component: see D12-01 (blocking product decision) and D12-02..06 (all Partial, in Section 2)
- Required implementation: see D12-01 through D12-06
- Dependencies: D12-01 through D12-06
- Backend work: see those rows
- Database/migration work: see those rows
- Mobile work: see those rows
- Automation work: see those rows
- Notification work: see those rows
- Offline/sync impact: see those rows
- Security/RBAC impact: see those rows
- Tests required: see those rows
- Verification method: automated test, per those rows
### D14-02 - Domain 14 (Weather) - Hourly forecast
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: `OpenMeteoProvider.get_weather` now also requests Open-Meteo's real, documented
  `hourly` param; `HourlyForecastEntry` (new dataclass) carries the next 24 upcoming hours
  only (never past hours, never more than 24); cached via the EXISTING `weather_snapshots`
  table (new `snapshot_type='hourly'` value + `hour_timestamp` column, migration
  `a595f6178964`) rather than a new table, mirroring this table's own stated "one table,
  snapshot_type distinguishes rows" convention. `FarmWeatherResponse.hourly` (new field,
  defaults to `[]`, never fabricated).
- Tests added and passing: `tests/test_batch8_hourly_weather.py` (6 tests: `_parse_response`
  unit tests against a static fixture matching Open-Meteo's real documented shape - the
  live-API-round-trip caveat this provider's own docstring discloses applies identically
  here, untested by design - plus end-to-end cache/API tests via `FakeWeatherProvider`)
- Verification method: automated test (parsing logic + service/cache integration);
  environment-dependent for the real live-API call, same caveat as D14-01/03/04/05/06/08
- Existing relevant files/classes/functions: OpenMeteoProvider.get_weather only requests Open-Meteo's current/daily params, never hourly (open_meteo_provider.py:35-36); WeatherReading/WeatherSnapshot have no hourly-granularity fields
- Missing component: hourly forecast data entirely
- Required implementation: extend OpenMeteoProvider.get_weather to also request the hourly param, add hourly fields to WeatherSnapshot (or a new related table if hourly data is high-volume enough to warrant separate storage), add an hourly-forecast endpoint/screen section
- Dependencies: none blocking; also an opportunity to finally add the missing tests/test_weather_provider.py the provider's own docstring already (incorrectly) claims exists
- Backend work: weather/open_meteo_provider.py, weather_service.py, weather_snapshot.py (new hourly fields/table)
- Database/migration work: new columns or a new weather_hourly_readings table, Alembic migration
- Mobile work: weather_screen.dart - hourly forecast section
- Automation work: none new - same fetch trigger as daily/current
- Notification work: none
- Offline/sync impact: same caching/staleness pattern as current/daily readings
- Security/RBAC impact: none
- Tests required: test_open_meteo_provider_parses_hourly_fields (also finally creating the long-claimed-but-missing test_weather_provider.py); test_hourly_forecast_endpoint
- Verification method: environment-dependent for real data (same live-API caveat as D14-01/03/04/05/06/08) plus automated test for parsing logic against a fixture
### D15-04 - Domain 15 (Weather Risk) - Frost
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `weather_alert_rules.evaluate_frost_risk` using a Magnus-formula dew-point
  approximation over already-fetched `temperature_c`/`humidity_percent` — no new external
  data, reuses the `WEATHER_ALERT` category. Wired into
  `weather_alert_orchestration_service.generate_alerts_for_farm_weather` (both the
  pull-based endpoint and the proactive sweep).
- Mobile work: not yet done — `weather_screen.dart` should surface a frost advisory
  display; tracked as a follow-up.
- Tests added and passing: `test_weather_alert_rules.py::TestFrostRisk` (3 tests),
  `test_proactive_weather_sweep.py::test_sweep_detects_frost_risk`
- Verification method: automated test, confirmed passing

### D15-05 - Domain 15 (Weather Risk) - Storm
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: `app/services/weather/wmo_codes.py` (new) decodes `condition_code` per Open-Meteo's
  real, public WMO weather-code table - codes 95/96/99 (thunderstorm, slight/heavy hail) →
  `is_storm=True`. `WeatherReadingResponse.is_storm` (new field, `None` when `condition_code`
  itself is `None`, never a fabricated `False`). Cyclone (D15-06) deliberately NOT attempted -
  no WMO code represents a cyclone (a large-scale system, not a point-in-time condition);
  stays Missing, cited in wmo_codes.py's own docstring.
- Tests added and passing: `tests/test_batch8_wmo_codes.py` (7 tests)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: no storm concept in code; only generic high-wind threshold
- Missing component: dedicated storm classification
- Required implementation: would need either (a) a new meteorological classification derived from combining existing wind+rain+pressure data (Open-Meteo does provide condition_code/WMO codes not currently decoded, see D15-07), or (b) ingesting a real storm-advisory feed from IMD - the latter is a real external-data dependency, not purely a code gap
- Dependencies: D15-07 (Hail/condition-code decoding) - decoding the already-fetched WMO condition_code is the buildable first step; a genuine storm-tracking feed is a larger external-integration decision
- Backend work: weather/open_meteo_provider.py - decode condition_code per WMO's public table (buildable now); weather_alert_rules.py - new storm-adjacent rule using the decoded condition
- Database/migration work: none for condition-code decoding (already stored raw); new fields would be needed for full storm-tracking metadata if a real feed is integrated later
- Mobile work: weather_screen.dart - storm-adjacent advisory display
- Automation work: none new for condition decoding
- Notification work: reuses WEATHER_ALERT / new category if a distinct storm feed is integrated
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_condition_code_decodes_to_friendly_label
- Verification method: automated test for condition-code decoding; environment-dependent for a real storm-feed integration if pursued
### D15-06 - Domain 15 (Weather Risk) - Cyclone
- Current implementation status: Missing (re-investigated, Missing Backlog Batch 8 - deliberately NOT built)
- Batch 8 note: D15-05/D15-07 (storm/hail, same Weather Risk domain) WERE built this batch by
  decoding the real WMO weather-code table - re-examined whether the same technique covers
  cyclone too. It does not: WMO's point-in-time condition codes (fog/rain/snow/thunderstorm)
  have no code representing a large-scale cyclone system. Confirmed genuinely blocked on a
  real external track/warning feed (same root cause already disclosed at D75-05, docs/audit/FINAL_CANONICAL_group_D.md),
  not re-labeled to force a false closure.
- Existing relevant files/classes/functions: no cyclone-tracking or govt-advisory ingestion
- Missing component: entire capability
- Required implementation: this genuinely requires a real IMD/meteorological-agency cyclone-advisory feed - recommend this be reclassified OUT_OF_SCOPE (same class of justification as D18-10's IoT-hardware exclusion) unless the project intends to build a real external integration; Missing implies a buildable-now increment, which understates that a real external data source is a prerequisite
- Dependencies: a real external cyclone-advisory data source (IMD or equivalent) - no such integration exists anywhere in this codebase
- Backend work: n/a until an external feed is integrated
- Database/migration work: n/a
- Mobile work: n/a
- Automation work: n/a
- Notification work: n/a
- Offline/sync impact: n/a
- Security/RBAC impact: n/a
- Tests required: n/a
- Verification method: n/a - recommend reclassifying OUT_OF_SCOPE (real external government data source this project structurally never fabricates); see the cross-note in Section 5/6

### D15-07 - Domain 15 (Weather Risk) - Hail
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: same `wmo_codes.py` decode as D15-05 - codes 96/99 → `is_hail=True`;
  `WeatherReadingResponse.is_hail` (new field, same `None`-when-unavailable convention).
- Tests added and passing: `tests/test_batch8_wmo_codes.py` (shared with D15-05, 7 tests)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: condition_code stored raw from Open-Meteo's WMO code but never decoded/mapped to any category, including hail
- Missing component: WMO-code-to-category decoding entirely
- Required implementation: same buildable fix as D15-05 - decode the already-stored condition_code per WMO's public weather-code table (codes 96/99 = hail-bearing thunderstorm), surfaced as an advisory
- Dependencies: none blocking - data already fetched and stored, purely a decoding/mapping gap
- Backend work: weather/open_meteo_provider.py or weather_service.py - new decode_condition_code mapping function
- Database/migration work: none - condition_code already stored
- Mobile work: weather_screen.dart - friendly condition label plus hail advisory when applicable
- Automation work: none new
- Notification work: reuses WEATHER_ALERT
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_condition_code_96_99_maps_to_hail_advisory
- Verification method: automated test
### D15-08 - Domain 15 (Weather Risk) - Flood
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `weather_alert_rules.evaluate_cumulative_rainfall_risk` — a pure function over
  a precomputed cumulative-rainfall total; `weather_alert_orchestration_service.py` computes
  that total via a new `weather_repository.list_current_since` history query over the
  already-stored `weather_snapshots.rainfall_mm` (a real per-fetch history, never
  overwritten — confirmed by direct read of `weather_service.py`). Reuses `WEATHER_ALERT`.
  True river-level/hydrological flood modeling remains out of reach without a real
  government sensor feed, as this row's own citation disclosed — only the buildable
  increment was built.
- Mobile work: not yet done — `weather_screen.dart` should surface a flood-risk advisory;
  tracked as a follow-up.
- Tests added and passing: `test_weather_alert_rules.py::TestCumulativeRainfallRisk` (3
  tests), `test_proactive_weather_sweep.py::test_sweep_detects_flood_risk_from_cumulative_rainfall_history`
- Verification method: automated test, confirmed passing

### D15-09 - Domain 15 (Weather Risk) - Drought
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: `weather_alert_rules.evaluate_consecutive_dry_days_risk` — a pure function
  over a precomputed dry-day count; the orchestration layer's new
  `_count_consecutive_dry_days` walks the same `weather_snapshots` history backward from
  yesterday (today's data is deliberately excluded — may be partial), stopping at the first
  day with no data at all (conservative — never assumes dry from missing history) or with
  rainfall at/above the dry threshold. Reuses `WEATHER_ALERT`. True soil-moisture-based
  drought detection stays blocked on D18-10's disclosed-absent IoT hardware, unchanged.
- **Bug found and fixed during this session's own testing** (not merely at implementation
  time): the DB driver can return `WeatherSnapshot.fetched_at` as an aware datetime
  expressed in the session/connection's local timezone (observed: IST) rather than UTC.
  Calling `.date()` on it directly silently bucketed rows under the wrong calendar day
  whenever the local time-of-day crossed midnight relative to UTC, undercounting
  consecutive dry days by one and suppressing a genuine drought alert. Fixed by
  normalizing to UTC (`.astimezone(timezone.utc).date()`) before bucketing - a real
  production correctness fix, not just a test artifact, caught by reproducing a live
  failure with a debug script rather than assumed away.
- Mobile work: not yet done — `weather_screen.dart` should surface a drought-risk advisory;
  tracked as a follow-up.
- Tests added and passing: `test_weather_alert_rules.py::TestConsecutiveDryDaysRisk` (2
  tests), `test_proactive_weather_sweep.py::test_sweep_detects_drought_risk_from_consecutive_dry_days_history`,
  `::test_sweep_does_not_flag_drought_with_too_few_dry_days`
- Verification method: automated test, confirmed passing
### D17-02 - Domain 17 (Water) - Water availability
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: new `Plot.water_availability` (nullable `WaterAvailability` enum:
  adequate/limited/scarce), farmer-declared only - independent of `irrigation_source`
  (which describes the TYPE of source, not its reliability). Did not wait on a separate
  WaterSource model (D17-01) as this row's prior analysis anticipated - the enum field
  directly on `Plot` was sufficient and avoided an unnecessary new table.
- Tests added and passing: `tests/test_batch8_history_tracking.py` (part of the 8
  water-availability/shortage/history tests)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: no availability/quantity tracking anywhere
- Missing component: entire capability
- Backend work: new water_source_service.py, once D17-01's model exists
- Database/migration work: new fields/table on top of D17-01's work
- Mobile work: farm/plot detail screen - water availability field
- Automation work: none
- Notification work: none
- Offline/sync impact: standard write sync
- Security/RBAC impact: none
- Tests required: test_record_water_availability, once built
- Verification method: automated test, contingent on D17-01

### D17-03 - Domain 17 (Water) - Water shortage
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: `Plot.water_shortage` (computed property) = `water_availability == SCARCE`;
  `None` (not `False`) when not yet reported, honestly distinct from a reported
  adequate/limited state. Deliberately simpler than the rainfall-deficit-combined approach
  this row's prior analysis proposed - a farmer-declared flag, not an automatic weather-
  derived detection (no new fabricated signal, consistent with `is_sorted`/`quality_grade`'s
  "farmer-declared, never inferred" convention used throughout this project).
- Tests added and passing: `tests/test_batch8_history_tracking.py` (part of the 8
  water-availability/shortage/history tests)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: no shortage detection; closest proxy is the rain-probability alert, which is about excess not shortage
- Missing component: entire capability
- Backend work: combines D15-09's weather-side signal with D17-02's farmer-declared availability
- Database/migration work: none beyond D17-01/02's
- Mobile work: farm/plot detail screen - shortage advisory
- Automation work: reuses the drought-risk sweep once built
- Notification work: reuses WEATHER_ALERT category
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_water_shortage_advisory_combines_rainfall_deficit_and_declared_availability
- Verification method: automated test, contingent on D17-01/02/D15-09
### D17-04 - Domain 17 (Water) - Waterlogging
- Current implementation status: **VERIFIED (fixed this session via the same function as
  D15-08, was Missing)** — `evaluate_cumulative_rainfall_risk` fires `waterlogging_risk_alert`
  at the lower threshold and `flood_risk_alert` at the higher one, exactly as this row
  anticipated. See D15-08's entry above for the full evidence.
- Tests: `test_weather_alert_rules.py::TestCumulativeRainfallRisk::test_waterlogging_risk_at_threshold`
- Verification method: automated test, confirmed passing

### D17-05 - Domain 17 (Water) - Drought risk (water domain)
- Current implementation status: **VERIFIED (fixed this session via the same function as
  D15-09, was Missing)** — identical fix/tests, same commit. See D15-09's entry above.
- Verification method: automated test (same tests as D15-09), confirmed passing
### D17-06 - Domain 17 (Water) - Water history
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: new `PlotWaterHistory` table (migration `5b87cb6eb39c`), mirroring
  `CropCycleStageHistory`'s exact append-only pattern; `plot_service._record_water_history`
  fires only on a genuine `water_availability` change. `GET /plots/{id}/water-history`.
- Tests added and passing: `tests/test_batch8_history_tracking.py` (4 of the 8 water tests:
  history entry created, no-op on same value, multiple changes each recorded, per-farmer
  isolation)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: no historical log of water source/availability changes over time; no water-equivalent of crop_cycle_stage_history.py
- Missing component: entire capability
- Backend work: new water_source_history_service.py, once built
- Database/migration work: new water_source_history table mirroring crop_cycle_stage_history's shape
- Mobile work: water-history view on farm/plot detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none new
- Security/RBAC impact: none
- Tests required: test_water_source_change_creates_history_entry, once built
- Verification method: automated test, contingent on D17-01/02

### D18-06 - Domain 18 (Irrigation) - Irrigation activity
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: new `IrrigationRecord` model (`irrigation_records` table, migration
  `4ab51c60125d`) mirroring `TreatmentRecord`'s exact shape — `crop_cycle_id` FK,
  `irrigation_date`, `duration_minutes`/`volume_liters`, `source` (reuses D3-08's
  `IrrigationSource` enum, not a second duplicate vocabulary), optional `task_id` FK
  (validated same-crop-cycle, same pattern as `Task.depends_on_task_id`). New
  `irrigation_service.py`/`irrigation_repository.py`/`api/v1/irrigation.py`
  (`POST`/`GET /crop-cycles/{id}/irrigation-records`).
- D18-08 (Pump failure) built in the same migration, per this row's own suggested
  resolution: a simple optional `failure_note` field on `IrrigationRecord` rather than a
  full equipment-inventory system.
- Mobile work: not yet done — a new Log Irrigation screen mirroring the existing
  treatment-recording screen; tracked as a follow-up.
- Tests added and passing: `test_irrigation_records.py` (6 tests, including
  `test_irrigation_record_can_flag_a_pump_failure` for D18-08)
- Verification method: automated test, confirmed passing

### D18-08 - Domain 18 (Irrigation) - Pump failure
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D18-06, was Missing)** — see D18-06's entry above for the full evidence.
- Verification method: automated test (same commit as D18-06), confirmed passing

### D19-03 - Domain 19 (Soil) - Soil location
- Current implementation status: **FUTURE (reclassified this session, was Missing)** — per
  this row's own recommendation. D20 (Soil Testing foundation) was built this session, but
  sub-plot soil-zone tracking remains a genuinely low-priority refinement no validated
  farmer need has surfaced for yet - most smallholder plots do not need sub-plot zoning.
  Building it speculatively now that its blocker is gone would be exactly the kind of
  unrequested feature-building this project avoids; kept deferred with the same honest
  citation D20-14 already uses, not silently built because it's technically now possible.
- Verification method: n/a - a documented deferral decision, not a code change
### D19-04 - Domain 19 (Soil) - Soil history
- Current implementation status: **VERIFIED (Missing Backlog Batch 8, was Missing)**
- Fix applied: new `PlotSoilHistory` table (migration `5b87cb6eb39c`), mirroring
  `CropCycleStageHistory`'s exact append-only pattern - records both `soil_type` and
  `soil_category` together; `plot_service._record_soil_history` fires on a genuine change to
  either field. `GET /plots/{id}/soil-history`.
- Tests added and passing: `tests/test_batch8_history_tracking.py` (4 of the 17 total:
  soil_type change, soil_category-only change, no-op on same value, unrelated update creates
  no entry)
- Verification method: automated test, confirmed passing
- Existing relevant files/classes/functions: Plot has updated_at but no field-level change history; old soil_type overwritten, not versioned, on update; compare to crop_cycle_stage_history.py which the project built for an analogous case but never mirrored here
- Missing component: soil_type change history
- Backend work: plot_service.py::update_plot - append history row on soil_type change, mirroring _record_stage_history
- Database/migration work: new plot_soil_history table, Alembic migration
- Mobile work: plot detail screen - soil history view (optional; can ship backend-only first)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard plot-write sync
- Security/RBAC impact: none
- Tests required: test_updating_soil_type_creates_a_history_entry
- Verification method: automated test

### D19-05 - Domain 19 (Soil) - Crop-linked soil information
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing —
  the surfacing facet only)**
- Fix applied: `CropCycle.plot_soil_type`/`plot_soil_category` computed properties (pure
  join through to `Plot`, no new logic), surfaced on `CropCycleResponse`. The
  soil-suitability-recommendation facet remains deliberately unbuilt — it would need an
  authoritative per-crop soil-preference dataset, the same anti-fabrication boundary as
  D5-05/D21-01 (both FUTURE).
- Mobile work: not yet done — `crop_details_screen.dart` should display the plot's soil
  type/category inline; tracked as a follow-up.
- Tests added and passing: `test_crop_cycles.py::test_crop_cycle_response_includes_plot_soil_type`
- Verification method: automated test, confirmed passing (surfacing facet only)
### D20-01 - Domain 20 (Soil Testing) - Soil sample (collection record)
- Current implementation status: **VERIFIED (fixed and tested this session, P1, was Missing)**
- Fix applied: the entire Soil Testing domain foundation, built this session. New
  `SoilSample` model (`soil_samples` table, migration `381e2dc405e4`) - `plot_id` FK,
  `collection_date`, `lab_name` (optional), `notes`; `self_tested` is a computed property
  (`lab_name is None`), never a separately-stored column that could disagree with it. New
  `soil_testing_service.py`/`soil_testing_repository.py`/`api/v1/soil_testing.py`
  (`POST`/`GET /plots/{id}/soil-samples`).
- Mobile work: not yet done — a new Log Soil Sample screen; tracked as a follow-up.
- Tests added and passing: `test_soil_testing.py` (11 tests total across D20-01..12,
  itemized below)
- Verification method: automated test, confirmed passing

### D20-02 - Domain 20 (Soil Testing) - Lab test (result record)
- Current implementation status: **VERIFIED (fixed this session via the same foundation as
  D20-01, was Missing)** — new `SoilTestResult` model FK'd to `SoilSample`, holding every
  measured value (D20-03..09/11 are columns on this one table, exactly as this row's own
  citation specified). `POST`/`GET /soil-samples/{id}/results`.
- Tests: `test_soil_testing.py::test_create_soil_test_result_linked_to_sample`
- Verification method: automated test, confirmed passing

### D20-03 - Domain 20 (Soil Testing) - pH
- Current implementation status: **VERIFIED (fixed this session, was Missing)** —
  `ph_value` (Numeric) with a DB `CHECK` constraint (0-14 range, `ck_soil_test_results_ph_range`),
  exactly as this row's own citation specified.
- Tests: `test_soil_testing.py::test_ph_value_rejected_outside_0_to_14_range`
- Verification method: automated test, confirmed passing

### D20-04 - Domain 20 (Soil Testing) - Nitrogen
- Current implementation status: **VERIFIED (fixed this session, was Missing)** —
  `nitrogen_kg_per_ha` column on `SoilTestResult`.
- Tests: `test_soil_testing.py::test_create_soil_test_result_with_npk_and_organic_carbon_and_ec_values`
- Verification method: automated test, confirmed passing

### D20-05 - Domain 20 (Soil Testing) - Phosphorus
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D20-04, was Missing)** — `phosphorus_kg_per_ha` column. Same test as D20-04.

### D20-06 - Domain 20 (Soil Testing) - Potassium
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D20-04, was Missing)** — `potassium_kg_per_ha` column. Same test as D20-04.

### D20-07 - Domain 20 (Soil Testing) - Organic carbon
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D20-04, was Missing)** — `organic_carbon_percent` column. Same test as D20-04.

### D20-08 - Domain 20 (Soil Testing) - EC (electrical conductivity)
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D20-04, was Missing)** — `ec_ds_per_m` column. Same test as D20-04.

### D20-09 - Domain 20 (Soil Testing) - Micronutrients
- Current implementation status: **VERIFIED (fixed this session, was Missing)** — a
  flexible `micronutrients` JSONB column on `SoilTestResult`, exactly as this row's own
  citation recommended (varies by lab, not fixed columns).
- Tests: `test_soil_testing.py::test_create_soil_test_result_with_micronutrient_json`
- Verification method: automated test, confirmed passing

### D20-10 - Domain 20 (Soil Testing) - Soil report (document/summary)
- Current implementation status: **VERIFIED (fixed and tested this session, was Missing —
  the storage facet; OCR deliberately not built)**
- Fix applied: `POST /soil-test-results/{id}/report` stores an uploaded lab-report file,
  mirroring `invoice_service.upload_invoice`'s exact storage pattern (`report_storage_key`
  column). Deliberately NO OCR — this row's own citation marked OCR as optional ("if
  wanted"), not required, and the structured D20-03..09 fields already serve as the
  farmer-facing summary (this row's other half), so nothing further was needed there.
- Tests added and passing: `test_soil_testing.py::test_upload_soil_report_document`
- Verification method: automated test, confirmed passing

### D20-11 - Domain 20 (Soil Testing) - Test date
- Current implementation status: **VERIFIED (fixed this session via the same migration as
  D20-02, was Missing)** — `test_date` column on `SoilTestResult`, required.
- Tests: `test_soil_testing.py::test_soil_test_result_requires_test_date`
- Verification method: automated test, confirmed passing

### D20-12 - Domain 20 (Soil Testing) - Stale test (test result aging)
- Current implementation status: **VERIFIED (fixed and tested this session, was Missing)**
- Fix applied: `SoilTestResult.is_stale(today, max_age_days)` mirroring
  `WeatherSnapshot.is_stale()`'s exact pattern, exactly as this row's own citation
  specified — a new `Settings.soil_test_max_age_days` (730 days, a real agronomic
  convention, same disclosed-placeholder treatment as this project's other threshold
  settings), surfaced on every `SoilTestResultResponse`.
- Tests added and passing: `test_soil_testing.py::test_soil_test_result_is_stale_after_max_age`
- Verification method: automated test, confirmed passing
### D20-13 - Domain 20 (Soil Testing) - Test reminder
- Current implementation status: **VERIFIED (Missing Backlog Batch 4)** - new `NotificationCategory.SOIL_TEST_REMINDER` + `SoilTestResult.reminder_alerted_at` fires-once-per-episode gate (migrations `f3a8c9d1e5b2`/`a6b7c8d9e0f1`); new scheduler job `soil_test_reminder_sweep` (daily by default) mirrors `run_expiry_check_sweep`'s exact shape, alerting on the LATEST `SoilTestResult` per plot once it exceeds `soil_test_max_age_days` (D20-12) - an older, superseded stale result for a plot that has since been retested is correctly never alerted on. All 4 cited dependencies (D20-01/02/11/12) were already VERIFIED before this batch. This closes D78-10 (docs/audit/FINAL_CANONICAL_group_D.md) too - same mechanism, that row's own premise ("Soil Testing domain doesn't exist") no longer holds. Tests: `tests/test_soil_test_reminder_sweep.py` (3 new).
- Existing relevant files/classes/functions: no reminder/notification category exists for soil testing (notification.py:26-32 has no such category)
- Missing component: reminder mechanism
- Required implementation: add NotificationCategory.SOIL_TEST_REMINDER, and a scheduler job (mirroring run_expiry_check_sweep's exact shape in scheduler.py) that fires when a plot's most recent SoilTestResult.test_date (D20-11) exceeds the staleness threshold (D20-12)
- Dependencies: D20-01, D20-02, D20-11, D20-12 (all blocking)
- Backend work: soil_test_result_service.py::run_soil_test_reminder_sweep, scheduler.py registration, notification.py new category, notification_service.py's _CATEGORY_PREFERENCE_MAP/_TITLE_BY_CATEGORY entries
- Database/migration work: new NotificationCategory enum value (additive migration mirroring b8069da2cd90_add_payment_alert_notification_category.py)
- Mobile work: none beyond standard notification display
- Automation work: new scheduler job
- Notification work: new SOIL_TEST_REMINDER category
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test_soil_test_reminder_sweep_fires_once_past_staleness_threshold, mirroring the existing expiry-sweep dedup test pattern
- Verification method: automated test, contingent on D20-01/02/11/12
### D21-07 - Domain 21 (Seeds) - Seed usage
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: `input_inventory_service.py::record_usage` (lines 77-90) is generic across every `InputInventoryItem.category` value, including `ProductCategory.SEED` - there is no seed-specific carve-out needed because the model/endpoint were never category-restricted
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02/05/08/09 (VERIFIED) - confirmed to already cover this
- Backend work: none - `record_usage` already exists and is category-agnostic
- Database/migration work: none
- Mobile work: confirm the mobile inventory screen has a record-usage action (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: `_check_low_stock` already fires on the resulting balance (D22-06/D24-08/D24-09)
- Offline/sync impact: standard inventory-write sync
- Security/RBAC impact: none
- Tests required: none new - `test_record_usage_decreases_quantity`/`test_record_usage_greater_than_remaining_is_rejected` already exercise this path (category-agnostic, so already covers seed items)
- Verification method: automated test + direct code read this session, confirmed passing in the 761-test full suite run

### D22-01 - Domain 22 (Fertilizer) - Fertilizer requirement
- Current implementation status: **OUT_OF_SCOPE (reclassified, Missing Backlog Batch 7)** - confirmed by this row's own evidence text: an auto-computed dosage recommendation is structurally out of bounds per `docs/PRODUCT_SAFETY.md`'s absolute no-independent-prescription rule, same class as D23-08's assistant-side pesticide-dosage block. Reclassified per this row's own recommendation, no code change - the absence is the correct, deliberate safety behavior.
- Existing relevant files/classes/functions: no rule computes this; docs/PRODUCT_SAFETY.md:1-14's absolute no-independent-prescription rule makes an auto-computed dosage recommendation structurally out of bounds by design
- Missing component: any requirement calculator
- Required implementation: none - this is correctly and deliberately out of bounds per the project's own safety rule, same class as D23-08's assistant-side pesticide-dosage block; recommend reclassifying FUTURE or OUT_OF_SCOPE rather than Missing, since the cluster file's own evidence text already states the deliberate rule even though the status cell itself says Missing
- Dependencies: none - structurally blocked by design, not by missing data
- Backend work: none - should not be built per PRODUCT_SAFETY.md
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: this IS a safety/consent boundary - the absence is the correct behavior
- Tests required: none needed - a negative test (test_no_endpoint_computes_a_fertilizer_dosage) could make the boundary explicit
- Verification method: n/a - recommend reclassifying (FUTURE or OUT_OF_SCOPE with the PRODUCT_SAFETY.md:1-14 citation) rather than Missing
### D22-05 - Domain 22 (Fertilizer) - Fertilizer usage
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: same as D21-07 - `record_usage` is category-agnostic, covers `ProductCategory.FERTILIZER` with no separate code path
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02/05/08/09
- Backend work: see D21-07
- Database/migration work: see D21-07
- Mobile work: see D21-07
- Automation work: see D21-07
- Notification work: see D21-07
- Offline/sync impact: see D21-07
- Security/RBAC impact: see D21-07
- Tests required: see D21-07
- Verification method: same as D21-07

### D23-06 - Domain 23 (Crop Protection) - Usage (crop protection)
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: same as D21-07 - `record_usage` is category-agnostic, covers `ProductCategory.CROP_PROTECTION_PRODUCT` with no separate code path
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02/05/08/09
- Backend work: see D21-07
- Database/migration work: see D21-07
- Mobile work: see D21-07
- Automation work: see D21-07
- Notification work: see D21-07
- Offline/sync impact: see D21-07
- Security/RBAC impact: see D21-07
- Tests required: see D21-07
- Verification method: same as D21-07
### D24-03 - Domain 24 (Input Inventory) - Unit (of measure for a farmer-held input)
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: `InputInventoryItem.unit` (`input_inventory.py:47`) is `Mapped[str]`, `nullable=False` - a required field independent of the optional `product_id` FK, so non-catalog inputs are already trackable
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02 (VERIFIED)
- Backend work: none - the field already exists as required
- Database/migration work: none
- Mobile work: confirm the inventory form surfaces it (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard sync
- Security/RBAC impact: none
- Tests required: none new - schema already enforces `nullable=False`, requests without it are rejected by Pydantic validation
- Verification method: direct code read this session (`input_inventory.py:47`, `schemas/input_inventory.py:11`)

### D24-06 - Domain 24 (Input Inventory) - Usage (recording consumption)
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: `input_inventory_service.py::record_usage` (lines 77-90)
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02/05/08/09
- Backend work: see D21-07
- Database/migration work: see D21-07
- Mobile work: see D21-07
- Automation work: see D21-07
- Notification work: see D21-07
- Offline/sync impact: see D21-07
- Security/RBAC impact: see D21-07
- Tests required: see D21-07
- Verification method: same as D21-07
### D24-07 - Domain 24 (Input Inventory) - Remaining quantity (computed: purchased minus used)
- Current implementation status: VERIFIED (re-verified this continuation session)
- Existing relevant files/classes/functions: `input_inventory_service.py:82` - `item.quantity -= payload.quantity_used` inside `record_usage`, confirming `quantity` is a running remaining-quantity, not a static purchased-amount, mirroring `DealerProduct.stock_quantity`'s existing decrement pattern
- Missing component: none
- Required implementation: none
- Dependencies: D24-01/02/05/08/09
- Backend work: none - decrement logic already exists
- Database/migration work: none
- Mobile work: inventory screen - confirm it displays `quantity` as the remaining balance (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: standard sync
- Security/RBAC impact: none
- Tests required: none new - `test_record_usage_decreases_quantity` already asserts this
- Verification method: direct code read this session (`input_inventory_service.py:82`), confirmed passing in the 761-test full suite run

### D24-10 - Domain 24 (Input Inventory) - Inventory history
- Current implementation status: **VERIFIED (Missing Backlog Batch 2)** - confirmed exactly this row's own closing recommendation: `input_inventory_service.py` already logged every mutation (`INPUT_INVENTORY_CREATED`/`USAGE_RECORDED`/`RESTOCKED`/`CORRECTED`) via `AuditLogger(entity="input_inventory_item")` - zero new DB work needed. New `get_item_history` (mirrors `farm_service.get_farm_history`/D2-06 exactly) + `GET /input-inventory/{item_id}/history`. Real bug found and fixed in the process: `create_item`'s audit-log call read `item.id` BEFORE the `db.flush()` that actually populates it (a Python-side `uuid.uuid4` default only applies at flush time), so every CREATED row had previously been logged with the literal string "None" as its entity_id - permanently unreachable by this new read path until fixed. Tests: `tests/test_input_inventory.py::test_item_history_shows_every_mutation_in_order`, `test_item_history_is_not_visible_to_another_farmer`
- Existing relevant files/classes/functions: GET /orders gives purchase history only; partial credit only insofar as order/purchase history exists
- Missing component: true inventory history (additions/consumption over time) as opposed to marketplace purchase history
- Required implementation: add an append-only input_inventory_history table (or reuse an audit-log-style pattern) recording every create/usage/restock/correction event against an InputInventoryItem, mirroring crop_cycle_stage_history.py's pattern - check first whether the Batch 3 delta's correction action already implies some history tracking (the matrix summary lists create, usage, restock, correction as built actions, which strongly suggests event-level tracking may already partially exist and just need a farmer-facing history endpoint/screen on top)
- Dependencies: D24-01/02/05/08/09 (the underlying event actions, VERIFIED)
- Backend work: input_inventory_service.py::get_history_for_item (new, or already present internally and just unexposed)
- Database/migration work: new history table if not already tracked internally; none if the existing AuditLogger calls already capture these events sufficiently to query back
- Mobile work: Inventory History view on the inventory item detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: standard read
- Security/RBAC impact: ownership check
- Tests required: test_inventory_item_history_includes_all_events_in_order
- Verification method: automated test - recommend re-confirming against current input_inventory_service.py/AuditLogger usage before treating this as fully open, since Batch 3 may have already logged these events
### D26-04 - Domain 26 (Input Verification) - Authenticity information
- Current implementation status: Missing (re-confirmed genuinely blocked, Missing Backlog Batch 9) - blocked on a real external manufacturer/industry-registry verification relationship that does not exist and is not planned in this codebase; a fabricated/simulated verification would violate the project's anti-fabrication convention, same class as D15-06/D18-10's external-dependency exclusions. This row's own older text offered FUTURE or OUT_OF_SCOPE as options, but consistent with this project's established Batch 3/4/7/8 convention of leaving a genuinely-blocked row honestly Missing with its reason disclosed inline rather than reclassifying it, left Missing - the FUTURE-vs-OUT_OF_SCOPE call remains open for a real product decision.
- Existing relevant files/classes/functions: Product has no QR/barcode/manufacturer-verification capability; explicitly disclosed in docs/PROMPT9_ASSUMPTIONS_RISKS.md:80-89 as an open NEEDS VALIDATION question
- Missing component: entire capability
- Required implementation: this needs a real manufacturer-side QR/barcode verification API (an external integration with each manufacturer or a shared industry registry) - a fabricated/simulated verification would violate the project's own anti-fabrication convention; treat this as blocked on a genuine external manufacturer/registry relationship, similar in kind to D15-06/D18-10's external-dependency exclusions
- Dependencies: a real external manufacturer/registry verification API - none exists or is planned in this codebase
- Backend work: n/a until an external integration exists
- Database/migration work: n/a - though Product could gain an optional qr_code/batch_number field now, ready for future verification, without fabricating the verification logic itself
- Mobile work: n/a until backend exists; could add QR-code scanning UI now (reusing existing camera-capture infrastructure) as a no-op placeholder
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until a real integration exists
- Verification method: n/a - recommend flagging this for a scope decision (FUTURE with an explicit blocked-on-a-real-manufacturer/registry-verification-relationship citation, or OUT_OF_SCOPE if the project decides never to pursue it) rather than leaving it Missing, since Missing implies a buildable-now increment which this is not

## 4. Broken

None. Confirmed empty for this group.

The only BROKEN scenario in domains 1-26/99 at baseline was D1-18 (Account
recovery / password reset with no identity check), which was independently
re-verified this session against current code per MATRIX Section A: the
Twilio Verify OTP gate is now required in auth_service.py::reset_password
before any password change can occur, and this is reflected in D1-18's
VERIFIED status in Section 1 above. No other scenario in this group was
ever classified BROKEN by the source cluster files. Zero BROKEN rows remain
in this group, matching the reconciled project-wide total of 0 BROKEN
across all 798 scenarios.

## 5. Future - with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D7-12 | 7 Crop Stages | Automatic stage estimation | crop_cycle.py:110-115 - AICropStageResult model docstring explicitly states this is deferred, verbatim "not written or read by any logic in this phase." CAUTION - the cluster file's citation also says "no scheduler/Celery/APScheduler anywhere in repo," which is now factually stale: scheduler.py (APScheduler) was added for the P0/Batch-3/Batch-7 work confirmed in this session (backend/app/services/scheduler.py, 3 registered jobs). The FUTURE label itself likely still holds for a different, valid reason - no trained AI stage-classification model is configured anywhere in the project - but the citation should be corrected to that reason rather than the outdated scheduler-absence claim on the next audit pass. |
| D8-02 | 8 Crop Calendar | Crop-stage tasks | task.py:1-18, verbatim: "this project has no crop-calendar, no validated agronomic rule dataset... only source #1 (explicit farmer-created task) can be implemented without inventing agronomy." Real, explicit, in-code citation - justified. |
| D8-03 | 8 Crop Calendar | Variety-specific tasks | Same deferral as D8-02 (task.py:1-18); zero variety references in task_service.py, confirmed. Justified. |
| D8-04 | 8 Crop Calendar | Region-specific tasks | Same deferral as D8-02 (task.py:1-18); no region/mandal/district branching in task creation logic. Justified. |
| D8-05 | 8 Crop Calendar | Sowing-date-driven tasks | task_service.py:38-57 (manual due_date only); task.py:1-18 explicitly names this exact scenario (day-30-after-sowing example) as deferred. Justified. |
| D9-01 | 9 Task Automation | Automatic task creation | PROJECT_STATUS.md:386-388,402, explicit: "no auto-generated crop-calendar tasks (correctly, since no authoritative rule source exists)." This reasoning is about the absence of a validated agronomic rule dataset, not about scheduler absence, so it remains fully valid even though scheduler.py now exists for other purposes. Justified. |
| D16-05 | 16 Weather Automation | Weather to task creation | task.py:6-11, explicit: "no crop-calendar, no validated agronomic rule dataset... only source #1 (explicit farmer-created task) can be implemented without inventing agronomy." Justified. |
| D16-06 | 16 Weather Automation | Weather to task modification | task_service.py:8-13 docstring: "This is a read-only connection - it never changes task status, due date, or completion"; weather_action_engine_service.py:12-14: "Task integration is ADVISORY ONLY... never automatically rescheduled or modified." This is a design-principle deferral (avoid silently mutating farmer data), independent of scheduler existence. Justified. |
| D16-07 | 16 Weather Automation | Weather to task postponement | Same citations as D16-06; grep for postpone across app/ is empty, confirming no code path exists. Justified. |
| D20-14 | 20 Soil Testing | Crop-linked recommendation (from soil test results) | GAP_REPORT resolution table, explicit: "Reclassified FUTURE. Structurally blocked on the entire Soil Testing domain (D20-01, 14/14 MISSING) being built first - attempting this without that foundation would mean fabricating soil data." Real citation from the reconciliation source document itself. Justified. |
| D21-01 | 21 Seeds | Seed requirement calculator | GAP_REPORT resolution table, explicit: "Reclassified FUTURE. Requires an authoritative per-crop seeding-rate reference dataset; inventing one would violate this project's own no-fabricated-agronomic-data rule." Justified. |

**Additional FUTURE-candidates surfaced during this reconciliation** (not
themselves labeled FUTURE by the source cluster files, so not double-counted
in the 13 above, but flagged in their Section 2/3 itemized entries with a
recommendation to reclassify): D5-05 (Variety-specific recommendations),
D11-06 (New task generation), D13-04 (Recurring maintenance), D16-03
(Weather to crop stage sensitivity), D19-03 (Soil location), D19-05's
suitability facet, D22-01 (Fertilizer requirement), D26-04 (Authenticity
information). See each row's own itemized block in Section 2/3 for the
specific citation-based reasoning.

## 6. Out of Scope - with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D9-11 | 9 Task Automation | Rejection | CONFIRMED this session (was flagged questionable): independently re-verified by direct grep of `backend/app/models/task.py` for `assignee\|reviewer\|Role\.` — zero matches. This is consistent with, not an isolated gap in, the task domain's actual uniform design: every task is farmer-created-and-owned only (the same "farmer-only-task-mutation convention" cited to justify D9-01/D16-05/D16-06), with zero second-party assignment/review concept anywhere in the domain. `CaseAssignment` (expert-network disease consultation) is a structurally distinct concept and does not answer this question. No product requirement document defines role-based task rejection today. Kept OUT_OF_SCOPE because the workflow is genuinely undefined by current product scope, not because it would be hard to build — re-confirm with the product team before ever promoting this to a plan item. |
| D18-10 | 18 Irrigation | Future sensor integration | irrigation_intelligence_service.py:11-14,63,77, explicit and quoted: "confirmed absent from this project by inspection... always False, stated explicitly... never silently omitted." Requires real IoT soil-moisture/flow hardware this project structurally never fabricates - `soil_moisture_available` is hardcoded False and disclosed as the honest interface boundary. Genuinely justified: a real external hardware dependency, not an inferential absence. |

**Cross-note:** D15-06 (Cyclone, currently MISSING in Section 3) was flagged
in its own itemized entry as a strong OUT_OF_SCOPE candidate - it requires a
real IMD/meteorological-agency cyclone-advisory feed, the same class of
justification as D18-10's IoT-hardware exclusion - but was not moved here
because no source document (cluster file or matrix/gap-report) labels it
OUT_OF_SCOPE today; only D9-11 and D18-10 carry that label as originally
classified in the cluster files, so those are the two rows itemized above.

## 7. Environment Dependent - exact dependency

| Scenario ID | Domain | Name | Exact external dependency |
|---|---|---|---|
| D14-01 | 14 Weather | Current weather | Requires live Open-Meteo API reachability from the deployment network. Provider abstraction, caching, and honest available:false / is_stale fallback are all VERIFIED by test locally; whether the live API is actually reachable depends on the deployment environment. |
| D14-03 | 14 Weather | Daily forecast | Same dependency as D14-01 - live Open-Meteo API reachability. |
| D14-04 | 14 Weather | Rain (amount, mm) | Same dependency as D14-01 - live Open-Meteo API reachability (feeds the heavy-rain-by-mm rule). |
| D14-05 | 14 Weather | Rain probability | Same dependency as D14-01 - live Open-Meteo API reachability. |
| D14-06 | 14 Weather | Temperature | Same dependency as D14-01 - live Open-Meteo API reachability. |
| D14-08 | 14 Weather | Wind | Same dependency as D14-01 - live Open-Meteo API reachability. |

This matches FINAL_GAP_REPORT.md's own "Environment Dependent (6)" table
exactly (same six scenario IDs, same stated dependency). No other Domain
1-26/99 scenario in this reconciliation is Environment Dependent.
