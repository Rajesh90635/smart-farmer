# Smart Farmer V3 — Prioritized Implementation Plan

Source: `docs/audit/FINAL_CANONICAL_group_{A,B,C,D}.md`, frozen this session per
`docs/FINAL_GAP_REPORT.md`'s "FROZEN CANONICAL COUNTS" — see that section for the full
reconciliation. Authoritative current-scope work remaining: **332** (223 Missing + 109
Partial + 0 Broken) — see "Summary counts" at the bottom of this document for the current
number; the 388 figure below is historical (predates this document's own P0-P4 batch, and
predates the P1 fixes, cluster #7 re-verification, and notification-wiring batch all
already applied since).

**Status update this session (P0 batch, before the rest of this plan's own work began):**
- **D97-12 (BROKEN) — FIXED.** `task_service.py::create_task` now guards against
  `_TERMINAL_CULTIVATION_STATUSES`, tested (`test_tasks.py`, 2 new tests). Reclassified
  VERIFIED. Removed from the P0 table below.
- **D78-07, D78-09 — VERIFIED, not just "kept in plan."** Both scenarios' underlying code
  already existed; D78-07 needed a new test (`test_payments.py::test_payment_failure_notifies_the_farmer`,
  added), D78-09 already had one. Neither needs further implementation work; removed from
  the notification-wiring section below.
- The original 390/391-row count below (superseded by 388 above) predates this fix batch;
  read "391" throughout this document's prose as historical, not current.

## Caveat resolutions

**D9-03 (Reminder, Domain 9) — RECLASSIFY FUTURE → MISSING, added to this plan.**
The original FUTURE citation (`PROJECT_STATUS.md:402`) rested entirely on "no background
scheduler anywhere in the project." That premise is now false: `backend/app/services/scheduler.py`
exists and runs on APScheduler (confirmed by direct file read and `find` on the repo), with
3 registered `add_job` calls already serving Expert-SLA reminders, weather sweeps, and
input-inventory expiry sweeps. The exact infrastructure D9-03 needs already exists and is
proven in production use. Included as MISSING, merged into the Task-overdue-reminder
cluster (see below) with D9-16/D78-01/D37-04 — one implementation closes all four.

**D9-14 (Dependent task, Domain 9) — LEAVE EXCLUDED, not added to this plan.**
D9-14 is a verbatim duplicate of D8-07 ("Task dependencies"), which is already VERIFIED via
`Task.depends_on_task_id` (confirmed present in `backend/app/models/task.py`). No
independent gap remains; recommend the next audit pass fold D9-14 into D8-07's VERIFIED
status rather than carrying it as a separate FUTURE row. Not part of this plan.

**D9-11 (Rejection, Domain 9) — LEAVE EXCLUDED (stays effectively Out-of-Scope), not added.**
Confirmed by grepping `backend/app/models/task.py` for `assignee|reviewer|Role\.`: zero
matches. No role-based task-assignment/review concept exists anywhere in the task domain —
every task is farmer-created-and-owned only. Unlike D9-03 (blocker was a stale technical
fact, now resolved) or D9-14 (literal duplicate of finished work), D9-11's absence is a
genuine product-scope question — should a second party ever be able to assign/review a
farmer's own tasks? — not a documented, ready-to-build technical gap. `CaseAssignment`
(expert-network disease consultation) is a structurally distinct concept and doesn't answer
this question. Recommend the product team explicitly confirm scope before this becomes a
plan item; kept out for now.

**D78-07 (Payment notification, Domain 78) — RESOLVED this session, VERIFIED.**
Direct read of `backend/app/services/payment_service.py` lines 113-126 confirmed
`_notify_payment_failed()` already fires `NotificationCategory.PAYMENT_ALERT` /
`message_key="PAYMENT_FAILED"` on payment failure (added for D66-04). This satisfies
D78-07's exact wording. Added `tests/test_payments.py::test_payment_failure_notifies_the_farmer`
to close the "code exists, no test" gap; full suite re-run confirmed passing. Reclassified
VERIFIED in `docs/audit/FINAL_CANONICAL_group_D.md`. Removed from this plan.

**D78-09 (Stock notification, Domain 78) — RESOLVED this session, VERIFIED.**
Direct read of `backend/app/services/input_inventory_service.py` lines 153-177 confirmed
`_check_low_stock()` already fires `NotificationCategory.STOCK_ALERT`/`message_key="INPUT_LOW_STOCK"`
(added for D22-06/D24-08/D24-09). This satisfies D78-09's exact wording, and — unlike
D78-07 — it already had a dedicated passing test
(`tests/test_input_inventory.py::test_low_stock_alert_fires_once_then_stays_quiet_until_restocked`),
so no new code or test was needed, only the stale MISSING label. Reclassified VERIFIED in
`docs/audit/FINAL_CANONICAL_group_D.md`. Removed from this plan.

**D35-06 (Case timeout, Domain 35) — excluded, confirmed correct.** Independently
re-verified this session by direct read of `case_sla_service.py::_expire_reassign_or_escalate`
(timeout detection, reassignment, escalation-on-breach all present) plus its dedicated test
file `tests/test_case_sla_service.py`. Already correctly VERIFIED in
`docs/audit/FINAL_CANONICAL_group_B.md`; no code change, no matrix change, no entry needed
in this plan.

## Dependency clusters

1. **Task-overdue-reminder** — D9-16 (A, Partial), D9-03 (A, reclassified above), D78-01 (D,
   Missing), D37-04 (B, Missing). Root: no scheduled sweep ever notifies a farmer that a task
   became overdue. One `task_reminder_service.py` sweep + a `TASK_ALERT`/`TASK_DUE` category
   registered on the existing `scheduler.py` closes all four scenario IDs at once.
2. **Concurrent active-cycle guard** — D6-07 (A, Partial), D11-05 (A, Partial); interacts
   with D12-01 (B... actually A, Missing — intercropping needs an explicit escape hatch from
   this same guard). Root: nothing stops two non-terminal `CropCycle` rows existing on one
   plot (an offline-replay/double-tap data-integrity risk).
3. **Irrigation/soil controlled-vocabulary enum** — D3-08, D3-09, D17-01 (all A, Partial).
   Root: `Plot.irrigation_type`/`soil_type` are unvalidated free text. One enum + migration
   closes all three (and retroactively validates the already-IMPLEMENTED D18-01..05/D19-01/02
   rows, which are not part of this plan).
4. **Cumulative-rainfall weather-risk** — D15-08 (flood), D15-09 (drought), D17-04
   (waterlogging), D17-05 (drought/water) — all A, Missing; D75-01 (flood-disaster), D75-02
   (drought-disaster) — both D, Missing. Root: no multi-day rainfall-accumulation query
   exists over the already-stored `weather_snapshots` history. One accumulation function
   serves all six scenario IDs, just tagged into different notification categories.
5. **WMO condition-code decoding** — D15-05 (storm), D15-07 (hail) — both A, Missing; D75-03
   (hail-disaster) — B... D, Missing. Root: Open-Meteo's `condition_code` is fetched and
   stored but never decoded into a friendly category.
6. **Soil Testing domain foundation** — D20-01 (root) through D20-13 (14 items, A, all
   Missing), plus D19-03 (sub-plot zoning, A), D19-05's suitability facet (A), D78-10 (soil
   notification, D). Root: no `SoilSample`/`SoilTestResult` model exists at all. Per this
   task's own instruction, an entirely-missing domain routinely depended on by farmers is
   still P1 — soil testing is exactly that.
7. **Input-inventory usage-tracking (likely-already-resolved)** — D21-07, D22-05, D23-06,
   D24-03, D24-04, D24-06, D24-07 (all A). Root: the canonical audit itself flags that
   Batch 3's `InputInventoryItem` work (create/usage/restock/correction/low-stock/expiry,
   all VERIFIED via delta) may already satisfy every one of these seven rows. Needs a direct
   re-read of `input_inventory_service.py` + its tests before any new code is written.
