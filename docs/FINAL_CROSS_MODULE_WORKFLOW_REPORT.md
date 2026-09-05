# Final Cross-Module Workflow Report

Each workflow below is traced end-to-end through the real code, citing the same evidence
already gathered in `docs/audit/c0*.md` and reconciled in
`docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md`. "Complete" here means every step in the named
chain has real code and (where claimed) a passing test — a broken link is called out
explicitly, not smoothed over.

## Workflow A — New Farmer → Farm → Plot → Crop → Cycle

Registration (D1-01, VERIFIED) → login (D1-02, VERIFIED) → consent (D1-13, VERIFIED) →
farm (D2-01, VERIFIED) → plot (D3-01, VERIFIED) → crop (D4-02, VERIFIED) → variety (D5-01,
VERIFIED) → cycle (D6-01, VERIFIED) → sowing (D6-02, VERIFIED) → stage (D6-06, VERIFIED) →
tasks (D9-01, farmer-created only — FUTURE for auto-generation, working manually) →
notifications (in-app only, no push at any step).

**Status: COMPLETE for every manual step.** The one honest gap in this chain is
auto-generated tasks from sowing/stage (D8-02/D8-05, deliberately FUTURE — no validated
agronomic rule dataset exists to drive it, and the project's own `task.py` docstring
states this explicitly rather than inventing agronomy).

## Workflow B — Crop → Weather → Risk → Task

Weather (D14-01, ENVIRONMENT_DEPENDENT on live Open-Meteo reachability — architecture and
fallback VERIFIED) → plot/crop/stage (weather is farm-level only, not per-plot; D16-01
PARTIAL) → sensitivity (D16-03, PARTIAL — only one heavy-rain rule considers crop/stage,
and only for message wording) → risk (D16-04, VERIFIED) → task: **broken link** — weather
never creates, modifies, or postpones a task (D16-05/06/07, FUTURE, explicitly documented:
"never automatically rescheduled or modified"). A weather advisory is attached to an
existing pending SPRAYING task's API response only (D8-06, PARTIAL) → notification
(VERIFIED, see automation matrix) → farmer action (manual).

**Status: PARTIAL by design.** The chain is deliberately advisory-only past the risk step —
this is a documented safety/anti-fabrication choice (no validated rule exists to safely
auto-modify a task), not an oversight.

## Workflow C — Photo → AI → Confidence → Expert

Photo (D27-03, VERIFIED) → quality check (D30-01/02, VERIFIED for blur/lighting; D30-03/04
PARTIAL for framing/plant-part — guidance-only) → AI diagnosis (D27-04/D29-04, VERIFIED for
pipeline; ENVIRONMENT_DEPENDENT/FUTURE for real accuracy — `NotConfiguredModelProvider` is
the only wired implementation, so every real analysis in this environment resolves to
`AI_UNAVAILABLE`, disclosed not hidden) → confidence (D31-01/02/03, VERIFIED) →
unknown/low-confidence handling (D32-01/02, VERIFIED — never invents a diagnosis) → expert
escalation: **farmer-confirmed, not automatic** (D31-05/D32-05, PARTIAL-by-design — creating
a case shares the farmer's photo with a professional, and this project's `CaseConsent` rule
means that requires explicit farmer action; the farmer IS proactively prompted) →
assignment (D33-02/03, VERIFIED) → SLA (D35-*, VERIFIED) → recommendation (D36-01, VERIFIED
— no medicine/dosage field exists, by design) → farmer acknowledgement: **gap** — no
acknowledge/read-receipt endpoint exists (D36-04, MISSING; `ProfessionalFeedback` is a
rating survey, not an acknowledgement).

**Status: COMPLETE through recommendation; the final acknowledgement step is genuinely
missing.**

## Workflow D — Expert Recommendation → Task → Follow-up

**Broken link at the first step**: no code path connects a `CaseReview` outcome to `Task`
creation at all (D37-01, MISSING, explicitly deferred — `Task` has no `case_id`/
`treatment_id` FK). The *separate*, farmer-initiated Treatment/Follow-up system covers an
analogous but architecturally distinct chain: treatment recorded (D38-*, VERIFIED) →
follow-up observation (D38-03, VERIFIED) → outcome (D39-04/05/06, VERIFIED, exactly 4
non-fabricated outcomes) → reinspection (D39-01/02, VERIFIED, reuses the existing
photo/analyze pipeline, no second AI call invented) → escalation on worsening (D38-06/
D39-07, VERIFIED as of the P0 batch).

