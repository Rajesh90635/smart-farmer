# Final Gap Report

Reconciles against `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md`. Full per-row evidence is in
`docs/audit/c01_foundation.md` through `c13_governance_farmbrain_security.md`.

## Category counts (reconciles to 798)

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

**Stale pending reconciliation:** the 9-row resolution below (7 IMPLEMENTED, 2 reclassified
FUTURE) moves rows out of the 284 MISSING count into Implemented/Future, and D89-08 out of
the 113 PARTIAL count. The table above is left as last independently verified rather than
hand-adjusted here, to avoid guessing a new total without re-running the full 798-row
reconciliation this session did not repeat.

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