8. **Net-realization itemization (marketplace)** — D57-04 (root), D57-05, D57-06, D57-07,
   D58-02, D58-03, D58-04, D58-05, D58-06, D58-07, D55-08 (all C), plus D53-03/D69-08 (shared
   `STORAGE` ledger-category enum) and D55-04 (transport rate reference). Root:
   `AcceptOfferRequest.charges` is one undifferentiated farmer-entered lump sum.
9. **Storage domain foundation** — D53-01 (root) through D53-07 (C, Missing/Partial), plus
   D48-04, D52-04 (pointers into the same domain). Root: no `Storage` entity exists.
10. **Mandi/live market-price feed** — D56-01 (root) through D56-07 (C, all Missing), D57-02
    (C, Partial, cross-market comparison). Root: no real government Agmarknet/eNAM/data.gov.in
    integration exists; this project structurally never fabricates this data. D57-01 (Market
    registry) is a lighter, independently-buildable prerequisite, NOT part of this cluster.
11. **Machinery domain foundation** — D45-01 (root) through D45-08 (B, all Missing), D44-05
    (pointer). Root: no `Machinery` model exists anywhere.
12. **Labour domain foundation** — D46-01 (root), 02, 04, 05, 06 (B, Missing), D46-03 (B,
    Partial), D44-06 (pointer). Root: no Labour marketplace model exists.
13. **Nearby-services directories** — D44-07 (mandi), 08 (storage), 09 (cold storage), 10
    (soil lab), 11 (diagnostic centre) — all B, Missing. Root: each needs a sourced
    reference-data set + a simple lookup endpoint, the same pattern already proven and
    VERIFIED for D44-01 (Expert).
14. **Community domain foundation** — D43-01 (root) through D43-06 (B, all Missing); D43-07
    (AI triage) deliberately deferred, see P4. Root: no `CommunityPost` model exists.
15. **Education/Knowledge-base content** — D42-01 (root) through D42-10 (B; nine Missing +
    D42-03 Partial). Root: `KnowledgeEntry` table exists with zero rows — this is fundamentally
    a licensed-content-sourcing task, not an engineering one, before any serving endpoint has
    value.
16. **Pest AI-diagnosis foundation** — D28-01 through D28-07 (B, Missing, minus D28-06 which
    is deliberately safety-deferred), D29-03 (shared w/ D30-04), D29-05 (=D28-04), D29-06,
    D30-04/D30-05/D30-06 image-quality siblings, D95-04 (D, pest risk factor). Root: D28-02
    (pest-observation concept) and D28-04 (`predict_pest` model method) don't exist yet; real
    diagnostic accuracy is additionally blocked on the same "no real trained model" constraint
    that already applies to Disease (D27-04/D29-04).
17. **Voice/STT foundation** — D40-01 (root), D40-02, D40-03 (B, Missing), D1-11 (A, mic
    permission), D41-02 (B, Partial, location-based UI-language detection reusing the same
    resolver). Root: no speech-to-text package/service exists anywhere in the mobile app.
18. **actual_quantity production write-path (yield/analytics)** — D97-02, D96-09, D98-06 (all
    D) are only meaningfully non-null once `HarvestRecord.actual_quantity` is actually written
    by a real farmer-facing code path — the root cause itself is D49-02/D50-02 (C, both
    FUTURE, correctly outside this Missing/Partial plan, but must be fixed first for these
    three items to deliver real value; each is still buildable now as an honest
    insufficient-data placeholder).
19. **Generic offline `PendingWriteQueue<T>`** — D81-01 (root), 02, 03, 04, 06, 07 (D,
    Missing), D81-05/09 (blocked further on an `Observation`/`Notes` entity that doesn't exist
    at all), D82-06 (sync-status UI, D Partial), D78-12 (local sync notification, D Missing),
    D83-02 (backoff strategy, D Missing). Root: only crop-photo uploads have an offline queue
    today; every other write (farm/plot/crop/task/expense/harvest) is lost if made offline.
20. **Notification-delivery-provider abstraction** — D90-04 (D, Partial). Root: today every
    notification in this project is a DB row, in-app-only — there is no real push/SMS
    delivery channel. This affects the practical *reach* of every other notification-category
    item in this plan: a farmer who doesn't open the app will never see any of them, however
    many sweeps/categories get built.
21. **Satellite/NDVI (needs real imagery API + PostGIS)** — D76-01 (shared with D3-07's plot-
    boundary-polygon work), D76-02 (root, needs a Sentinel-Hub-class account), D76-03, D76-04,
    D76-05, D76-06, D76-07, D90-08 (dup of D76-06). Root: no satellite-imagery provider
    account exists, and `Plot` has no polygon geometry yet.
22. **IoT sensor/actuation (needs physical hardware)** — D77-01 (root) through D77-07 (D, all
    Missing). Root: no physical sensor/controller hardware exists; `irrigation_intelligence_service.py`
    already honestly hardcodes `soil_moisture_available=False` pending this.
23. **Grading-engine foundation** — D52-02 (root, C Partial), D51-03 (C), D51-07 (C, Partial),
    D59-04 (C, Partial), D61-04 (C, Partial, additionally blocked on D61-02 pooling). Root:
    `quality_grade` is unconstrained free text; no per-crop grading schema exists.
24. **Government/external-data ecosystem (Schemes, Insurance)** — D73-01 (root) through
    D73-06, D74-01 (root) through D74-05 (D, all Missing). Root: no authoritative government
    scheme/insurance dataset sourced; self-reported shells are independently buildable now,
    full automation needs a real feed.

---

## P0 — Security/data-loss/safety/core-workflow blockers

**D97-12 (new, BROKEN) is DONE, fixed and tested this session** —
`task_service.py::create_task` now checks `_TERMINAL_CULTIVATION_STATUSES` before
creating a task, matching its two sibling guards. 2 new passing tests in
`test_tasks.py`. Reclassified VERIFIED; removed from this table.

**P0 is now fully DONE, fixed and tested this session:**

| Scenario ID | Status | What happened |
|---|---|---|
| D97-12 (BROKEN) | DONE → VERIFIED | `create_task` now guards `_TERMINAL_CULTIVATION_STATUSES`; 2 new tests |
| D6-07 | DONE → VERIFIED | `create_crop_cycle` now rejects a second active cycle on one plot (409); 2 new tests |
| D11-05 | DONE → VERIFIED | Same fix/tests as D6-07 (identical underlying gap) |
| D68-02 | DONE → VERIFIED | `resolve_dispute` now rejects `refund_amount` ≤ 0 or > `order.final_amount`; 1 new test |
| D100-14 | Re-verified PARTIAL (no new work — already fixed by an earlier, undocumented pass) | Direct re-read found `InMemoryRateLimiter` already wired into login/OTP-request/reset-password **and** photo upload, each with a passing test. The specific gap this row named is closed. Genuinely remaining: global ASGI middleware + a Redis-backed multi-instance store — real infra this project doesn't have, not fabricated here, same disclosed-limitation pattern as other environment-scale gaps. |

Full backend suite after all four fixes: confirm via a full clean re-run (see
`docs/FINAL_RELEASE_READINESS.md`) — 0 regressions expected/required before moving to P1.

---

## P1 — Core farmer lifecycle & cross-module workflows

### Task management fundamentals

**DONE this session** — D9-05, D9-06, D9-09, D9-10, D9-12, D9-16, D9-03, D37-04, D78-01 all
VERIFIED (the task-overdue-reminder cluster, one build); D37-03 PARTIAL (the independent
priority-field half is VERIFIED, the recommendation-derived half stays blocked on unbuilt
D37-01). See `docs/audit/FINAL_CANONICAL_group_{A,B,D}.md` for each row's evidence. Removed
from this table.

| Scenario ID | Domain | Name | Why P1 | Depends on | Size |
|---|---|---|---|---|---|
| D78-12 | 78 Notifications | Sync notification | Local/in-app signal on terminal upload states; part of core offline reliability, cluster #19 | cluster #19 | S |

### Account/security lifecycle

**DONE this session** — D1-19 (Account deactivation) VERIFIED. See
`docs/audit/FINAL_CANONICAL_group_A.md`. Removed from this table (now empty).

### Crop-cycle/stage fundamentals