**Status: the checklist's literal chain (Recommendation→Task) does not exist; the
functionally-equivalent Treatment→Follow-up→Reinspection→Escalation chain is real,
VERIFIED, and parallel to it — a farmer just cannot get there starting from an expert's
own review.**

## Workflow E — Disease → Treatment → Input → Inventory

Disease (D27-04, VERIFIED/ENV_DEPENDENT) → recommendation: **structurally absent** —
`docs/DISEASE_MODEL.md`/`treatment_record.py` deliberately exclude a "what to apply"
suggestion (D27-06, FUTURE, explicit safety exclusion — the system records only what a
farmer actually applied, never suggests what to apply) → farmer confirmation (implicit,
since nothing is ever suggested to confirm) → input purchase (D25-05, VERIFIED, explicit
two-tap add-to-cart→checkout) → inventory (D24-01, VERIFIED as of batch 3) → usage
(D24-06, VERIFIED) → remaining stock (D24-07, VERIFIED) → expiry/low-stock alert (D24-08/09,
VERIFIED as of batch 3).

**Status: COMPLETE from input-purchase onward; the Disease→Treatment "recommendation"
link is a deliberate, disclosed safety boundary, not a gap — the project's own
`docs/PRODUCT_SAFETY.md` states the system must never independently prescribe a
fertilizer/pesticide/dosage, and it structurally doesn't (no code path connects
diagnosis data to order/checkout at all, D23-09, IMPLEMENTED).**

## Workflow F — Weather → Irrigation

Rain forecast (D14-01, ENV_DEPENDENT) → crop water requirement: **absent** — no rule
computes an actual water requirement (D17-02, MISSING) → irrigation recommendation
(D16-08/D18-09, VERIFIED — deterministic DELAY/MONITOR/IRRIGATE_NOW/NO_ACTION/UNKNOWN
mapping, `soil_moisture_available` always explicitly `False`, never fabricated) → task:
**never auto-created or modified** (D16-05/06, FUTURE) → farmer action (manual) →
irrigation record: **absent** — no `IrrigationRecord`-analog exists to log an actual
watering event (D18-06, MISSING; the project has this exact pattern for treatments but
never built an analogous one for irrigation).

**Status: PARTIAL.** The recommendation step is genuinely strong and honest about its own
limits (never claims to know real crop water need); the chain has no auto-task and no
event log at either end.

## Workflow G — Crop Failure → Re-sowing

