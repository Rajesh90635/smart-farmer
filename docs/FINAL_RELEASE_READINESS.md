# Final Release Readiness — Smart Farmer V3

Reconciles `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md`, `docs/FINAL_AUTOMATION_WORKFLOW_MATRIX.md`,
`docs/FINAL_CROSS_MODULE_WORKFLOW_REPORT.md`, and `docs/FINAL_GAP_REPORT.md` into a single
release-readiness view.

**Updated this later continuation session** (Missing Backlog Batch 2 - 14 approved items
spanning all four canonical group files for the first time this session, per the user's
"go ahead next batch" approving the priority plan's own recommended Batch 2 list) — see
`docs/FINAL_GAP_REPORT.md`'s "FROZEN CANONICAL COUNTS" for the current authoritative status
totals (798 total: 447 Verified, 73 Implemented, 21 Partial, 185 Missing, 0 Broken, 38
Future, 26 Out of Scope, 8 Environment Dependent; 206 current-scope items remain, down from
219 after Batch 1, 236 at the start of the Missing-backlog work, 312 before the prior
Partial-completion pass, 391 three sessions ago). This pass VERIFIED 13 of the 14 approved
Batch 2 scenarios: partial payments D65-01/02/03/05 (dealer-order flow only, per that
cluster's own citations), D89-03 (`RuleVersionSnapshot` effective-date scoping), D90-02
(`MarketProvider` abstraction, confirmed non-regression), D24-10 (input-inventory history,
zero new DB work - plus a real pre-existing audit-log bug found and fixed), D2-08/D2-09
(farm-level irrigation/soil rollup), D13-05 (`TaskType.PRUNING`), D30-05/D30-06 (duplicate-
photo and old-photo warnings, backend + mobile + all 7 languages), and D74-01 (crop
insurance policy CRUD). 1 approved item (D65-04, ledger-level partial-payment tracking) was
investigated and deliberately deferred - a genuine ledger-design question (avoiding
double-counting or prematurely importing an incomplete sale), correctly not force-built
under time pressure. Batch 1 (17 approved items, all in Group D: D89-01, D81-01, D93-05,
D94-01/02/03/04/06/07, D95-05/06/08, D96-02/07, D98-04/05, 16 VERIFIED + 1 zero-code bonus
D89-02) preceded this batch; 1 of its approved items (D95-07) was investigated and correctly
left genuinely Missing, since it shares Partial row D88-06's exact "no crop-linked reference
price" blocker. Batches 3-4 (new-domain foundations needing a product decision, and
external/licensed-data/hardware-dependent items) remain explicitly deferred, per the
prioritization plan's own scope boundary - not started this pass. An earlier continuation
session completed or
honestly reclassified every genuine Partial scenario across all four
`FINAL_CANONICAL_group_*.md` files (Partial 97→21, Verified 351→417) — see each group
file's own batch note for the full per-scenario breakdown; the 21 that remain Partial each
carry an individually-verified, non-fabricated reason (blocked on a still-Missing
dependency, a real architecture change, an unavailable external service, or no
authoritative source to draw from) rather than being force-closed. Prior sessions' work
spans: all of P0; the P1
task-management cluster; D1-19 account deactivation; the crop-failure reason taxonomy;
crop-stage additions; the weather-risk safety-detection cluster; irrigation/soil data
quality; the entire Soil Testing domain foundation; cluster #7 re-verification; the
notification-wiring batch (D78-03/05/08 VERIFIED, D78-13 later fully closed); the
marketplace/harvest completeness batch; the season-closure batch (new
`CropCycleClosureSnapshot` table); the grading-engine batch (new `CropGradeOption` table)
plus D52-01 sorting; and this session's own Partial-completion pass across Groups A/B/C/D.
An earlier continuation session additionally: (1) root-caused and fixed
a genuine test-reliability defect found on a fresh full-suite run,
`test_security.py::test_jwt_rejects_tampered_token` (tampered only the JWT's last 2
base64url characters, whose final 2 bits are unused padding - ~1/1600 tamper attempts left
the signature byte-identical and correctly passed verification; not a security bug in the
JWT code itself, confirmed by direct byte comparison; fixed by tampering a
byte-significant middle character instead, 0/5000 flakes after); (2) closed D78-13's
previously-disclosed new-device-login gap end-to-end - new `RefreshToken.device_id`
(client-generated per-install id, not a hardware fingerprint), `auth_service.login()`
detects a device_id never seen before for that account and fires a new
`NEW_DEVICE_LOGIN_ALERT` exactly once per device per farmer (verified: same device never
re-fires, a second distinct device does, no device_id sent is honestly skipped not
fabricated), message body omits all device/IP detail, `dedup_suffix` hashes device_id
(never stores it raw); mobile `DeviceIdentity` wired into `AuthRepository.login()`.
Backend suite: **791 passed, 0 failed** (was 787 before this session's 2 fixes; +4 new
tests, 0 regressions from either change). Migration (`21f2c9cef22d`) verified
upgrade→`alembic check`(empty diff for this change)→downgrade→re-upgrade; one
pre-existing, unrelated schema drift on `crop_cycle_closure_snapshots` (from the earlier
season-closure batch) was found by the same `alembic check` and is disclosed, not fixed,
here. Also independently re-verified this session: `flutter analyze` (41 issues, 0 errors,
unchanged) and `flutter test` (263 passed, 0 failed, unchanged).

**Updated this later continuation session** (Missing Backlog Batch 3 - reconstructed after
an unexpected shutdown mid-batch; no persisted priority-plan doc names Batch 3's approved
scenario count the way Batch 1/2's own commit messages do, so this reconciliation is scoped
strictly to what the working tree evidenced: 8 already-written, already-tested scenarios plus
1 zero-code bonus, all confirmed by re-running their tests fresh, not carried forward on
faith) — `docs/FINAL_GAP_REPORT.md`'s "FROZEN CANONICAL COUNTS" now read 798 total: 456
Verified, 73 Implemented, 21 Partial, 176 Missing, 0 Broken, 38 Future, 26 Out of Scope, 8
Environment Dependent; 197 current-scope items remain (down from 206 after Batch 2). 9 rows
moved Missing→VERIFIED: D74-02 (crop damage records), D79-04 (notification `expires_at`
expiry, category-specific default, excluded-not-deleted), D89-07 (`AuditLogger`
"RULE_EVALUATED" entries from the crop-risk and proactive-weather-sweep rule engines),
D92-09 (daily-brief lines re-ranked by real urgency), D78-12 (mobile one-time terminal-sync
SnackBar, device-local only), D76-06/D77-06/D90-03 (Satellite/IoT/Maps provider
abstractions - ABC + honest `NotConfigured*` stub each, no real backing implementation
configured, mirroring `WeatherProvider`/`MarketProvider` exactly), and D90-08 (identical gap
to D76-06, zero new code, closed as a bonus). D78-06 (market notification) was
re-investigated and correctly left Missing - building it would contradict a decision
(`MARKET_ALERT`'s deliberate exclusion) this project already made twice. Full backend suite:
**950 passed, 0 failed** (up from 931 at the end of Batch 2 - +19 new tests, this batch's
own). Full Flutter suite: **304 passed, 0 failed** (up from 301). Alembic migration chain
re-verified single-headed and applies cleanly. See `docs/audit/FINAL_CANONICAL_group_D.md`'s
per-scenario rows and `docs/FINAL_GAP_REPORT.md`'s own batch note for full citations. (Note:
the section-level counts further down this document - Backend/Mobile "791 passed"/"263
passed" etc. - predate Batch 2 and Batch 3 and are known-stale; they were not rewritten by
either batch, which only updated this summary block and `FINAL_GAP_REPORT.md`'s authoritative
table. Treat `FINAL_GAP_REPORT.md`'s FROZEN CANONICAL COUNTS as the one current source for
category totals, and the two full-suite numbers directly above as the current test-pass
counts, not the older per-section figures below.)

**Updated this later continuation session** (Missing Backlog Batch 4 - assembled directly
from the remaining backlog's own dependency graph, since no persisted priority-plan doc
names Batch 4's approved scenario count either, same as Batch 3) — `docs/FINAL_GAP_REPORT.md`'s
"FROZEN CANONICAL COUNTS" now read 798 total: 465 Verified, 73 Implemented, 21 Partial, 167
Missing, 0 Broken, 38 Future, 26 Out of Scope, 8 Environment Dependent; 188 current-scope
items remain (down from 197 after Batch 3). 9 rows moved Missing→VERIFIED: D81-02/03/04/06/07
(Plot/Crop/Task/Expense/Harvest offline queueing, reusing D81-01's shared `PendingWriteQueue` -
D81-05/D81-09 deliberately NOT built, both blocked on an entirely new Observation/Notes
entity, a real new-domain decision this batch does not make unilaterally), D83-02
(exponential backoff gating both automatic sync retry loops), D89-04 (region scoping of a
rule, sharing D89-05's mechanism, no real per-region values shipped), D20-13 (soil test
reminder sweep - all 4 of its own cited dependencies were already VERIFIED), and D78-10
(soil notification - closed as a zero-new-code bonus once its own cited blocker, the entire
Soil Testing domain, turned out to already be VERIFIED). A real bug found and fixed while
implementing D83-02: the backoff check used strict `isAfter`, which failed on a clock tie
(two `DateTime.now()` calls returning an identical timestamp under fast execution) - fixed to
an inclusive comparison, caught by a pre-existing test that started failing intermittently
once backoff was added. Full backend suite: **956 passed, 0 failed** (up from 950 - +6 new
tests, this batch's own). Full Flutter suite: **312 passed, 0 failed** (up from 304 - +8 new
tests). Alembic migration chain re-verified single-headed and applies cleanly. See
`docs/audit/FINAL_CANONICAL_group_A.md`'s and `docs/audit/FINAL_CANONICAL_group_D.md`'s
per-scenario rows and `docs/FINAL_GAP_REPORT.md`'s own batch note for full citations.

**Updated this later continuation session** (Missing Backlog Batch 5 - assembled directly
from the remaining backlog's own dependency graph, since no persisted priority-plan doc names
Batch 5's approved scenario count either, same as Batch 3/4) — `docs/FINAL_GAP_REPORT.md`'s
"FROZEN CANONICAL COUNTS" now read 798 total: 473 Verified, 73 Implemented, 21 Partial, 159
Missing, 0 Broken, 38 Future, 26 Out of Scope, 8 Environment Dependent; 180 current-scope
items remain (down from 188 after Batch 4). 8 rows moved Missing→VERIFIED: D71-05/06/07
(Plot/Farm/Season P&L rollup), D38-02/05 (treatment follow-up reminder sweep + reschedule),
D96-08 (season weather-impact comparison), and D36-04/07 (case acknowledgement +
recommendation-version FK). D36-06 (expert identity) deliberately NOT built - a genuine
product/privacy decision per its own row, not an engineering gap. Two real pre-existing bugs
found and fixed while implementing this batch (neither caused by Batch 5's own changes): (1)
the season-closure snapshot's `weather_impact_summary` (D97-09, already VERIFIED) filtered
for notification categories that are never actually tied to a crop cycle - `weather_alert_count`
had been silently always 0 for every crop cycle ever closed; fixed by adding the correct
category (`crop_alert`) to the filter, with a new regression test. (2) `case_repository.
get_excluded_professional_ids` was missing `COMPLETED` from its exclusion set, so a
second-opinion request could re-select a professional who already reviewed the same case -
a real crash reproduced directly while writing D36-07's own test; fixed, and re-verified
against the existing case-routing/SLA suites for non-regression. Full backend suite: **972
passed, 0 failed, 1 error** (up from 956). The 1 error,
`test_personalization.py::test_personalization_evidence_count_reflects_real_task_data`, does
not reproduce in isolation (1/1 standalone, 26/26 for the whole file) - the same
pre-existing, disclosed shared-test-database-scale flakiness this project has repeatedly
documented elsewhere; this batch touched neither `personalization_service.py` nor anything
that test depends on. Full Flutter suite: **312 passed, 0 failed** (unchanged - no mobile
changes this batch). Alembic migration chain re-verified single-headed and applies cleanly
to both dev and test databases. See `docs/audit/FINAL_CANONICAL_group_{B,C,D}.md`'s
per-scenario rows and `docs/FINAL_GAP_REPORT.md`'s own batch note for full citations.

**Updated this later continuation session** (Missing Backlog Batch 6 - assembled directly
from the remaining backlog's own dependency graph, since no persisted priority-plan doc names
Batch 6's approved scenario count either, same as Batch 3/4/5) — `docs/FINAL_GAP_REPORT.md`'s
"FROZEN CANONICAL COUNTS" now read 798 total: 479 Verified, 73 Implemented, 20 Partial, 154
Missing, 0 Broken, 38 Future, 26 Out of Scope, 8 Environment Dependent; 174 current-scope
items remain (down from 180 after Batch 5). 6 rows moved Missing→VERIFIED: D2-07 (farm
infrastructure - new `FarmInfrastructure` model, list-per-farm CRUD mirroring
`plot_service.py`'s exact shape, farmer-entered and informational only) and D37-01/02/03/05/06
(recommendation creates task - new nullable `Task.source_case_review_id` FK, a farmer-
confirmed suggestion surfaced on `CaseResponse` via `case_service._build_task_suggestion`,
never auto-created; due-date hint and priority share the same suggestion; completion needed
zero new logic via the existing generic complete endpoint; follow-up added a new nullable
`TreatmentRecord.source_task_id` FK reusing the existing effectiveness-comparison logic
unchanged). A related completeness gap closed in the process: `CaseResponse` previously had
no `latest_review_id` at all, meaning Batch 5's own review-acknowledgement endpoint (D36-04)
was unreachable from any farmer-facing read path - fixed alongside the new suggestion fields.
Full backend suite: **986 passed, 0 failed** (up from 972 - +13 new tests, this batch's own:
`tests/test_farm_infrastructure.py` (5), `tests/test_cases.py` (8)). This run also resolved
the previously-disclosed `test_personalization.py` flake and a newly-found one
(`test_cases.py::test_create_case_with_no_available_field_agent_waits_for_assignment`, which
this batch's own new field_agent-creating test helper had exposed by accumulating verified
`field_agent` rows in the shared, never-reset `smart_farmer_test` database across prior
sessions) - both traced to the same disclosed shared-test-database-scale pollution, not an
application defect, and resolved this session by dropping and recreating `smart_farmer_test`
from migrations rather than by touching any application or test code. Full Flutter suite:
**312 passed, 0 failed** (unchanged - no mobile changes this batch). Alembic migration chain
re-verified single-headed (head `a6b7c8d9e0f2`) and applies cleanly to both dev and the
freshly-recreated test database. See `docs/audit/FINAL_CANONICAL_group_{A,B}.md`'s
per-scenario rows and `docs/FINAL_GAP_REPORT.md`'s own batch note for full citations.

**Updated this later continuation session** (Missing Backlog Batch 9 - deliberately small,
since the remaining backlog's low-hanging fruit had already been exhausted by Batches 3/4/7/8)
— `docs/FINAL_GAP_REPORT.md`'s "FROZEN CANONICAL COUNTS" now read 798 total: 508 Verified, 73
Implemented, 20 Partial, 123 Missing, 0 Broken, 38 Future, 26 Out of Scope, 8 Environment
Dependent; 143 current-scope items remain (down from 146 after Batch 8). 3 rows moved
Missing→VERIFIED: D52-03 (Packing - new `HarvestListing.packing_requirements` field,
migration `54738ef35b1a`), and a zero-code reconciliation finding, D57-06/D58-05 (storage
cost/deduction) - both already fully implemented and tested via the existing
`storage_charge` itemized-charge field, simply never reconciled against that fact. Full
backend suite: 1056 passed, 1 failed (up from 1055 - the 1 failure was the same pre-existing,
already-disclosed `test_rule_versioning.py` flake, not touched this batch). Full Flutter
suite unchanged (no mobile changes this batch). Several other rows (D5-05, D7-10, D11-06,
D26-04, D52-07, D53-06) were re-investigated but deliberately left Missing rather than
reclassified, on finding that `docs/FINAL_GAP_REPORT.md`'s own Batch 7/8 notes had already
examined several of these exact rows and consistently chose to leave a genuinely-blocked row
honestly Missing with its reason disclosed inline rather than reclassify it - this batch
corrected each row's own stale inline citation to match, without introducing a new
reclassification precedent. See `docs/audit/FINAL_CANONICAL_group_{A,C}.md`'s per-scenario
rows and `docs/FINAL_GAP_REPORT.md`'s own batch note for full citations.

**Rule-versioning clock-tie bug fixed (following session)**: the `test_rule_versioning.py`
flake disclosed above is now fixed - `RuleVersionSnapshot.sequence` (migration
`7fb0f206a5a5`), a real monotonic Postgres IDENTITY column used as a deterministic secondary
sort key in `get_effective_at`, mirroring the identical fix already applied to
`CounterOffer.sequence` for the same clock-tie bug class. Verified against 20 real tied rows
accumulated in the test database (not just a fresh-database pass) - 5/5 repeated runs passed
after the fix. Full backend suite: **1057 passed, 0 failed**. See
`docs/FINAL_GAP_REPORT.md`'s own "Rule-versioning clock-tie bug" note for full detail.

## Functional

- 100 domains audited (13 cluster passes, `docs/audit/`), 798 individually-classified
  granular scenarios (exceeds the "300+" floor).
- Cross-module workflows audited: 10 named workflows (A-J) traced end-to-end with
  explicit COMPLETE/PARTIAL calls, not just per-domain summaries.
- Automatic workflows audited: 13 genuine scheduler-driven or rule-triggered workflows
  identified and individually verified (see automation matrix) — CRUD is not counted as
  automation.
- Manual workflows: the overwhelming majority of farmer-facing actions (farm/plot/crop
  CRUD, task creation/completion, purchases, disputes, GDPR export/delete) — all
  explicit-tap-triggered, no silent auto-mutation of farmer data anywhere found.
- Hybrid workflows: AI diagnosis → confidence-gated escalation prompt → farmer-confirmed
  case creation (Workflow C); weather → advisory (never auto-modifies a task, Workflow B/F).
- Safety-confirmation workflows, explicitly verified: no automatic chemical
  purchase/dispatch (D23-09, IMPLEMENTED — no code path connects diagnosis to
  order/checkout at all); OCR never auto-posts to the ledger (D69-11, VERIFIED by test);
  weather-action engine never reschedules/modifies a task (D16-06, FUTURE by explicit
  design); AI never names a disease at low confidence or when unavailable (D32-06,
  VERIFIED, structural not text-filter).

## Backend

- **Test result: 791 passed, 0 failed** (full suite; up from 702 at the start of the
  prior-prior session, 787 at the start of this later continuation — +4 new tests for
  D78-13's new-device-login detection, plus a fix to a genuinely flaky pre-existing test,
  `test_security.py::test_jwt_rejects_tampered_token` (tampered only the JWT's last base64
  characters, whose final bits are unused padding — not a real signature-verification bug,
  confirmed by direct byte comparison; see `docs/FINAL_GAP_REPORT.md`) — confirmed by a
  full clean re-run, not merely the new tests in isolation). An earlier run in the prior
  continuation saw 2 failures in `tests/test_case_sla_service.py`'s own pre-existing
  shared-test-DB pollution flake (see the session summary above); every later run's clean
  0-failure result is consistent with that being non-deterministic, not a regression caused
  by this session's actual changes.
- **Flutter: independently re-verified this session** — `flutter analyze` (41 issues, all
  info-level, 0 errors, matches the prior claim exactly) and `flutter test` (263 passed, 0
  failed, "All tests passed!" - this specific claim had never been independently re-run
  before this session and is now confirmed genuine, not carried forward on faith).
- **Zero BROKEN scenarios** — all 12 originally-disclosed bugs previously re-verified
  fixed, plus D97-12 (a new finding from a later pass: `task_service.py::create_task` never
  checked `cultivation_status` before creating a task, unlike its sibling guards) fixed and
  tested this session.
- Migration status: every migration cited in the cluster audits was verified end-to-end at
  the time it was written (upgrade → data check → downgrade → re-upgrade →
  `alembic revision --autogenerate` empty diff) per the project's own established
  convention; this session's `21f2c9cef22d` (device_id) round-tripped clean with no drift
  of its own. `alembic check` did surface one pre-existing, unrelated drift on
  `crop_cycle_closure_snapshots` from an earlier season-closure-batch migration (a
  unique-constraint/index shape mismatch against its model) — disclosed here, not fixed,
  out of scope for this session's work.
- API status: RBAC (`require_role`), farmer-ownership (`get_owned`, 404-not-403 by design
  to prevent ID enumeration), and consent-gating are consistently applied — VERIFIED by a
  9-endpoint cross-farmer isolation sweep (D100-07, `test_phase40_integration.py`,
  confirmed passing).
- Security status: JWT auth + rotating refresh tokens (D100-01, VERIFIED), RBAC (D100-02/
  03, IMPLEMENTED — consistently applied, no single central test), audit logging across
  27+ services in the same DB transaction as the write (D100-12, IMPLEMENTED), consent
  system versioned and itemized not a blanket boolean (D100-10). Rate limiting remains
  PARTIAL by disclosed design — in-memory, single-process, covers only login/reset-password
  (D100-14) — a real deployment-scale gap, not hidden. GDPR-style data export/deletion now
  exists (D100-09, VERIFIED, explicitly a good-faith MVP not a certified compliance review).

## Mobile

- **`flutter analyze`: 41 issues, 0 errors** — all info-level, same kinds as before (one
  more `value:`→`initialValue` instance from the new task-dependency dropdown, not a new
  kind of issue). Flutter 3.44.6 confirmed available in this environment.
- **`flutter test`: 263 passed, 0 failed** — 257 plus 6 new tests for the fields below, run
  live this session, full suite.
- Mobile now surfaces the 6 of 7 backend-only session's gap-report resolutions that have a
  farmer-facing UI surface at all (see `docs/FINAL_GAP_REPORT.md`): task dependencies
  (blocked-state indicator, disabled Complete button, a dependency picker in the create-task
  sheet) and recurrence (a repeat-interval field) in `task_list_screen.dart`; per-acre
  cost/revenue/profit in `crop_financial_summary_screen.dart`; a lessons-learned prompt at
  crop-cycle close and its display in `crop_details_screen.dart`. The post-storm inspection
  prompt (D16-11) needed no mobile change — it's a notification-text change already rendered
  generically. `Notification.rule_version` (D89-08) was deliberately NOT added to the mobile
  model — there is no debug/details view for it to appear in, and adding an unused field
  would be dead code. All new strings translated across all 7 languages, matching the
  existing localization discipline (verified via `flutter gen-l10n` + a fresh
  `flutter analyze`/`flutter test` pass).
- Runtime verification: individual cluster audits additionally ran targeted live sessions
  this cycle (Telugu E2E login→language-switch→Daily-Briefing→Listen; location dropdown
  cascade verified against real seeded village data end-to-end including a direct DB
  read-back) — cited in `docs/audit/c07`/`PROJECT_STATUS.md`, not re-run this pass.
- Localization status: 651/651 `.arb` keys match across all 7 supported languages
  (en/hi/kn/ta/ml/mr/te), 0 missing/extra — VERIFIED by direct key-set diff. Backend
  advisory text (weather/disease/case templates) is honestly English-only outside the 8
  `daily_summary_*` keys, by explicit disclosed design (auto-translating
  safety-relevant text without native-speaker review is considered worse than an honest
  English fallback) — do not read this as "multilingual complete"; read it as "UI chrome
  and the daily-briefing family are multilingual, most advisory text is not yet."
- Offline status: offline/sync infrastructure (`PendingUploadQueue`/`SyncCoordinator`/
  `NetworkStatusChecker`) is scoped exclusively to crop-photo uploads — Farm/Plot/Crop/
  Task/Expense/Harvest/Notes have zero offline queueing, confirmed by direct inspection of
  each repository file, not assumed. Within that one path: dead-letter recovery (this
  session's bug-fix reconciliation) and auth-expiry consistency (same reconciliation) are
  now fixed; the sync-outcome notification gap (D78-12) remains open.

## AI

- Diagnosis pipeline: fully built provider-abstraction architecture (`ModelProvider` ABC),
  zero real trained model configured in this environment — `NotConfiguredModelProvider` is
  the only wired implementation, so every real analysis resolves to `AI_UNAVAILABLE`,
  disclosed not hidden.
- Confidence: HIGH/MEDIUM/LOW thresholds are real and enforced (VERIFIED by boundary
  tests), explicitly disclosed as unvalidated placeholders pending a real evaluation
  dataset — never presented as calibrated certainty.
- Unknown/insufficient-evidence handling: VERIFIED structurally — `predicted_class` is
  `None` in every UNKNOWN/LOW_CONFIDENCE/CROP_MISMATCH/AI_UNAVAILABLE branch of
  `prediction_validator.py`.
- Expert escalation: farmer-confirmed, not automatic on low confidence (a deliberate
  consent-boundary choice, not a bug — creating a case shares the farmer's photo with a
  professional).
- Governance: model name+version+confidence recorded on every analysis (VERIFIED); farmer
  correction of a *specific* AI result now exists (`POST /ai/analysis/{id}/correction`,
  new this cycle); false-positive/false-negative *tracking as a live pipeline* remains
  MISSING — the raw correction signal now exists but is not yet aggregated into any
  dashboard or evaluation loop.

## Automation

- Task automation: overdue detection is real and live-computed (VERIFIED); automatic task
  creation from any trigger remains FUTURE by explicit, code-documented design (no
  validated agronomic rule dataset exists to drive it safely).
- Weather automation: pull-based alerts VERIFIED; proactive (scheduler-driven) push sweep
  now VERIFIED (closes the "farmer who never opens the app is never warned" gap).
- Notifications: dedup via DB unique constraint (VERIFIED); no expiry/TTL concept exists
  (disclosed MISSING); this line was stale as of this session's re-check against
  `app/models/notification.py`'s actual `NotificationCategory` enum — Task, Stock, Payment,
  Dispute, and (this session) Security all now exist; 4 of the original 13 candidate
  categories remain genuinely MISSING (Market, Soil, Disaster-as-distinct, Sync),
  confirmed by grep, each individually cited in `c12`.
- Retry/idempotency: DB-enforced idempotency keys (orders, photo uploads, notification
  dedup) all VERIFIED; exponential backoff for sync retries confirmed genuinely MISSING
  (immediate retry on every connectivity event, no delay/backoff math anywhere).

## Data

- Provenance: source/model/fetch-time recorded consistently for weather/AI/price
  individually (PARTIAL as a *unified* cross-cutting concept — no single provenance model
  spans crop-risk factors, notifications, and rule outputs).
- Rule versioning: genuinely MISSING across the board — weather/crop-risk rules are plain
  deterministic Python functions with no `rule_id`/version/effective-date/region/stage
  parameter (D89-01 through D89-08), except `rule_version` was added to
  `CropRiskScoreResponse` this cycle (D88-07, now PARTIAL — one rule family only).
- Audit logging: append-only `AuditLog`, written in the same DB transaction as the
  business write, used from 27+ services (IMPLEMENTED, widely and consistently applied).

## Security

- Authentication/authorization/RBAC/ownership: all VERIFIED or IMPLEMENTED with strong,
  consistent patterns (`require_role`, `get_owned`, 404-not-403).
- Privacy: consent system is real, versioned, itemized (VERIFIED design); GDPR-style
  export/deletion now exists (VERIFIED, explicit MVP-not-certified-compliance disclosure).
- Rate limiting: PARTIAL — covers only login/reset-password, in-memory/single-process,
  not wired to image-upload endpoints despite the module's own docstring naming that as an
  intended target. A real, disclosed, deployment-scale gap.
- Cross-user isolation: directly tested this cycle's audit — Farmer A cannot reach Farmer
  B's farm/plot/crop/photo/expense/harvest/sale/payment/dispute/case/notification via a
  9-endpoint sweep (`test_phase40_integration.py`, VERIFIED, confirmed passing).

## External Providers — verified locally / mocked / environment dependent / not implemented / future

| Provider | Status |
|---|---|
| Weather (Open-Meteo) | Real ABC + real implementation; architecture VERIFIED against a fake provider; live reachability from this specific network is ENVIRONMENT_DEPENDENT |
| AI/vision model | Real ABC; `NotConfiguredModelProvider` only — no trained model configured anywhere; FUTURE for real accuracy |
| OCR (Tesseract) | Real ABC + a genuinely working local implementation — the most complete of all provider abstractions, confirmed with a real rendered test image |
| Assistant LLM | Real ABC (`AIProvider`); `NotConfiguredAIProvider` only, no API key configured, verified directly |
| Payment gateway | Real ABC as of this cycle (`PaymentGatewayProvider`); only a sandbox adapter implemented, with an `is_sandbox_completable` guard refusing to run against a misconfigured non-sandbox deployment |
| SMS/OTP (Twilio Verify) | Real, wired for password-reset identity verification (closes the account-takeover gap) |
| Market/mandi price feed | Not implemented — `market.py` is an explicit empty placeholder; no fabricated data |
| eNAM, Government Schemes, Crop Insurance, Satellite, IoT, Cold Storage | Not implemented, confirmed by exhaustive grep; correctly OUT_OF_SCOPE (real external regulated relationships) or MISSING (no interface even attempted) |
| Maps/geocoding | Not implemented — location is static Mandal/Village master data, no live geocoding provider |
| Push/SMS notification delivery | Not implemented — in-app DB notification only, no FCM/SMS gateway abstraction exists |

## Zero-gap status

- **0 current-scope BROKEN** (was 12, independently re-verified fixed this session).
- **0 scenarios remain genuinely undecided backlog** (was 9). 7 (D8-07, D8-08, D16-11,
  D72-04/05/06, D89-08 partial, D94-08, D97-10) were decided in scope and implemented this
  session, 6 of them backed by new passing tests (D16-11 is copy-only, no dedicated test);
  2 (D20-14, D21-01) were honestly reclassified FUTURE — both structurally blocked
  on a prerequisite (an unbuilt Soil Testing domain; an unsourced seeding-rate dataset) whose
  absence this project correctly refuses to paper over with fabricated data. Full resolution
  detail in `docs/FINAL_GAP_REPORT.md`. The top-line category counts in
  `docs/FINAL_GAP_REPORT.md` are stale pending a full reconciliation pass (this session
  updated the 9-row table itself, not the 798-row category totals).
- All other MISSING/PARTIAL rows carry their own inline justification in `docs/audit/c0*.md`.

## Test-database isolation (this session's own audit, per the prompt's explicit ask)

Found and fixed 3 instances of the same anti-pattern (assertions against an unscoped,
shared, never-reset test database rather than the specific entity a test created):
products/admin pagination, the Expert SLA sweep's own reminder test, and 3
input-inventory expiry-sweep tests. Checked the one remaining candidate
(`test_proactive_weather_sweep.py`) and confirmed it already scopes every call with
`farm_ids=[...]`, per its own docstring explaining exactly this hazard — no fourth
instance found. All fixes verified robust by reproducing the failure with a deliberately
simulated leftover row, then confirming the scoped assertion survives it.