**D7-01, D7-03 DONE this session** (VERIFIED, optional additive stages); **D7-07 decided
OUT_OF_SCOPE** (documented product decision, not an arbitrary third stage). Removed from
this table.

| Scenario ID | Domain | Name | Why P1 | Depends on | Size |
|---|---|---|---|---|---|
| D5-02 | 5 Crop Variety | Variety creation (admin) | Core master-data gap — no write path for a reference table farmers depend on for crop selection | D4-02 cross-ref | M |
| D8-01 | 8 Crop Calendar | Dynamic calendar (cross-crop-cycle aggregation) | Farmers with multiple active cycles need one unified calendar — core daily workflow | none | M |
| D11-02 | 11 Re-Sowing | Farmer confirmation (re-sow UX) | Core crop lifecycle UX completing the already-VERIFIED re-sow linkage | D10-10/D11-01 (done) | S/M |
| D99-01 | 99 Special Crop Scenarios | Crop failure (cross-ref) | Pointer — resolved by the now-VERIFIED D10-04..07 rows | D10-04..07 (done) | S |
| D99-02 | 99 Special Crop Scenarios | Re-sowing (cross-ref) | Pointer — D11-05 is done; still blocked on D11-02 above | D11-02, D11-05 (done) | S |

### Crop-failure reason taxonomy