Failure detection (D10-01, VERIFIED as of batch 4 — dedicated `report-failure` endpoint
with a real reason taxonomy, distinct from a plain "changed my mind" cancel) → farmer
confirmation (implicit in the report-failure call itself) → old cycle closure: **not
enforced** — nothing prevents a second concurrently-active cycle on the same plot before
the old one is closed (D6-07/D11-05, PARTIAL, a real double-tap/offline-replay risk) →
re-sowing recommendation (D10-09/D11-01, VERIFIED as of batch 4 — category-driven,
deliberately non-prescriptive, consistent with the project's no-fabrication convention) →
farmer confirmation (D11-02, PARTIAL — generic create-flow only, no re-sowing-aware
confirmation step) → new sowing (D11-03/04, VERIFIED) → new cycle, linked via
`resown_from_crop_cycle_id` (D10-10, VERIFIED as of batch 4) → regenerated calendar/tasks:
**does not exist** — no task is ever auto-created for a new cycle, re-sown or not
(D11-06, MISSING, same root cause as Workflow A's task gap).

**Status: COMPLETE for failure→recommendation→re-sow-and-link; the old-cycle-exclusivity
gap and the absent task regeneration are real, disclosed limitations.**

## Workflow H — Harvest → Sale → Payment → Profit

Harvest readiness (D47-01/03, VERIFIED, farmer-confirmed only, no automatic maturity
detection — D47-02, FUTURE) → harvest planning: **largely absent** (labour/machinery/
transport/storage pre-harvest planning are all MISSING, D48-*) → quantity (D49-01,
VERIFIED) → quality (D51-01, IMPLEMENTED, free-text grade by design) → sale (D52-06,
VERIFIED, full `HarvestListing`→`BuyerOffer`→`SaleOrder` lifecycle, row-locked
concurrency-safe) → order (D63-*, VERIFIED, 16-state transition map) → payment (D64-01/02/03,
VERIFIED, sandbox-only by disclosed design; retry now works, see zero-BROKEN
reconciliation) → expense (D69-01, VERIFIED) → revenue (D70-01, VERIFIED, idempotent sale
import) → profit (D71-01/03, VERIFIED, honest NULL-handling where no real yield/price
dataset exists) → ROI (D72-01, IMPLEMENTED; D72-02/03, FUTURE — explicitly, deliberately
`Literal[None]` since `Order` has no `crop_cycle_id` to attribute spend to revenue) →
season closure (D97-11, VERIFIED for the status-transition itself; D97-02 through D97-10
mostly PARTIAL/MISSING — quantity/quality/sale/revenue/costs/profit are all captured
elsewhere live, never consolidated into a single closure snapshot).

**Status: COMPLETE and thoroughly tested from harvest through profit; harvest *planning*
(pre-harvest) and season-closure *snapshotting* are the two genuine structural gaps, both
disclosed per-row in `c08`/`c13`.**

## Workflow I — Offline Photo

Offline capture → local persistence (`PendingUploadQueue`, on-disk JSON manifest,
survives app kill/restart, D82-01/D84-05, VERIFIED) → queue (D82-01, VERIFIED) → reconnect
(`NetworkStatusChecker`, D82-04, IMPLEMENTED) → upload (D82-02, IMPLEMENTED) → server
acknowledgement (D82-05, IMPLEMENTED) → local state reconciliation (`remove()` on success,
IMPLEMENTED) → AI processing (same as Workflow C from here) → diagnosis → notification:
**this specific leg is a genuine gap** — no notification is ever sent when a queued photo
finishes syncing or fails (D78-12, MISSING; a farmer has no way to be told "your queued
photo synced" other than reopening the photo screen).

**Status: COMPLETE for the offline→sync mechanics themselves (the single strongest offline
path in the app); the sync-outcome notification at the very end of the chain does not
exist. This is also the ONLY entity with any offline path at all — Farm/Plot/Crop/Task/
Expense/Harvest/Notes have zero offline queueing (D81-01 through D81-09, MISSING, confirmed
by direct code inspection of each repository file, not assumed from the absence of a
queue-named file).**

## Workflow J — Auth Expiry During Sync

Queued data (D82-01, VERIFIED) → token expires → sync fails authentication: now correctly
detected in BOTH the background sync path (pre-existing) and the foreground manual-upload
path (D84-02, fixed this session's reconciliation — was BROKEN, an inconsistency between
the two paths) → queue preserved (D84-05, VERIFIED, `authenticationRequired` items are
never lost, just stuck) → reauthentication → retry: previously **BROKEN** (D84-04/D87-04/
05/06 — no code path ever revived a stuck item, despite a code comment promising a UI path
that didn't exist) → **now fixed** (`pending_upload_queue.dart`'s `needsManualAction`
exposes a real revival path, per this session's reconciliation of the original 7 disclosed
bugs) → successful sync → no duplicate (idempotent via `(session_id, client_upload_id)`
unique constraint, D86-01, VERIFIED).

**Status: COMPLETE end-to-end as of this session's bug reconciliation** — this was the
single most-broken cross-module chain in the original audit (3 of the 7 disclosed BROKEN
bugs sat on exactly this path) and is now closed.

---

## Summary across all 10 workflows

| Workflow | End-to-end status |
|---|---|
| A. New Farmer → Cycle | COMPLETE (manual steps); task auto-generation FUTURE by design |
| B. Weather → Risk → Task | PARTIAL by design (advisory-only past risk, deliberate safety choice) |
| C. Photo → AI → Expert | COMPLETE through recommendation; farmer acknowledgement MISSING |
| D. Recommendation → Task | Literal chain MISSING; parallel Treatment→Follow-up chain COMPLETE |
| E. Disease → Input → Inventory | COMPLETE from purchase onward; "recommendation" step is a deliberate safety boundary, not a gap |
| F. Weather → Irrigation | PARTIAL (recommendation strong and honest; no auto-task, no event log) |
| G. Crop Failure → Re-sowing | COMPLETE for failure→recommendation→link; exclusivity + task-regeneration gaps disclosed |
| H. Harvest → Sale → Profit | COMPLETE and best-tested chain in the app; pre-harvest planning and closure-snapshotting are the real gaps |
| I. Offline Photo | COMPLETE for sync mechanics; sync-outcome notification MISSING; only entity with any offline support |
| J. Auth Expiry During Sync | COMPLETE as of this session (previously the most-broken chain — 3 of 7 disclosed bugs) |
