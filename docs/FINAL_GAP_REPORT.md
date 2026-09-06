# Final Gap Report

Reconciles against `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md`. Full per-row evidence is in
`docs/audit/c01_foundation.md` through `c13_governance_farmbrain_security.md`, superseded
row-by-row by `docs/audit/FINAL_CANONICAL_group_{A,B,C,D}.md` (the current authoritative
source — see the frozen counts below).

## FROZEN CANONICAL COUNTS (authoritative — supersedes every count below and in
## `FINAL_100_DOMAIN_SCENARIO_MATRIX.md`/`FINAL_RELEASE_READINESS.md`/`FINAL_IMPLEMENTATION_PLAN.md`)

Independently re-counted this session directly from the four `FINAL_CANONICAL_group_*.md`
files (not taken on faith from any prior summary table), after resolving every flagged
inconsistency:

| Category | Count |
|---|---:|
| Verified | 352 |
| Implemented | 73 |
| **Attended (Verified + Implemented)** | **425** |
| Partial | 97 |
| Missing | 215 |
| Broken | 0 |
| **Current-scope work remaining (Partial + Missing + Broken)** | **312** |
| Future | 30 |
| Out of Scope | 25 |
| Environment Dependent | 6 |
| **TOTAL** | **798** |

(Verified rose from 278→323 and Missing fell from 273→233 this session, across: the P0 fix
batch (D6-07/D11-05/D68-02 PARTIAL→VERIFIED); the P1 task-management cluster (D9-03/05/
06/09/10/12/16, D37-04, D78-01 → VERIFIED; D37-03 → PARTIAL); D1-19 (account
deactivation); the crop-failure reason taxonomy (D10-04/05/06/07); the crop-stage
additions (D7-01/D7-03 VERIFIED, D7-07 OUT_OF_SCOPE — hence Out of Scope 24→25); the
weather-risk safety-detection cluster (D15-04 frost, D15-08/D17-04 flood/waterlogging,
D15-09/D17-05 drought, D75-01/D75-02 disaster-tagged duplicates — this batch also caught
and fixed a genuine production timezone bug, see D15-09's entry); the irrigation/soil
data-quality cluster (D3-08/D3-09/D17-01/D24-04 VERIFIED, D18-06/D18-08 new
`IrrigationRecord` model VERIFIED); and the Soil Testing domain foundation (D20-01 through
D20-12 VERIFIED — an entirely new domain built from zero code; D19-05 VERIFIED; D19-03
reclassified FUTURE, hence Future 29→30). See `docs/FINAL_IMPLEMENTATION_PLAN.md`'s
Summary counts section for the itemized before/after of each.)

(This continuation session, after the above was committed: cluster #7 re-verification —
D21-07/D22-05/D23-06/D24-03/D24-06/D24-07 MISSING→VERIFIED, +6/-6, no new code. Direct
re-read of `input_inventory_service.py` confirmed the existing generic, category-agnostic
`record_usage`/`InputInventoryItem.unit`/`.quantity` decrement already fully satisfied all
six rows, exactly as the implementation plan's cluster #7 note suspected. Verified 323→329,
Missing 233→227, current-scope remaining 341→335. See
`docs/audit/FINAL_CANONICAL_group_A.md`'s D21-07/D22-05/D23-06/D24-03/D24-06/D24-07 entries.)

(Further, same continuation session: notification-wiring batch — D78-03 (disease),
D78-08 (dispute), D78-05 (harvest, no code needed) MISSING→VERIFIED (+3 Verified, -3
Missing); D78-13 (security/password-change) MISSING→PARTIAL (+1 Partial, -1 Missing) - the
password-change half is built and tested, the new-device-login half is genuinely not built
(no device/session fingerprinting exists anywhere in this codebase) and is disclosed, not
fabricated. Verified 329→332, Partial 108→109, Missing 227→223, current-scope remaining
335→332. Full backend suite: 765 passed, 0 failed (was 761). See
`docs/audit/FINAL_CANONICAL_group_D.md`'s D78-03/05/08/13 entries.)

(Further, same continuation session: marketplace/harvest completeness batch — D47-01
(approaching audit log/409), D64-05 (payment date), D66-03 (pending-payment timeout
sweep) PARTIAL→VERIFIED (+3 Verified, -3 Partial); D50-03 (yield/acre), D51-02 (moisture),
D51-04 (defects), D67-05 (farmer dispute response) MISSING→VERIFIED (+4 Verified, -4
Missing). D51-02/D51-04 deliberately scoped to `HarvestRecord` only, not `HarvestListing`
(disclosed scope reduction, not a hidden gap - see their own entries). Verified 332→339,
Partial 109→106, Missing 223→219, current-scope remaining 332→325. Full backend suite:
775 passed, 2 failed (`tests/test_case_sla_service.py` — pre-existing shared-test-DB
pollution flake, confirmed unrelated: neither file touched this session, and both tests
pass cleanly in isolation; not fixed in this batch, out of scope). See
`docs/audit/FINAL_CANONICAL_group_C.md`'s D47-01/D50-03/D51-02/D51-04/D64-05/D66-03/D67-05
entries.)

(Further, same continuation session: season-closure batch — D97-02/D97-03/D97-04/D97-05/
D97-06/D97-07 PARTIAL→VERIFIED (+6 Verified, -6 Partial); D97-08/D97-09 MISSING→VERIFIED
(+2 Verified, -2 Missing). New `CropCycleClosureSnapshot` table, created once by
`close_my_crop_cycle`, freezes harvest quantity/quality/status, actual cost/revenue/profit,
a disease summary, and a weather-impact summary at the moment of closure - verified frozen
against a later ledger edit. Verified 339→347, Partial 106→100, Missing 219→217,
current-scope remaining 325→317. Full backend suite: 778 passed, 0 failed (the
test_case_sla_service.py flake from the previous batch did not reproduce this run,
consistent with it being non-deterministic shared-DB pollution, not a real regression). See
`docs/audit/FINAL_CANONICAL_group_D.md`'s D97-02..09 entries.)

(Further, same continuation session: grading-engine batch — D52-02 (grading), D59-04
(quality matching) PARTIAL→VERIFIED (+2 Verified, -2 Partial); D51-03 (size) MISSING→
VERIFIED (+1 Verified, -1 Missing). New admin-authored `CropGradeOption` table (empty by
default, no fabricated per-crop grading dataset), validated at `create_listing`; D51-03
folded into the same dimension-agnostic mechanism. New `SaleOrder.quality_mismatch_warning`,
computed once at `accept_offer`, informational only. Verified 347→350, Partial 100→98,
Missing 217→216, current-scope remaining 317→314. Full backend suite: 786 passed, 0 failed.
Also independently re-verified this session: Flutter analyze (41 issues, 0 errors, matches
prior claim) and, for the first time this session, `flutter test` (263 passed, 0 failed,
confirming the previously-unverified claim). See
`docs/audit/FINAL_CANONICAL_group_C.md`'s D51-03/D52-02/D59-04 entries.)

(Further, same continuation session: D52-01 (sorting) MISSING→VERIFIED (+1 Verified, -1
Missing) - new `HarvestListing.is_sorted`/`sorting_notes`, farmer-declared only. Verified
350→351, Missing 216→215, current-scope remaining 314→313. Full backend suite: 787 passed,
0 failed. See `docs/audit/FINAL_CANONICAL_group_C.md`'s D52-01 entry.)

(Later continuation session, after an unexpected shutdown - reconstructed from git/doc
evidence, not from any prior session's claims: full backend suite re-run fresh found 1
failure, `test_security.py::test_jwt_rejects_tampered_token` - root-caused, not just
re-run-until-green. The test tampered only the JWT's last 2 base64url characters; a
5000-iteration stress test confirmed base64's final character carries 2 unused padding
bits, so ~1-in-1600 tamper attempts decoded to byte-identical signature bytes and
correctly passed verification (a real code-level defect would have been a security bug;
this was a test-design flaw, verified by direct signature-byte comparison, not assumed).
Fixed by tampering a middle signature character instead (guaranteed byte-significant);
0/5000 flakes after the fix. No scenario-status change - this is test-reliability, not a
product gap. Full suite: 787 passed, 0 failed (unchanged, confirming no regression from
the fix itself).

D78-13 (security notification) PARTIAL→VERIFIED (+1 Verified, -1 Partial): closed the
new-device-login half, previously disclosed as unbuilt because no device/session
identifier existed anywhere in this codebase. New `RefreshToken.device_id` (client-
generated per-install random id, not a hardware fingerprint - migration
`21f2c9cef22d`); `auth_service.login()` checks login history for that device_id
*before* issuing the current login's own token, and fires `NEW_DEVICE_LOGIN_ALERT`
(`SECURITY_ALERT` category) the first time only, per device, per farmer - verified by 4
new targeted tests, including that a second login from the same device never re-fires
and a genuinely new second device does. No device_id sent (older client) is honestly
skipped, never fabricated as new or known. Message body omits all device/IP detail;
`dedup_suffix` is a SHA-256 hash of device_id, never the raw client value, in the shared
`notifications` table. Mobile: new `DeviceIdentity` (per-install id via
`flutter_secure_storage`, same random-byte pattern as the existing crop-photo
`client_upload_id`, survives logout, resets only on reinstall), wired into
`AuthRepository.login()`. Verified 351→352, Partial 98→97, current-scope remaining
313→312. Full backend suite: 791 passed, 0 failed (+4 new tests, 0 regressions).
`flutter analyze` (41 issues, 0 errors, unchanged) and `flutter test` (263 passed, 0
failed, unchanged) both independently re-run. Migration verified upgrade → `alembic
check` (empty diff for this change specifically) → downgrade → re-upgrade. One
pre-existing, unrelated drift was found by the same `alembic check` and disclosed, not
fixed: `crop_cycle_closure_snapshots`'s unique constraint/index shape (from the earlier
season-closure batch) doesn't match its model declaration - out of scope for this batch,
does not affect this change's own correctness. See
`docs/audit/FINAL_CANONICAL_group_D.md`'s D78-13 entry.)

Reconciliation applied this session (see each canonical group file's own "Reconciliation
deltas applied" table for full citations):

- **D9-03** (Reminder): FUTURE → MISSING. The FUTURE citation's premise ("no background
  scheduler exists") is now false — `scheduler.py` (APScheduler) exists with 3 registered
  jobs. Merged into the Task-overdue-reminder cluster with D9-16/D78-01/D37-04.
- **D9-14** (Dependent task): removed as a row — verbatim duplicate of D8-07 ("Task
  dependencies"), already VERIFIED. Folding it rather than double-counting one finished
  feature is why the total moved from 799 to 798.
- **D9-11** (Rejection): stays OUT_OF_SCOPE, but the "questionable inferential absence"
  flag is resolved — independently re-verified by grep that `task.py` has zero
  assignee/reviewer/Role concept anywhere, consistent with the task domain's uniform
  farmer-owned-only design, not merely "hard to build."
- **D35-06** (Case SLA timeout): confirmed already correctly VERIFIED —
  `case_sla_service.py::_expire_reassign_or_escalate` implements timeout/reassignment/
  escalation, covered by `tests/test_case_sla_service.py`. No code change; no matrix change.
- **D97-12** (new finding, closed-season task-creation guard): BROKEN → VERIFIED. Fixed in
  `task_service.py::create_task` (added the same `_TERMINAL_CULTIVATION_STATUSES` guard its
  siblings `complete_task`/`cancel_all_pending_for_crop_cycle` already had) and covered by
  2 new tests in `test_tasks.py`.
- **D78-07** (Payment notification): MISSING → VERIFIED. `payment_service._notify_payment_failed`
  already fired the required notification; added `test_payments.py::test_payment_failure_notifies_the_farmer`
  to close the "code exists, no test" gap.
- **D78-09** (Stock notification): MISSING → VERIFIED. `input_inventory_service._check_low_stock`
  already fired the required notification, already covered by an existing passing test
  (`test_low_stock_alert_fires_once_then_stays_quiet_until_restocked`) — no code or test
  change needed, only the status label was stale.
- **D6-07 / D11-05** (Multiple cycles / Old cycle closure, the identical underlying gap):
  PARTIAL → VERIFIED. Added `crop_cycle_repository.count_active_for_plot` and a guard in
  `create_crop_cycle` rejecting a second non-terminal `CropCycle` on one plot (409),
  ordered after the resowing-specific validation so a legitimate re-sow's own 422 still
  fires first. 2 new tests in `test_crop_cycles.py`.
- **D68-02** (Adjustment architecture / refund bounds): PARTIAL → VERIFIED.
  `dispute_service.resolve_dispute` now rejects a non-positive `refund_amount` or one
  exceeding `order.final_amount`. 1 new test in `test_orders.py`.
- **D100-14** (Rate limiting): re-verified PARTIAL, no code change needed. Direct re-read
  found `InMemoryRateLimiter` already wired into login/OTP-request/reset-password **and**
  photo upload (each with a passing test) — the specific gap this row's citation named was
  already closed by an earlier, undocumented pass. The genuinely remaining gap (global ASGI
  middleware, Redis-backed multi-instance safety) needs infra this project doesn't have.

The per-category counts and per-row citations immediately below (the pre-existing "798"
table and the 9-row resolution table) are the state **before** this session's
reconciliation pass and are kept for history/traceability only — do not treat them as
current. The FROZEN CANONICAL COUNTS table above is the one authoritative number set.

## Category counts (historical — see FROZEN CANONICAL COUNTS above for the current numbers)

| Category | Count | Details |
|---|---:|---|
| Complete | — | Not used as a distinct bucket (per the audit's own methodology — VERIFIED is used instead, to avoid double-counting "complete") |
| Implemented | 69 | Code fully covers the scenario, no test specifically asserts it |
| Verified | 271 | Code fully covers the scenario AND a passing automated/live test specifically asserts it |
| Partial | 113 (or 114, see disclosed ±1) | Only part of the required workflow exists — every row individually cited in the 13 cluster files |
| Missing | 284 | Required functionality doesn't exist — every row individually cited |
| Broken | 0 | All 12 originally-disclosed BROKEN rows independently re-verified as fixed this session (see matrix Section A) |
| Future | 30 | Explicitly, deliberately deferred, with a citation to where the project already documented that decision |
| Out of Scope | 25 | Requires a real external business/legal/regulated relationship this project structurally never fabricates |
| Environment Dependent | 6 | Code correct/complete; real-world behavior depends on something this dev machine/session lacks |
| **TOTAL** | **798** | |

## Zero-BROKEN verification (this session's direct contribution)

Every one of the 12 originally-disclosed BROKEN rows was re-checked against **current
code**, not re-trusted from prior documentation:

- D1-18 (password reset) — Twilio OTP gate confirmed present.
- D49-05, D50-07 (harvest status regression) — guard confirmed present, test passing.
- D57-07, D58-06 (fake net realization) — `charges` confirmed to be a real farmer-entered
  value now (reclassified BROKEN→PARTIAL, not VERIFIED — see below).
- D59-06 (offer expiry dead code) — `valid_until` check confirmed present, test passing.
- D66-02 (payment retry blocked) — transition guard confirmed present, test passing.
- D84-02 (foreground-upload auth-expiry inconsistency) — 401 check confirmed present in
  both paths.
- D84-04, D87-04, D87-05, D87-06 (dead-letter items unrecoverable) — `needsManualAction`
  revival path confirmed present.

**Result: 0 current-scope BROKEN scenarios remain.**

## Unjustified-Partial audit (why 284 MISSING + 113 PARTIAL is not a hidden pile)

The user's zero-gap rule requires every non-trivial gap to carry an explicit
Future/Out-of-Scope/Environment-Dependent justification, or be flagged honestly if it
doesn't. The 13 cluster audits already did this per-row (every MISSING/PARTIAL cell in
`docs/audit/` carries a citation and reasoning, not a bare label) — re-asserting all 397
rows' reasoning here would be pure duplication. What this report previously added was the
**honest subset the source audit itself flagged as NOT cleanly justified** — i.e., MISSING
items where the audit explicitly wrote "no explicit deferral documented" rather than
pointing to a real FUTURE/OUT_OF_SCOPE decision. That subset has now been resolved, one way
or another, per row:

| Scenario ID | Scenario | Resolution |
|---|---|---|
| D8-07 | Task dependencies | **Decided in scope, VERIFIED.** `Task.depends_on_task_id` (self-referential FK), validated same-crop-cycle at creation (`task_service._validate_dependency`); `complete_task` blocks completion until the dependency is COMPLETED. Tests: `test_tasks.py::test_task_dependency_*` (3). |
| D8-08 | Recurring tasks | **Decided in scope, VERIFIED.** `Task.repeat_interval_days`; completing a task with it set auto-creates the next occurrence (plain due-date offset, never a cron/calendar rule) — skipped once the crop cycle is no longer active. Tests: `test_tasks.py::test_completing_a_re*` (3). |
| D16-11 | Post-event weather inspection prompt | **Decided: reuse only, IMPLEMENTED (copy-only, no dedicated test).** No new entity, no auto-created task. The existing `crop_weather_heavy_rain` alert (already fires per active crop cycle after heavy rain) now also suggests photographing visible damage via the existing crop-photo flow. |
| D20-14 | Soil-linked crop recommendation | **Reclassified FUTURE.** Structurally blocked on the entire Soil Testing domain (D20-01, 14/14 MISSING) being built first — attempting this without that foundation would mean fabricating soil data. Moved to the Future(30) count below. |
| D21-01 | Seed requirement calculator | **Reclassified FUTURE.** Requires an authoritative per-crop seeding-rate reference dataset; inventing one would violate this project's own no-fabricated-agronomic-data rule. Moved to the Future(30) count below. |
| D72-04/05/06 | Cost/Revenue/Profit per acre | **Decided in scope, VERIFIED.** `CropFinancialSummaryResponse.{cost,revenue,profit_loss}_per_acre`, computed from `Plot.area_sqm` via `area_units.from_square_meters`; `None` (never a fabricated 0) when the plot can't be resolved. Test: `test_crop_financials.py::test_per_acre_financials_scale_with_actual_plot_area`. |
| D89-08 | Historical reproducibility of a past rule decision | **Partially resolved, VERIFIED for the partial.** `Notification.rule_version` is now populated (`weather_alert_rules.RULE_VERSION`) for every weather-alert-rule-triggered notification — mirrors D88-07's `crop_risk_v1` precedent (test: `test_proactive_weather_sweep.py`). A full versioned/dated threshold snapshot (the complete D89-01/02 rule-versioning system) remains genuinely FUTURE work; this closes the "undecided" label, not the underlying PARTIAL. |
| D94-08 | "What changed since last visit" aggregator | **Decided in scope, VERIFIED.** `FarmerProfile.last_daily_summary_snapshot`/`last_daily_summary_at` store the raw facts behind the last daily-summary fetch; `get_daily_summary` diffs against it and surfaces a count-based "N updates since your last visit" line — no new events table. Test: `test_assistant_chat.py::test_daily_summary_flags_what_changed_since_last_visit`. |
| D97-10 | Lessons-learned free text at season closure | **Decided in scope, VERIFIED.** `CropCycle.lessons_learned`, settable only via `CropCycleCloseRequest` at `close_my_crop_cycle` — never editable afterward. Tests: `test_crop_cycles.py::test_close_crop_cycle_*lessons_learned*` (2). |

**None of these are hidden or force-labeled** — the two genuinely large/data-fabrication-risk
items (D20-14, D21-01) were honestly deferred to FUTURE with a stated blocking reason, same
discipline as every other FUTURE row in this project; the other seven were small enough to
resolve and cover with passing tests directly this session (10 new tests, full 702-test
backend suite re-run clean — see `docs/FINAL_RELEASE_READINESS.md`).

Two borderline rows worth noting explicitly rather than silently folding into the above:

- **D44-13 (Transporter role)** — `Role.TRANSPORTER` exists as vocabulary only; a design
  comment in `delivery_service.py` says delivery "may later be handed to a distinct
  transporter role," which is a real but informal signal, not a committed roadmap item.
  Kept as MISSING rather than FUTURE per the same "no explicit deferral" discipline.
- **D60-01 (eNAM registration boundary)** and **D61-01 (FPO membership)** — correctly
  OUT_OF_SCOPE per the checklist's own rule (real external legal/business relationships
  this project structurally never fabricates), even though no document names eNAM/FPO by
  name specifically — the *general* "no fabricated integrations" rule applies even without
  a domain-specific citation.

## Everything else in the 284 MISSING / 113 PARTIAL is individually justified in-line

The remaining ~275 MISSING and ~104 PARTIAL rows each carry their own citation in
`docs/audit/c0*.md` — most fall into one of these honest, evidence-backed patterns:

- **Entire domains never attempted, confirmed by exhaustive grep, not assumed**: Government
  Schemes (73), Crop Insurance claim/settlement (74), Satellite (76), IoT (77),
  Machinery (45), Labour (46), Community (43), Education content (42), live Mandi/eNAM
  price feed (56/57/60), FPO (61) — each confirmed absent by direct search across
  `backend/app` and `mobile/lib`, with the search terms and zero-hit result stated per row.
- **Deliberate safety/anti-fabrication boundaries**: no AI-suggested treatment/dosage
  (D27-06), no automatic chemical purchase (D23-09), no auto-generated agronomic tasks
  (D8-02/D9-01), no fabricated yield formula (D50-01 uses a repurposed quantity field, not
  invented), no fabricated ROI/attribution (D72-02/03).
- **Real structural gaps disclosed by the project's own code/docs before this audit ever
  ran**: no scheduler existed before the P0 batch (now fixed for the workflows that needed
  it); Pest is not modeled as distinct from Disease anywhere (D28-*); Plot/Farm/Season-level
  financial rollups don't exist despite the data being available to join (D71-05/06/07).

## Environment Dependent (6) — what was verified locally vs. what depends on this machine

| Scenario | What's verified locally | What depends on the environment |
|---|---|---|
| D14-01, D14-03, D14-04, D14-05, D14-06, D14-08 | Provider abstraction, caching, staleness fallback, honest `available:false` handling — all VERIFIED by test | Whether the live Open-Meteo API is actually reachable from a given deployment network |

(AI diagnosis accuracy and Telugu/regional TTS voice availability are handled as FUTURE/
disclosed-limitation rather than Environment Dependent, since no trained model is
configured at all in any environment yet, and TTS voice packs are an OS-level concern
already handled by honest `voice unavailable` reporting rather than silent failure.)