**DONE this session** — D10-04, D10-05, D10-06, D10-07 all VERIFIED (all four
`FailureReason` enum values already existed in code; this session added dedicated tests
plus D10-07's `failure_reason_note` field). See `docs/audit/FINAL_CANONICAL_group_A.md`.
Removed from this table (now empty).

### Weather-risk safety detections

**DONE this session** — D15-04 (frost, Magnus-formula dew point), D15-08/D17-04 (flood/
waterlogging, cumulative rainfall), D15-09/D17-05 (drought, consecutive dry days), D75-01/
D75-02 (disaster-tagged duplicates of D15-08/D15-09, reused `WEATHER_ALERT` rather than a
new `DISASTER_ALERT` category) all VERIFIED. See
`docs/audit/FINAL_CANONICAL_group_{A,D}.md`. Removed from this table (now empty).

### Irrigation/soil data quality

**DONE this session** — D3-08/D3-09/D17-01 (validated `IrrigationSource`/`SoilCategory`
enums on `Plot`, purely additive alongside the existing free text), D18-06 + D18-08 (new
`IrrigationRecord` model with a `failure_note` field), D24-04 (`InputInventoryItem.acquired_at`)
all VERIFIED. See `docs/audit/FINAL_CANONICAL_group_A.md`. Removed from this table (now
empty).

### Soil Testing domain foundation (cluster #6 — entirely missing but routinely depended on)

**DONE this session** — D20-01 through D20-12 (12 items) all VERIFIED: new `SoilSample`/
`SoilTestResult` models, every measured-value column (pH with a DB CHECK constraint,
N/P/K, organic carbon, EC, a flexible micronutrients JSONB), soil-report file upload
(storage only, no OCR — optional per this cluster's own citation), test date, and
`is_stale()` mirroring `WeatherSnapshot`'s pattern. D20-13 (Test reminder) deliberately NOT
built — it's a P2 item requiring a new scheduler sweep, out of this P1 batch's scope.
D19-05 (crop-linked soil surfacing) and D19-03 (reclassified FUTURE, a documented
non-build decision) also resolved alongside this cluster. See
`docs/audit/FINAL_CANONICAL_group_A.md` for full evidence. Removed from this table (now
empty except D20-13, still P2).

### Input-inventory usage-tracking (cluster #7)

**DONE this continuation session — re-verified, no new code needed.** Direct re-read of
`input_inventory_service.py` confirmed the suspicion below was correct: D21-07, D22-05,
D23-06, D24-03, D24-06, D24-07 all VERIFIED via the existing generic, category-agnostic
`record_usage`/`InputInventoryItem.unit`/`.quantity` decrement. See
`docs/audit/FINAL_CANONICAL_group_A.md`'s per-row entries. Removed from this table (now
empty).

### Marketplace/harvest core-workflow completeness
| Scenario ID | Domain | Name | Why P1 | Depends on | Size |
|---|---|---|---|---|---|
| D47-01 | 47 Harvest Readiness | Harvest approaching (audit log) | Small completeness gap on an already-core, VERIFIED workflow | none | S |
| D50-03 | 50 Yield | Yield/acre | Small, well-precedented (same pattern as VERIFIED D72-04/05/06) | D50-01 | S |
| D51-02 | 51 Quality | Moisture | Core harvest-quality capture, farmer-entered only | none | S |
| D51-03 | 51 Quality | Size (grading) | Cluster #23 (grading engine) | cluster #23 | S |
| D51-04 | 51 Quality | Defects | Core harvest-quality capture | none | S |
| D52-01 | 52 Post-Harvest | Sorting | Folds into cluster #23 | cluster #23 | S |
| D52-02 | 52 Post-Harvest | Grading (engine) | Root of cluster #23 | cluster #23 | M |
| D55-06 | 55 Transport | Pickup | Core sale-completion state, missing confirmation step | D62-08 | M |
| D55-07 | 55 Transport | Delivery | Core sale-completion state | D62-08 | M |
| D59-04 | 59 Buyer Matching | Quality (matching) | Cluster #23 | cluster #23 | S |
| D64-05 | 64 Payments | Payment date | Small, core payment visibility | none | S |
| D66-03 | 66 Failed Payments | Pending (timeout sweep) | Payments can sit PENDING forever with no resolution — core payment reliability | none | M |
| D67-05 | 67 Disputes | Seller/farmer response | Symmetric, small fix mirroring the existing buyer-response endpoint; core dispute-resolution completeness | D67-04 (done) | S |

### Season closure (cluster: closure-snapshot table)
| Scenario ID | Domain | Name | Why P1 | Depends on | Size |
|---|---|---|---|---|---|
| D97-02 | 97 Season Closure | Actual quantity at closure | Core season-close workflow; effectively blocked on actual_quantity (cluster #18) for real farmer value | cluster #18 | S |
| D97-03 | 97 Season Closure | Actual quality at closure | Shares D97-02's snapshot table | D97-04 (shared) | S |
| D97-04 | 97 Season Closure | Sale captured at closure | Root of the closure-snapshot table | none | M |
| D97-05 | 97 Season Closure | Revenue captured at closure | Shares D97-04's table | D97-04 | S |
| D97-06 | 97 Season Closure | Costs captured at closure | Shares D97-04's table | D97-04 | S |
| D97-07 | 97 Season Closure | Profit captured at closure | Shares D97-04's table | D97-04 | S |
| D97-08 | 97 Season Closure | Disease history at closure | Shares D97-04's table | D97-04 | S |
| D97-09 | 97 Season Closure | Weather impact at closure | Shares D97-04's table | D97-04 | S |

### Offline reliability (cluster #19) & notification delivery (cluster #20)
| Scenario ID | Domain | Name | Why P1 | Depends on | Size |
|---|---|---|---|---|---|
| D81-01 | 81 Offline | Farm offline | Root of the generic offline queue — rural connectivity makes this core, not optional | none | L |
| D81-02 | 81 Offline | Plot offline | Specialization of D81-01's queue | D81-01 | M |
| D81-03 | 81 Offline | Crop offline | Specialization | D81-01 | M |
| D81-04 | 81 Offline | Task offline | Specialization | D81-01 | M |
| D81-06 | 81 Offline | Expense offline | Specialization | D81-01 | M |
| D81-07 | 81 Offline | Harvest offline | Specialization | D81-01 | M |
| D81-05 | 81 Offline | Observation offline | Entity doesn't exist yet — larger than its siblings | D81-01 + new `Observation` model | M |
| D81-09 | 81 Offline | Notes offline | Same entity gap as D81-05, recommend unifying | D81-01, D81-05 | M |
| D82-06 | 82 Sync | Sync status (UI) | Farmer-visible sync state, part of core offline reliability | cluster #19 | M |
| D83-02 | 83 Retry | Exponential/backoff strategy | Prevents connectivity-flap retry storms | cluster #19 | S |
| D90-04 | 90 Provider Abstraction | Notification delivery provider | Cluster #20 — reach of every other notification in this plan depends on it; the ABC+honest-stub shell is buildable now without external credentials | none for the shell; real FCM/SMS needs an account | M |

### Notification wiring (small, core reliability)

**DONE this continuation session** — D78-03 (disease), D78-08 (dispute), D78-05 (harvest,
no code needed, already satisfied by D47-05) all VERIFIED. D78-13 (security) PARTIAL —
password-change alerting built and tested, new-device-login alerting genuinely not built
(no device/session fingerprinting exists in this codebase; disclosed as a remaining
limitation rather than fabricated). See `docs/audit/FINAL_CANONICAL_group_D.md`'s
D78-03/05/08/13 entries. Removed from this table (now empty).

*(D78-07 and D78-09 are DONE — resolved this session, see the caveat resolutions at the
top of this document. Removed from this table.)*

---

## P2 — Automation/AI/expert/weather/market/finance

### Weather automation & disaster-management (buildable now)
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D14-02 | 14 Weather | Hourly forecast | Weather-automation enhancement | none | M |
| D14-09 | 14 Weather | Severe weather (co-occurrence escalation) | Weather-automation enhancement | none | M |
| D15-05 | 15 Weather Risk | Storm (condition-code decode) | Cluster #5 | cluster #5 | S |
| D15-07 | 15 Weather Risk | Hail (condition-code decode) | Cluster #5 | cluster #5 | S |
| D16-01 | 16 Weather Automation | Weather to affected plot | Plot-level microclimate, explicitly-deferred phase boundary | D3-06/D3-07 (plot location) | M |
| D3-07 | 3 Plot | Plot boundary (polygon) | Shared root with D76-01 (satellite) — GIS infra enabling per-plot weather + future satellite work | none (PostGIS decision) | L |
| D75-03 | 75 Disaster Management | Hail alert/detection | Cluster #5 | cluster #5 | S |
| D75-06 | 75 Disaster Management | Heat advisory content | Buildable now, small | none | S |
| D75-07 | 75 Disaster Management | Frost wording | Buildable now, small | none | S |
| D75-08 | 75 Disaster Management | Damage detection (farmer-reported) | Buildable now as manual-report form | none | M |
| D75-09 | 75 Disaster Management | Evidence capture (disaster linkage) | Additive FK on CropPhoto | D75-08 | S |
| D75-10 | 75 Disaster Management | Inspection (case-type reuse) | Reuses existing case-routing infra | D75-08 | M |
| D75-11 | 75 Disaster Management | Recovery guidance | Static advisory content | D75-08 | S |
| D76-01 | 76 Satellite | Plot boundary (shared with D3-07) | Same build as D3-07 — buildable without a satellite API account | D3-07 | (shared) |
| D19-04 | 19 Soil | Soil history | Data-quality/history feature | none | M |
| D19-05 | 19 Soil | Crop-linked soil surfacing | Small read-only surfacing | none | S |
| D20-13 | 20 Soil Testing | Test reminder | Notification/automation angle of cluster #6 | cluster #6 | S |
| D78-10 | 78 Notifications | Soil notification | Blocked on cluster #6 | cluster #6 | S |
| D78-06 | 78 Notifications | Market notification | New category + wiring to price/offer changes | D94-05 (shared trigger) | M |
| D78-11 | 78 Notifications | Disaster notification | New category, shared with D75 cluster | D75 buildable rows | S |
| D79-04 | 79 Notification Dedup | Expiry (TTL) | Reuses existing scheduler | scheduler.py (done) | M |

### Pest / AI diagnosis / image quality (cluster #16)
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D27-02 | 27 Disease | Disease observation (notes field) | AI/disease governance completeness | none | S |
| D28-01 | 28 Pest | Pest risk (factor) | Cluster #16 | cluster #16 | S |
| D28-02 | 28 Pest | Pest observation | Root of cluster #16 | cluster #16 | M |
| D28-03 | 28 Pest | Pest photo | Cluster #16 | D28-02 | S |
| D28-04 | 28 Pest | Pest diagnosis (AI) | Cluster #16 | D28-02/03 | M |
| D28-05 | 28 Pest | Pest history | Cluster #16 | D28-04 | S |
| D28-07 | 28 Pest | Follow-up (pest) | Cluster #16 | D28-04 | S |
| D29-02 | 29 AI Diagnosis | Crop identification | New model-provider method | none (no real model — accuracy env-dependent) | M |
| D29-03 | 29 AI Diagnosis | Plant-part identification | Shares build with D30-04 | D30-04 | M |
| D29-05 | 29 AI Diagnosis | Pest detection | Same as D28-04 | D28-04 | M (shared) |
| D29-06 | 29 AI Diagnosis | Nutrient deficiency | New model-provider method | none | M |
| D30-03 | 30 Image Quality | Wrong framing | Extends existing quality-check pipeline | none | S |
| D30-04 | 30 Image Quality | Wrong plant part | Shares build with D29-03 | D29-03 | M |
| D30-05 | 30 Image Quality | Duplicate photo | Perceptual-hash check, additive | none | S |
| D30-06 | 30 Image Quality | Old photo (staleness) | Capture-timestamp check | none | S |
| D31-05 | 31 AI Confidence | Expert escalation (auto) | Opt-in auto-case-creation on low confidence | consent design | M |
| D32-04 | 32 Unknown Diagnosis | Ask additional question | Structured clarification-question bank | none | M |
| D32-05 | 32 Unknown Diagnosis | Expert escalation | Shared fix with D31-05 | D31-05 | S |
| D38-01 | 38 Follow-up | Follow-up date (field) | Feeds D38-02 reminder | none | S |
| D38-02 | 38 Follow-up | Reminder | Scheduler sweep | D38-01 | M |
| D38-05 | 38 Follow-up | Reschedule | Small endpoint | D38-01 | S |
| D39-... | — | (no P2 items; D39-03 is P4, see below) | — | — | — |
| D91-03 | 91 AI Governance | Input metadata captured | Additive fields | none | S |
| D91-08 | 91 AI Governance | Outcome tracked vs. recommendation | Extends new D91-07 correction endpoint | D91-07 (done) | S |
| D91-09 | 91 AI Governance | False positive tracking | Aggregation over new `farmer_correction` rows | D91-07 (done) | M |
| D91-10 | 91 AI Governance | False negative tracking | Shares D91-09's service | D91-09 | S |
| D95-04 | 95 Risk Dashboard | Pest risk factor | Blocked on cluster #16 | cluster #16 | S |

### Voice/STT (cluster #17)
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D40-01 | 40 Voice | Voice input (STT) | Root of cluster #17 | cluster #17 | L |
| D40-02 | 40 Voice | Speech-to-text (provider abstraction) | Same build as D40-01 | D40-01 | M |
| D40-03 | 40 Voice | Voice question (wiring) | Small once D40-01/02 exist | D40-01/02 | S |
| D40-05 | 40 Voice | "What should I do today?" intent | Small intent-router addition | none | S |

### Expert network completeness
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D34-04 | 34 Expert Assignment | Expert response (professional-facing mobile UI) | Expert-network completeness — a whole new professional-facing screen set | scope decision (separate app surface?) | L |
| D36-03 | 36 Expert Recommendation | Evidence | Additive FK, respects existing photo-grant scoping | none | M |
| D36-04 | 36 Expert Recommendation | Farmer acknowledgement | Small read-receipt endpoint | none | S |
| D36-06 | 36 Expert Recommendation | Expert identity | Needs a professional-side consent flag first | new consent flag | M |
| D36-07 | 36 Expert Recommendation | Recommendation version | Self-referential FK for second opinions | none | M |
| D37-01 | 37 Recommendation→Task | Recommendation creates task | Root of the Recommendation→Task domain (farmer-confirmed, never auto-created) | none | M |
| D37-02 | 37 Recommendation→Task | Due date | Extends D37-01 | D37-01 | S |
| D37-05 | 37 Recommendation→Task | Completion | Auto-resolves once D37-01 exists | D37-01 | S |
| D37-06 | 37 Recommendation→Task | Follow-up | Links to existing Treatment/Follow-up machinery | D37-01 | S |
| D10-08 | 10 Crop Failure | Failure confirmation (expert review) | Optional expert-review layer over the already-VERIFIED self-report | Domain 33-39 infra (done) | M |

### Data provenance / rule versioning (AI governance completeness)
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D88-01 | 88 Data Provenance | Source recorded | Additive field across risk/notification outputs | none | M |
| D88-03 | 88 Data Provenance | Fetch date recorded | Expose an existing column | none | S |
| D88-04 | 88 Data Provenance | Effective date recorded | Extends D89-08's system | D89-08 | S |
| D88-05 | 88 Data Provenance | Region recorded | Surfaces existing Mandal/Village FK | none | S |
| D88-06 | 88 Data Provenance | Crop linkage recorded | New FK on ReferencePrice | none | M |
| D88-07 | 88 Data Provenance | Rule version (extend to weather-action) | Pattern already proven twice | none | S |
| D88-09 | 88 Data Provenance | Confidence recorded (parity) | Documentation or small schema field | none | S |
| D88-10 | 88 Data Provenance | Freshness/staleness flagged (parity) | Mirrors weather's existing `is_stale` | none | M |
| D89-01 | 89 Rule Versioning | Rule identifier | Constant per rule module | none | S |
| D89-02 | 89 Rule Versioning | Rule version (last module) | Pattern already proven twice | none | S |
| D89-03 | 89 Rule Versioning | Effective-date scoping | Part of D89-08's full system | D89-08 | M |
| D89-04 | 89 Rule Versioning | Region scoping | Reuses seeded Mandal/Village data | D89-05 | M |
| D89-05 | 89 Rule Versioning | Crop scoping | Needs a validated per-crop threshold source | authoritative dataset | M |
| D89-06 | 89 Rule Versioning | Crop-stage scoping | Extends D89-05 | D89-05, dataset | M |
| D89-07 | 89 Rule Versioning | Audit of rule firing | Reuses existing `AuditLogger` pattern | D89-01/02 | S |
| D89-08 | 89 Rule Versioning | Full rule-version history | Root of the rule-versioning system | none | L |
| D90-02 | 90 Provider Abstraction | Market provider abstraction | Refactor of an already-working feature into the established interface shape | none | M |
| D92-04 | 92 Farm Brain | Multi-crop stage coverage | Loop over all active cycles instead of one | none | S |
| D92-07 | 92 Farm Brain | Market included | Add a price-trend line | none | S |
| D92-09 | 92 Farm Brain | Priority/scoring across brief lines | Reorder by real severity | D92 batch (done) | M |
| D93-03 | 93 Daily Farm Brief | Weather actions summarized | Surface existing `crop_action` field | none | S |
| D93-05 | 93 Daily Farm Brief | Irrigation summarized | Wrap existing `irrigation_intelligence_service.py` | none | S |
| D93-06 | 93 Daily Farm Brief | Crop-stage actions summarized | Small lookup table | none | S |
| D93-08 | 93 Daily Farm Brief | Market summarized | Shared fix with D92-07 | D92-07 | S |
| D94-01 | 94 What Changed | Weather changed | Extends D94-08's diff mechanism | D94-08 (done) | S |
| D94-02 | 94 What Changed | Crop stage changed | Extends D94-08 | D94-08 (done) | S |
| D94-03 | 94 What Changed | Risk changed | Extends D94-08, may need a new snapshot table | D94-08 (done) | M |
| D94-04 | 94 What Changed | Task changed | Extends D94-08 | D94-08 (done) | S |
| D94-05 | 94 What Changed | Market changed | Extends D94-08 + D92-07's market wiring | D94-08 (done), D92-07 | S |
| D94-06 | 94 What Changed | Expert responded | Surfaces existing D78-04 notification in the diff view | D78-04 (done) | S |
| D94-07 | 94 What Changed | Payment changed | Extends D94-08; reuses D78-07's now-VERIFIED PAYMENT_ALERT event | D94-08 (done), D78-07 (done) | S |
| D95-05 | 95 Risk Dashboard | Water/irrigation risk factor | Reuses existing irrigation-intelligence service, reports UNKNOWN honestly | none | S |
| D95-06 | 95 Risk Dashboard | Harvest risk factor | Reuses existing harvest-readiness logic | D47-05 (done) | S |
| D95-07 | 95 Risk Dashboard | Market risk factor | Reuses existing reference-price history | sufficient price history | S |
| D95-08 | 95 Risk Dashboard | Payment risk factor | Reuses existing order/payment data | none | S |
| D96-01 | 96 Season Comparison | Compare crop | Small derived boolean | none | S |
| D96-02 | 96 Season Comparison | Compare variety | Small derived field | none | S |
| D96-07 | 96 Season Comparison | Compare disease history | Reuses existing services | none | S |
| D96-08 | 96 Season Comparison | Compare weather impact | Reuses existing weather-action history | none | S |
| D96-09 | 96 Season Comparison | Compare market realization | Cluster #18 | cluster #18 | S |
| D98-03 | 98 Historical Learning | Cost pattern signal | Extends personalization service, evidence-floor gated | none | S |
| D98-04 | 98 Historical Learning | Disease pattern signal | Same pattern | none | S |
| D98-05 | 98 Historical Learning | Weather impact signal | Same pattern | none | S |
| D98-06 | 98 Historical Learning | Market realization signal | Cluster #18 (per-unit variant); revenue-only variant is independent | cluster #18 | S |

### Finance/market workflows
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D5-04 | 5 Crop Variety | Variety-specific duration (prefill) | Small forecasting nicety | none | S |
| D8-06 | 8 Crop Calendar | Weather-adjusted tasks (opt-in reschedule) | Explicit farmer-confirmation step, weather automation | D16-06/07 (design boundary) | M |
| D13-01 | 13 Perennial Crops | Long-running crop cycle | Mostly a documentation/product decision | none | S |
| D13-02 | 13 Perennial Crops | Multiple seasons (history) | Perennial-crop history tracking | none | M |
| D13-05 | 13 Perennial Crops | Pruning (task type) | Additive enum | none | S |
| D13-06 | 13 Perennial Crops | Crop-year history | Aggregation rollup | D13-02 | M |
| D99-04 | 99 Special Crop Scenarios | Perennial crops (cross-ref) | Pointer to D13 cluster | D13-01/02/05/06 | S |
| D51-07 | 51 Quality | Quality-based price | Blocked on cluster #23 | cluster #23 | M |
| D52-03 | 52 Post-Harvest | Packing | Small free-text field + assistant wiring | none | S |
| D53-03 | 53 Storage | Cost | Shared `STORAGE` ledger enum with D69-08; feeds cluster #8 | D69-08 | S |
| D55-03 | 55 Transport | Distance (privacy-safe) | Coarse district-adjacency signal only | none | S |
| D55-04 | 55 Transport | Rate (reference table) | Feeds cluster #8's itemization | cluster #8 | M |
| D55-05 | 55 Transport | Scheduling | Pickup/delivery date fields | D55-06/07 | M |
| D55-08 | 55 Transport | Cost | Cluster #8 | cluster #8 | S |
| D57-01 | 57 Market Comparison | Multiple markets (registry) | Admin-seeded reference entity, buildable without a live feed | none | M |
| D57-03 | 57 Market Comparison | Distance (to market/buyer) | Same privacy-safe approach as D55-03 | D55-03 | S |
| D57-04 | 57 Market Comparison | Transport cost | Root of cluster #8 | cluster #8 | M |
| D57-05 | 57 Market Comparison | Commission | Cluster #8 | cluster #8 | S |
| D57-06 | 57 Market Comparison | Storage cost | Cluster #8 | cluster #8 | S |
| D57-07 | 57 Market Comparison | Net realization | Cluster #8 | cluster #8 | S |
| D58-02 | 58 Net Realization | Transport (deduction) | Cluster #8 | cluster #8 | S |
| D58-03 | 58 Net Realization | Commission (deduction) | Cluster #8 | cluster #8 | S |
| D58-04 | 58 Net Realization | Handling (deduction) | Cluster #8 | cluster #8 | S |
| D58-05 | 58 Net Realization | Storage (deduction) | Cluster #8 | cluster #8 | S |
| D58-06 | 58 Net Realization | Net realization (final) | Cluster #8 | cluster #8 | S |
| D58-07 | 58 Net Realization | Comparison (across options) | Cluster #8 + D57-01 registry | cluster #8, D57-01 | M |
| D59-05 | 59 Buyer Matching | Location (matching) | Filter/sort respecting existing privacy design | none | M |
| D65-01 | 65 Partial Payments | Partial payment | Root of the partial-payment model change | none | M |
| D65-02 | 65 Partial Payments | Remaining balance tracking | Extends D65-01 | D65-01 | S |
| D65-03 | 65 Partial Payments | Multiple payments (installments) | Extends D65-01/02 | D65-01/02 | S |
| D65-04 | 65 Partial Payments | Balance tracking (ledger-level) | Extends D65-01..03 + existing sale-import | D65-01..03, D70-01 (done) | M |
| D65-05 | 65 Partial Payments | Payment history (list) | Buildable independently, low effort | none | S |
| D67-03 | 67 Disputes | Evidence (photo upload) | Dedicated dispute-evidence pipeline | D67-01 (done) | M |
| D69-08 | 69 Expenses | Storage expense (ledger category) | Shared enum with D53-03 | D53-03 | S |
| D70-04 | 70 Revenue | Plot association | Pointer — same join as D71-05 | D71-05 | S |
| D70-05 | 70 Revenue | Season association | Pointer — same join as D71-07 | D71-07 | S |
| D71-05 | 71 Profit | Plot P&L | New aggregation service | none | M |
| D71-06 | 71 Profit | Farm P&L | Built on top of D71-05 | D71-05 | M |
| D71-07 | 71 Profit | Season P&L | Same pattern as D71-05 | none | M |
| D50-04 | 50 Yield | Historical yield | Aggregation over estimated quantity (doesn't need actual_quantity) | D50-01 | M |
| D50-06 | 50 Yield | Confidence (on yield figures) | New enum field | none | S |

### Auth/session reliability
| Scenario ID | Domain | Name | Why P2 | Depends on | Size |
|---|---|---|---|---|---|
| D84-01 | 84 Auth Expiry | Token expires during normal use (401 interceptor) | Reliability/UX polish, not a security vulnerability | `/auth/refresh` (done) | M |
| D87-01 | 87 Dead-letter | Permanent failure (test coverage) | Test-only gap on existing logic | none | S |
| D87-02 | 87 Dead-letter | Dead-letter state (server visibility) | New admin-facing report endpoint | none | M |

---

## P3 — Ecosystem/integration features

### Community domain (cluster #14)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D43-01 | 43 Community | Farmer question | Root of cluster #14 | cluster #14 | L |
| D43-02 | 43 Community | Farmer discussion | Cluster #14 | D43-01 | M |
| D43-03 | 43 Community | Expert answer (public) | Cluster #14 | D43-01/02 | M |
| D43-04 | 43 Community | Verification | Reuses D43-03's flag | D43-03 | S |
| D43-05 | 43 Community | Moderation | Should ship before/alongside public launch | D43-01/02 | M |
| D43-06 | 43 Community | Abuse/reporting | Farmer-facing half of D43-05 | D43-01/02, D43-05 | M |

### Education/knowledge-base (cluster #15)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D42-01 | 42 Education | Crop education | Root — content-sourcing task | cluster #15 | L |
| D42-03 | 42 Education | Disease education | Blocked on the entire cluster #15 (KnowledgeEntry must be populated first) | cluster #15, D42-01/06/10 | M |
| D42-02 | 42 Education | Stage-specific education | Cluster #15 | D42-01 | S |
| D42-04 | 42 Education | Pest education | Cluster #15 | D42-01, D28 cluster | S |
| D42-05 | 42 Education | Weather education | Cluster #15 | D42-01 | S |
| D42-06 | 42 Education | Text (format) | Same work as D42-01 | D42-01 | S |
| D42-07 | 42 Education | Image (format) | Cluster #15 | D42-01 | S |
| D42-08 | 42 Education | Audio (format) | Reuses existing TTS, no new infra | D42-01/06 | S |
| D42-09 | 42 Education | Video (format) | New video-player dependency, heavier lift | D42-01 | M |
| D42-10 | 42 Education | Expert-verified content (gating) | Enforcement only, schema exists | D42-01 | S |

### Machinery domain (cluster #11)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D44-05 | 44 Nearby Services | Machinery (pointer) | See D45 cluster | cluster #11 | S (pointer) |
| D45-01 | 45 Machinery | Machinery search | Root of cluster #11 | cluster #11 | L |
| D45-02 | 45 Machinery | Availability | Cluster #11 | D45-01 | M |
| D45-03 | 45 Machinery | Rental | Same build as D45-06 | D45-06 | S (shared) |
| D45-04 | 45 Machinery | Rate | Cluster #11 | D45-01 | M |
| D45-05 | 45 Machinery | Schedule | Same build as D45-02 | D45-02 | S (shared) |
| D45-06 | 45 Machinery | Booking | State-machine, mirrors Order | D45-01/02/04 | L |
| D45-07 | 45 Machinery | Cancellation | Extends D45-06 | D45-06 | S |
| D45-08 | 45 Machinery | Completion | Extends D45-06 | D45-06 | S |

### Labour domain (cluster #12)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D44-06 | 44 Nearby Services | Labour (pointer) | See D46 cluster | cluster #12 | S (pointer) |
| D46-01 | 46 Labour | Labour requirement | Root of cluster #12 | cluster #12 | M |
| D46-02 | 46 Labour | Availability | Cluster #12, design-decision-dependent | D46-01 | S |
| D46-03 | 46 Labour | Cost | Blocked on D46-01/02 for a real rate/quote feature | D46-01/02 | S |
| D46-04 | 46 Labour | Schedule | Date-range fields | D46-01 | S |
| D46-05 | 46 Labour | Assignment | Small state machine | D46-01/04 | M |
| D46-06 | 46 Labour | Completion | Extends D46-05 | D46-05 | S |

### Nearby-services directories (cluster #13)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D44-02 | 44 Nearby Services | Dealer (location filter) | Small additive filter | none | M |
| D44-03 | 44 Nearby Services | Seed supplier (filter) | Shares D44-02's filter | D44-02 | S |
| D44-04 | 44 Nearby Services | Fertilizer supplier (filter) | Shares D44-02's filter | D44-02 | S |
| D44-07 | 44 Nearby Services | Mandi | Cluster #13 | cluster #13 | M |
| D44-08 | 44 Nearby Services | Storage | Cluster #13, feeds D53 cluster #9 too | cluster #13 | M |
| D44-09 | 44 Nearby Services | Cold storage | Shares D44-08's model | D44-08 | S |
| D44-10 | 44 Nearby Services | Soil lab | Easiest of the D44 gaps — reuses expert-directory pattern directly | none | M |
| D44-11 | 44 Nearby Services | Diagnostic centre | May share model with D44-10 | D44-10 (design) | M |
| D44-13 | 44 Nearby Services | Transporter | Seeds `Role.TRANSPORTER`, reuses expert-matching pattern | delivery_service.py design | L |

### Harvest planning (pre-harvest logistics — ecosystem, not core recording)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D48-01 | 48 Harvest Planning | Labour planning | New pre-harvest planning entity, ecosystem/logistics not core harvest recording | none | M |
| D48-02 | 48 Harvest Planning | Machinery planning | Same pattern as D48-01 | D48-01 (shared convention) | M |
| D48-03 | 48 Harvest Planning | Transport planning (pre-harvest) | Same pattern as D48-01 | D48-01 (shared convention) | M |
| D48-05 | 48 Harvest Planning | Buyer planning (pre-harvest) | Larger forward-contract-style feature, builds on future D59-07 matching | D59-07 (FUTURE, not in this plan) | L |

### Storage domain foundation (cluster #9)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D48-04 | 48 Harvest Planning | Storage planning (pointer) | Blocked on D53 | cluster #9 | S (pointer) |
| D51-06 | 51 Quality | Certificate | Low-value placeholder field | none | S |
| D52-04 | 52 Post-Harvest | Storage (pointer) | Blocked on D53 | cluster #9 | S (pointer) |
| D52-05 | 52 Post-Harvest | Transport (pointer) | Duplicate summary of D55 cluster | D55 rows | S (pointer) |
| D53-01 | 53 Storage | Storage location | Root of cluster #9 | cluster #9 | L |
| D53-02 | 53 Storage | Capacity | Extends D53-01 | D53-01 | S |
| D53-04 | 53 Storage | Duration | New usage-record model | D53-01 | M |
| D53-05 | 53 Storage | Stored quantity | Extends D53-04 | D53-04 | S |
| D53-07 | 53 Storage | Release from storage | Extends D53-04 | D53-04 | S |

### FPO/pooling (ecosystem cooperative feature)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D61-02 | 61 FPO | Aggregation (pooling) | Large structural change to a single-farmer-per-listing model | none | XL |
| D61-03 | 61 FPO | Bulk quantity | Extends D61-02 | D61-02 | S |
| D61-04 | 61 FPO | Grading (pooled) | Blocked on D61-02 + cluster #23 | D61-02, cluster #23 | S |
| D61-05 | 61 FPO | Packing (group) | Blocked on D61-02 | D61-02 | S |
| D61-07 | 61 FPO | Group transport | Blocked on D61-02 + D55 domain | D61-02 | S |

### Government schemes / insurance (cluster #24)
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D73-01 | 73 Government Schemes | Scheme discovery | Root of cluster #24 | cluster #24 | L |
| D73-02 | 73 Government Schemes | Eligibility check | Cluster #24 | D73-01 | M |
| D73-03 | 73 Government Schemes | Required-documents checklist | Cluster #24 | D73-01 | S |
| D73-04 | 73 Government Schemes | Application status tracking | Self-reported shell buildable now; real status feed is a further external dependency | D73-01 | M |
| D73-05 | 73 Government Schemes | Notifications | Cluster #24 | D73-01/02 | S |
| D73-06 | 73 Government Schemes | Official-source boundary (guardrail) | Design/UI discipline shipping with D73-01/04 | D73-01/04 | S |
| D74-01 | 74 Crop Insurance | Policy record | Root, farmer-self-reported | none | M |
| D74-02 | 74 Crop Insurance | Crop damage record | Extends D74-01 | D74-01 | S |
| D74-03 | 74 Crop Insurance | Evidence capture | Reuses existing photo pipeline | D74-02 | S |
| D74-05 | 74 Crop Insurance | Claim status tracking | Self-reported shell; real insurer feed is a further dependency | D74-01 | M |

### Misc plot/farm/account ecosystem gaps
| Scenario ID | Domain | Name | Why P3 | Depends on | Size |
|---|---|---|---|---|---|
| D1-11 | 1 Account | Microphone permission | Cluster #17 prerequisite, not itself core | cluster #17 | S |
| D1-17 | 1 Account | Multiple users/roles resolution | RBAC edge case, no active use case yet | none | S |
| D2-06 | 2 Farm | Farm history | Nice-to-have audit view | none | S |
| D2-07 | 2 Farm | Farm infrastructure | Informational, non-blocking | none | M |
| D2-08 | 2 Farm | Farm-level irrigation rollup | Cosmetic rollup | cluster #3 | S |
| D2-09 | 2 Farm | Farm-level soil rollup | Cosmetic rollup | cluster #3 | S |
| D3-06 | 3 Plot | Plot location (hierarchy) | Edge case — plots normally inherit farm's hierarchy | none | S |
| D3-12 | 3 Plot | Previous crop (surfaced field) | Nice-to-have | none | S |
| D7-11 | 7 Crop Stages | Closed (computed flag) | Cosmetic API convenience | none | S |
| D9-08 | 9 Task Automation | Partial completion | Contingent on a product decision; not needed for most task types | none | S |
| D12-01 | 12 Intercropping | Multiple crops in same plot | Genuine product-scope decision, non-core | D6-07/D11-05 escape hatch | L |
| D12-02 | 12 Intercropping | Crop-specific information | Contingent on D12-01 | D12-01 | S |
| D12-03 | 12 Intercropping | Crop-specific tasks | Contingent on D12-01 | D12-01 | S |
| D12-04 | 12 Intercropping | Crop-specific risks (isolation test) | Contingent on D12-01 | D12-01 | S |
| D12-05 | 12 Intercropping | Crop-specific harvest (isolation test) | Contingent on D12-01 | D12-01 | S |
| D12-06 | 12 Intercropping | Crop-specific finance (isolation test) | Contingent on D12-01 | D12-01 | S |
| D99-03 | 99 Special Crop Scenarios | Intercropping (cross-ref) | Pointer to D12 cluster | D12-01..06 | S |
| D17-02 | 17 Water | Water availability | Ecosystem, blocked on D17-01 | D17-01 | M |
| D17-03 | 17 Water | Water shortage | Ecosystem | D17-01/02, cluster #4 | M |
| D17-06 | 17 Water | Water history | Ecosystem history view | D17-01/02 | M |
| D21-03 | 21 Seeds | Seed variety (linkage) | Marketplace/catalog enhancement | D5-02 | M |
| D22-02 | 22 Fertilizer | Fertilizer selection (category filter) | Marketplace UX | none | S |
| D24-10 | 24 Input Inventory | Inventory history | Nice-to-have | cluster #7 | M |
| D25-01 | 25 Input Purchase | Search (category/manufacturer/price filters) | Marketplace UX | D22-02 | S |
| D26-02 | 26 Input Verification | Product image upload | Marketplace, reuses existing storage pattern | none | M |
| D41-02 | 41 Local Language | Auto-detect location (UI language) | Reuses cluster #17's resolver, small UX addition | cluster #17 | S |
| D41-03 | 41 Local Language | Local-language UI (dealer-marketplace) | String-extraction/localization content work | none | M |
| D41-04 | 41 Local Language | Local-language advisory (translation) | Native-speaker translation review, not engineering | none | M |

---

## P4 — Environment-dependent / Future-blocked

### Real-hardware / real-external-API dependencies
| Scenario ID | Domain | Name | Blocking prerequisite | Size (if pursued) |
|---|---|---|---|---|
| D76-02 | 76 Satellite | Vegetation signal (NDVI) | Real satellite-imagery API account (e.g. Sentinel Hub) | L |
| D76-03 | 76 Satellite | Stress anomaly detection | D76-02 accumulated history | M |
| D76-04 | 76 Satellite | Change detection | D76-02 accumulated history | M |
| D76-05 | 76 Satellite | Inspection trigger | D76-03 | S |
| D76-06 | 76 Satellite | Provider abstraction | Meaningless without a real provider account | M |
| D76-07 | 76 Satellite | Safety guardrail (never declare failure from satellite alone) | Must ship with D76-02/03, sequenced together | S |
| D90-08 | 90 Provider Abstraction | Satellite/NDVI provider abstraction | Same as D76-06 (duplicate) | M (shared) |
| D77-01 | 77 IoT | Soil moisture (live sensor) | Physical sensor hardware + telemetry channel | L |
| D77-02 | 77 IoT | Temperature (on-farm sensor) | Physical sensor hardware | M |
| D77-03 | 77 IoT | Humidity (on-farm sensor) | Physical sensor hardware | M |
| D77-04 | 77 IoT | Weather station | Physical station hardware | M |
| D77-05 | 77 IoT | Irrigation controller (actuation) | Physical valve/pump + command interface; must ship with D77-07 consent gate | L |
| D77-06 | 77 IoT | Provider abstraction | Real implementations need hardware | M |
| D77-07 | 77 IoT | Authorization-before-actuation (consent gate) | Must precede D77-05, reuses existing ConsentRecord pattern | S |
| D56-01 | 56 Market Prices | Mandi price (real feed) | Real Agmarknet/eNAM/data.gov.in API account | XL |
| D56-02 | 56 Market Prices | Min price | D56-01 | S |
| D56-03 | 56 Market Prices | Max price | D56-01 | S |
| D56-04 | 56 Market Prices | Modal price | D56-01 | S |
| D56-05 | 56 Market Prices | Arrivals | D56-01 | S |
| D56-06 | 56 Market Prices | Historical price | D56-01 | S |
| D56-07 | 56 Market Prices | Price freshness | D56-01 | S |
| D57-02 | 57 Market Comparison | Price comparison (across markets) | D56-01 + D57-01 | M |
| D75-04 | 75 Disaster Management | Storm alert/detection (real classification) | Real wind-gust/cyclone-track feed (e.g. IMD) | M |
| D75-05 | 75 Disaster Management | Cyclone alert/detection | Real IMD cyclone-bulletin feed | M |
| D75-12 | 75 Disaster Management | Insurance boundary (guardrail) | Design constraint for future D74/D75 linkage; no code yet | S |
| D90-03 | 90 Provider Abstraction | Maps/geocoding provider | Real geocoding API account | M |

### Recommend FUTURE/OUT_OF_SCOPE, no work should be built now
| Scenario ID | Domain | Name | Blocking prerequisite | Size (if ever pursued) |
|---|---|---|---|---|
| D5-05 | 5 Crop Variety | Variety-specific recommendations | Authoritative per-variety agronomic dataset (anti-fabrication boundary) | N/A |
| D11-06 | 11 Re-Sowing | New task generation | Same deliberate deferral as D9-01/D8-02 (no validated agronomic rule dataset) | N/A |
| D15-06 | 15 Weather Risk | Cyclone | Real IMD/meteorological-agency feed; recommend reclassify OUT_OF_SCOPE | N/A |
| D16-03 | 16 Weather Automation | Weather to crop-stage sensitivity | Authoritative per-crop/stage threshold source | N/A |
| D19-03 | 19 Soil | Soil location (sub-plot zoning) | D20 Soil Testing foundation; low value until then | N/A |
| D22-01 | 22 Fertilizer | Fertilizer requirement calculator | Deliberate safety boundary (`PRODUCT_SAFETY.md`) — should not be built | N/A |
| D26-04 | 26 Input Verification | Authenticity information (QR/barcode) | Real manufacturer/registry verification relationship | N/A |
| D28-06 | 28 Pest | Pest recommendation | Same safety-deferred boundary as D27-06 | N/A |
| D39-03 | 39 Reinspection | Disease status (severity score) | Hard-blocked on a real trained AI model | N/A |
| D43-07 | 43 Community | AI triage | Should follow, not precede, human moderation (D43-05); not recommended as first pass | N/A |
| D44-12 | 44 Nearby Services | Veterinary centre | Requires an entirely new livestock domain — product-scope decision | N/A |
| D52-07 | 52 Post-Harvest | Spoilage risk | Authoritative per-crop shelf-life reference dataset | N/A |
| D53-06 | 53 Storage | Spoilage (in storage) | Same dataset blocker as D52-07 | N/A |

### Already resolved / no work required — recommend reclassification, not a live plan item
| Scenario ID | Domain | Name | Note | Size |
|---|---|---|---|---|
| D1-14 | 1 Account | Automated-action consent | Enum-only infra; no automated mutating action exists yet to gate | S |
| D2-10 | 2 Farm | Active farm selection | Deliberate stateless design, not a real gap | S |
| D4-07 | 4 Crop | Crop failure | Fully subsumed by the now-VERIFIED D10-01/02/03 | S |
| D7-10 | 7 Crop Stages | Post-harvest | Out of this domain's scope — belongs to the Harvest cluster, already handled there | S |
| D9-13 | 9 Task Automation | Recurring task (dup) | Duplicate of the now-VERIFIED D8-07/D8-08 | S |
| D10-11 | 10 Crop Failure | Season closure after failure | Fully resolved by the now-VERIFIED D10-01 delta | S |
| D13-04 | 13 Perennial Crops | Recurring maintenance | Fully covered by the now-VERIFIED D8-08 | S |
| D50-01 | 50 Yield | Yield estimate | Repurposed-field design is deliberate and already documented as final | S |

---

## Summary counts (FROZEN — reconciled this session, see `docs/FINAL_GAP_REPORT.md`'s
## "FROZEN CANONICAL COUNTS" for the single authoritative source)

| Priority | Count of Missing | Count of Partial | Count of Broken | Total |
|---|---:|---:|---:|---:|
| P0 | 0 | 1 | 0 | 1 |
| P1 | 17 | 21 | 0 | 38 |
| P2 | 93 | 56 | 0 | 149 |
| P3 | 73 | 24 | 0 | 97 |
| P4 | 40 | 7 | 0 | 47 |
| **Total (current-scope work remaining)** | **223** | **109** | **0** | **332** |

This reconciles against the four canonical group files' own current totals (A:
31M+28P=59; B: 63M+20P=83; C: 52M+24P+0=76; D: 77M+37P+0B=114; sum=332), after cluster #7's
-6 Missing (D21-07/D22-05/D23-06/D24-03/D24-06/D24-07, re-verified with no new code) and
the notification-wiring batch's -3 Missing/+1 Missing→Partial (D78-03/05/08 VERIFIED,
D78-13 PARTIAL — see `docs/FINAL_GAP_REPORT.md`).

*(Latest batches — irrigation/soil data quality cluster: D3-08/D3-09/D17-01/D24-04
PARTIAL→VERIFIED (-4 Partial, P1); D18-06 MISSING→VERIFIED (-1 Missing, P1); D18-08
MISSING→VERIFIED (-1 Missing, P3 — a small pump-failure field built alongside D18-06 in
the same migration, though itself a P3 item). Soil Testing domain foundation: D20-01
through D20-12 (12 items) MISSING→VERIFIED (-12 Missing, P1); D19-05 MISSING→VERIFIED (-1
Missing, P1); D19-03 MISSING→FUTURE (-1 Missing, removed from work count entirely — a
documented non-build decision, not a code change). A genuine production timezone bug was
also found and fixed during this batch's own testing (see D15-09's canonical entry) — the
weather-risk drought/flood rules' day-bucketing now normalizes to UTC before comparing
dates, since the DB driver can return timestamps in the session's local timezone.)*

**Full history of this session's reconciliation, starting from 391** (the original
390 — 274M/115P/1B — plus D9-03, added per the caveat resolution: FUTURE→MISSING because
its blocking premise, "no background scheduler exists," was factually false):

- **P0 (-6):** D97-12 (Broken→Verified, closed-season task-creation guard), D78-07/D78-09
  (Missing→Verified, notification code already existed), D6-07/D11-05 (Partial→Verified,
  crop-cycle concurrency guard), D68-02 (Partial→Verified, refund-amount bounds check).
  D100-14 stays PARTIAL — its two originally-cited gaps were already closed by an earlier,
  undocumented pass; the genuinely remaining gap (Redis-backed global middleware) needs
  infra this project doesn't have.
- **P1 task-management cluster (-8 Missing, net 0 Partial):** D9-03/05/06/09/10/12/16,
  D37-04, D78-01 → VERIFIED (one overdue-reminder-sweep build); D37-03 → PARTIAL
  (Missing→Partial, net zero — the independent priority-field half is VERIFIED, the
  recommendation-derived half stays blocked on unbuilt D37-01).
- **P1 account/crop-failure/crop-stage (-8 Missing):** D1-19 (self-deactivation), D10-04/
  05/06/07 (failure-reason taxonomy, code already existed), D7-01/D7-03 (optional
  LAND_PREPARATION/GERMINATING stages) all → VERIFIED; D7-07 → OUT_OF_SCOPE (documented
  decision, removed from the work count entirely).
- **P1 weather-risk cluster (-7 Missing):** D15-04 (frost), D15-08/D17-04 (flood/
  waterlogging), D15-09/D17-05 (drought), D75-01/D75-02 (disaster-tagged duplicates,
  deliberately reusing `WEATHER_ALERT` rather than a new category) all → VERIFIED.
- 391 − 6 − 8 − 8 − 7 = **361** (allowing for D9-14's separate removal as a duplicate row,
  never counted in this table to begin with — see the caveat resolutions above), matching
  the independent per-group-file recount.

(D9-11 and D35-06 were also resolved this session but neither was ever
Missing/Partial/Broken, so neither affects this table.)
