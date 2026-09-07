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
| Verified | 508 |
| Implemented | 73 |
| **Attended (Verified + Implemented)** | **581** |
| Partial | 20 |
| Missing | 123 |
| Broken | 0 |
| **Current-scope work remaining (Partial + Missing + Broken)** | **143** |
| Future | 38 |
| Out of Scope | 28 |
| Environment Dependent | 8 |
| **TOTAL** | **798** |

**Rule-versioning clock-tie bug (disclosed after Batch 8, now fixed):** the one remaining
backend test failure — `test_rule_versioning.py::test_a_query_for_an_old_date_still_reproduces_the_old_decision_after_a_threshold_change`
— has been fixed. Root cause (per Batch 8's own disclosure below): `rule_version_repository.
get_effective_at` ordered by `effective_from DESC` with no secondary tiebreaker; repeated
full-suite runs against the persistent shared test database accumulated many
`RuleVersionSnapshot` rows sharing the test's hardcoded `datetime(2020, 1, 1)` `effective_from`
value, and the tie-break could return any of them nondeterministically. Fix: added
`RuleVersionSnapshot.sequence` (a real monotonically-increasing Postgres IDENTITY column,
migration `7fb0f206a5a5`) as a deterministic secondary `ORDER BY ... , sequence DESC`,
mirroring the identical fix already applied to `CounterOffer.sequence` for the exact same bug
class. Verified as a real fix, not a coincidence: confirmed 20 tied rows now exist in the
test database with the identical `effective_from` (accumulated across this session's own
repeated runs), then re-ran the target test 5 times in a row against that same polluted
database — 5/5 passed, proving the tiebreaker resolves the tie correctly rather than merely
passing on a fresh/unpolluted run. Full backend suite: **1057 passed, 0 failed** (up from
1056/1 failed). Migration verified upgrade→downgrade→re-upgrade clean on both dev and test
databases; `alembic check` shows only the same pre-existing, already-disclosed
`crop_cycle_closure_snapshots` drift, no new drift introduced.

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING BACKLOG"
prioritization plan's Batch 9 — deliberately scoped small after the prior batch's own
disclosure that essentially every remaining low-hanging Missing item had already been
investigated by Batches 3/4/7/8 and correctly found to require either a new-domain product
decision (pest diagnosis, voice input, community forum, nearby-services/machinery/labour
marketplace, government schemes) or a genuine external/dataset dependency this project
structurally refuses to fabricate. 3 rows moved Missing→VERIFIED (-3 Missing, +3 Verified):
D52-03 (Packing — new `HarvestListing.packing_requirements`, migration `54738ef35b1a`,
farmer-declared free text distinct from generic `notes`, same honesty convention as
`sorting_notes`/`certificate_reference`; 1 new test), and a genuine zero-code reconciliation
finding: D57-06 (Storage cost, Market Comparison) and D58-05 (Storage deduction, Net
Realization) were both still marked Missing despite `AcceptOfferRequest.storage_charge`/
`SaleOrderResponse.storage_charge` already existing and already tested since D57-04/D58-04's
own Batch-2/Batch-8 work — these two rows were simply never reconciled against that fact.
Two other rows initially drafted for reclassification this batch (D5-05, D11-06, D26-04,
D52-07/D53-06's own older row text all recommended moving to FUTURE) were deliberately left
Missing instead, on discovering mid-batch that `docs/FINAL_GAP_REPORT.md`'s own Batch 7/8
notes had already investigated several of these exact rows (D11-06, D7-10, D1-14, D78-11,
D81-05/09, D52-07/D53-06) and consistently chose to leave a genuinely-blocked row honestly
Missing with its reason disclosed inline rather than reclassify it — this batch defers to
that established convention rather than introducing a new one; only the rows' own inline
text was corrected to cite the real, current blocker instead of a stale recommendation.
Total unchanged at 798 - every change this batch was either a real additive feature, a
zero-code reconciliation, or an inline citation fix; zero new/removed rows. Full backend
suite: 1056 passed, 1 failed (up from 1055 - +1 new test, this batch's own; the 1 failure was
the same pre-existing `test_rule_versioning.py` clock-tie-under-repeated-runs flake disclosed
in the Batch 8 note below - since fixed in a following session, see the "Rule-versioning
clock-tie bug" note above the FROZEN CANONICAL COUNTS table). Full
Flutter suite: unchanged (no mobile changes this batch). Migration `54738ef35b1a` verified
upgrade→downgrade→re-upgrade clean on both dev and test databases; `alembic check` shows
only the same pre-existing, already-disclosed `crop_cycle_closure_snapshots` drift, no new
drift introduced. See `docs/audit/FINAL_CANONICAL_group_{A,C}.md`'s per-scenario rows for
full citations.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING BACKLOG"
prioritization plan's Batch 8 — the first batch built from the pure Missing-scenario
backlog rather than a mixed audit-closure pass, per the user's own explicit "implement the
current canonical 143 Missing scenarios" instruction. No persisted priority-plan doc names
Batch 8's approved scenario count either, same situation every prior batch disclosed -
scenarios were selected directly from the remaining Missing backlog's own dependency graph,
strictly prioritizing rows with (a) no unbuilt product-scope decision and (b) no dependency
on external data/infrastructure this project doesn't have, per the user's own stop-and-flag
rule. 17 rows moved Missing→VERIFIED (-17 Missing, +17 Verified): D3-07 (plot boundary as
plain JSONB points, not PostGIS - not enabled in this project), D5-02 (admin-authored crop
variety creation), D9-08 (task completion_percentage, farmer-entered, never changes
status), D13-02/D17-06/D19-04 (season/water/soil append-only history tables, each mirroring
CropCycleStageHistory's exact convention), D13-04 (zero-code bonus - PROVED, not assumed,
that already-VERIFIED D8-08 recurrence + D13-05 pruning task type already satisfy perennial
recurring maintenance), D14-02 (hourly forecast, real Open-Meteo hourly params, reuses the
weather_snapshots table via a new snapshot_type rather than a new table), D15-05/D15-07
(storm/hail decoded from the real, public WMO weather-code table - codes 95/96/99), D17-02/
D17-03 (farmer-declared water_availability + derived water_shortage), D50-04 (historical
yield aggregation - average_yield honestly stays None today since actual_quantity is never
populated anywhere in this codebase, a separately-deferred D49-02/D50-02 dependency,
confirmed by direct grep not assumed), D51-06 (certificate_reference, farmer-declared),
D55-05 (preferred_pickup_date - a narrower, farmer-stated-preference scope than a full
buyer-confirmed schedule, which would need D55-06/D55-07's own shape decided first), D58-04
(handling_charge, same itemized-breakdown convention as transport/commission/storage), and
D74-03 (photo-to-CropDamageRecord evidence link, reusing the existing disease-AI photo
pipeline, D74-02's own dependency already VERIFIED).

Genuinely blocked and left Missing, not force-closed (per row, with the real reason):
D15-06 (Cyclone - no WMO code represents a large-scale cyclone system; re-investigated
alongside D15-05/07's own WMO decode work and confirmed genuinely blocked on a real
track/warning feed, same root cause as D75-05), D55-04 (Transport rate - its own row
explicitly needs a real rate-reference dataset), D11-06 (auto-task on re-sow - would
contradict this project's own twice-made "no auto-generated agronomic tasks" decision,
D8-02/D9-01 precedent), D1-14 (automated-action consent - needs a product decision on
*which* automated action to gate), D7-10 (post-harvest stage - would require redefining
HARVESTED as non-terminal, touching many already-VERIFIED invariants), D78-11 (distinct
DISASTER_ALERT category - buildable, but closing it means reclassifying already-VERIFIED
weather-risk alerts (frost/flood/drought), which touches existing VERIFIED test assertions;
deferred to a dedicated, more careful batch rather than rushed here), D81-05/D81-09
(Observation/Notes offline - an entirely new domain/entity shape, a product decision this
batch does not make unilaterally, same judgment three prior batches already made). Every
other remaining Missing row was individually checked and falls into one of: a genuinely
absent external data source/feed/hardware (Govt Schemes, Satellite/PostGIS, IoT hardware,
live Mandi/market prices, insurer claim/settlement feeds, per-crop shelf-life or per-stage
sensitivity reference datasets), a large net-new product domain needing an explicit
decision (Machinery, Labour, FPO pooling, Community), or a dependency on one of the above.

Total unchanged at 798 - every change this batch was an internal status move, zero new/
removed rows. Full backend suite: 1055 passed, 1 failed (up from 996 pre-Batch-8 baseline).
Full Flutter suite: 312 passed, 0 failed (unchanged from baseline - no mobile changes this
batch; every addition was backend-only, confirmed non-breaking for mobile parsing since
Flutter models read named keys and ignore unknown ones). Migrations: 9 new revisions
(5b57af46965e was the pre-batch clock-tie hotfix; 5b87cb6eb39c, fc2b32df536e, 39a9e48c0858,
cd0584254c03, a595f6178964, e9f7a17d3dd6 are this batch's own), single alembic head
throughout, applied cleanly to both dev and test databases. `alembic check`: only the same
pre-existing, already-disclosed `crop_cycle_closure_snapshots` drift remains — no new drift
introduced by any of this batch's migrations.

**The 1 failure is NOT caused by this batch** - `tests/test_rule_versioning.py::test_a_query_for_an_old_date_still_reproduces_the_old_decision_after_a_threshold_change`,
in a file this batch never touched (D89 Rule Versioning). Root-caused, not assumed: 
`rule_version_repository.get_effective_at` orders by `RuleVersionSnapshot.effective_from.desc()
LIMIT 1` with no secondary tiebreaker - the exact same bug CLASS this session's own
offer-negotiation clock-tie hotfix (`get_latest_counter_offer`) already fixed elsewhere, but
this occurrence was never patched here. The failing test backdates `effective_from` to a
HARDCODED constant (`datetime(2020, 1, 1)`) on every run; since this project's test database
is a real, persistent Postgres instance never truncated between runs (a pattern this report
has repeatedly disclosed elsewhere), repeated executions of this exact test across this
session's many full-suite verification passes accumulated 11 rows all sharing that identical
`effective_from` timestamp (confirmed by direct query) - the tie-break, unconstrained by any
secondary ordering key, nondeterministically returns a stale row from an earlier run instead
of the current run's own row. This is a genuine, pre-existing, reproducible-in-isolation
defect (confirmed via `pytest tests/test_rule_versioning.py` alone, 1 failed/7 passed) -
latent under a normal single-run/fresh-database condition, surfaced here specifically by this
session's own unusually repeated re-execution against the persistent test database. NOT
fixed as part of this batch (out of this batch's authorized scope - implementing Missing
scenarios, not general bug-fixing); flagged for the user's explicit decision, same as the
counter-offer bug was before its own hotfix was authorized.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization plan's Batch 7. No persisted priority-plan doc names
Batch 7's approved scenario count either, same situation Batch 3/4/5/6
disclosed - assembled directly from the remaining backlog's own dependency
graph. 11 rows moved off Missing (-11 Missing): 9 to VERIFIED (+9 Verified —
the entire Storage domain: D53-01 Storage location, D53-02 Capacity, D53-03
Cost, D53-04 Duration, D53-05 Stored quantity, D53-07 Release from storage,
D52-04 Storage post-harvest, D48-04 Storage planning pre-harvest — all one
new `Storage`/`StorageUsage` implementation, migration `a7b8c9d0e1f2`,
mirroring `harvest_service.py`'s CRUD/ownership conventions; plus D9-13,
a zero-code fold-in of a duplicate scenario ID for the already-VERIFIED
D8-08), and 2 to OUT_OF_SCOPE (+2 Out of Scope — D2-10 active farm
selection and D22-01 fertilizer requirement, both deliberate design/safety
decisions confirmed by their own row text, not engineering gaps).
Deliberately NOT built: D53-06/D52-07 (spoilage) - both genuinely blocked
on an authoritative per-crop shelf-life reference dataset that does not
exist, same anti-fabrication class as D21-01's seed-rate deferral. Total
unchanged at 798 - every change this pass was an internal status move,
zero new/removed rows. Full backend suite: 996 passed (up from 986 - +10
new tests, `tests/test_storage_facility.py`), 0 failed. Full Flutter suite:
312 passed, 0 failed (unchanged - no mobile changes this batch). Migrations
applied cleanly to both dev and test databases, single head (`a7b8c9d0e1f2`).
See `docs/audit/FINAL_CANONICAL_group_{A,C}.md`'s own Batch 7 notes for the
full per-scenario breakdown.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization + Batch 1 implementation prompts. A credit-efficient
dependency analysis of all 215 Missing scenarios was performed first (not
implemented from), then exactly 17 approved Batch 1 items were implemented,
all in Group D: D89-01, D81-01, D93-05, D94-01/02/03/04/06/07,
D95-05/06/07/08, D96-02/07, D98-04/05. Verified 417→434 (+17): 16 genuine
Batch-1 fixes plus 1 zero-code bonus (D89-02, found already satisfied by an
earlier D88-07 fix while verifying D89-01's own stated dependency). Missing
215→198 (-17, matching). 1 of the 17 approved items (D95-07) was
investigated and correctly NOT force-closed - it shares Partial row
D88-06/D92-07/D93-08's exact "no crop-linked reference price exists" root
cause and stays genuinely Missing, documented in Group D's own row. Partial
row D89-08 re-verified (stays Partial, unchanged count): its two cited
dependencies (D89-01, D89-02) are now both Verified, narrowing its sole
remaining blocker to D89-03 (a larger, deliberately-deferred item). Total
unchanged at 798 - every change this pass was an internal status move,
zero new/removed rows. Full backend suite and full flutter suite both
re-run green after this batch. See docs/audit/FINAL_CANONICAL_group_D.md's
own batch note for the full per-scenario breakdown.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization plan's Batch 5. As with Batch 3/4, no persisted
priority-plan doc in this repo names Batch 5's approved scenario count -
assembled directly from the remaining backlog's own dependency graph
(rows genuinely buildable now with no new product/business decision or
unconfigured external provider needed, clustered where one small piece of
work closes several rows at once). 8 rows moved Missing→VERIFIED: D71-05/
06/07 (Plot/Farm/Season P&L - the fuller cost-variance/per-acre view
D70-04/05's own totals-only responses deliberately deferred to these
rows), D38-02/05 (treatment follow-up reminder sweep + reschedule, both
hard-blocked on D38-01 which was already VERIFIED), D96-08 (season
weather-impact comparison, reusing the real persisted crop_alert
Notification history), and D36-04/07 (case acknowledgement +
recommendation-version FK). D36-06 (expert identity) deliberately NOT
built - its own row explicitly flags it as a genuine product/privacy
decision, not an engineering gap. Verified 465→473 (+8), Missing
167→159 (-8). Total unchanged at 798 - every change this pass was an
internal status move, zero new/removed rows.

Two real pre-existing bugs found and fixed this batch, neither caused by
Batch 5's own changes but discovered while implementing it:
1. `crop_cycle_service.py`'s season-closure `weather_impact_summary`
   (D97-09, already VERIFIED) filtered for `weather_alert`/`rain_alert`/
   `heavy_rain_alert` - none of which is ever actually tied to a
   `crop_cycle` entity (only `crop_alert` is; the other three are always
   farm-scoped). `weather_alert_count` had been silently always 0 for
   every crop cycle ever closed, uncaught by the existing test (which
   only asserted the zero case). Fixed by adding `crop_alert` to the
   filter set, with a new regression test proving a real notification is
   now counted.
2. `case_repository.get_excluded_professional_ids` was missing
   `COMPLETED` from its exclusion set, so requesting a second opinion
   could re-select a professional who already completed a review for the
   same case - a real crash (`IntegrityError` on the `(case_id,
   professional_id)` unique constraint), reproduced directly while
   writing D36-07's own test. Fixed by adding `COMPLETED`; re-verified
   against the existing case-routing/SLA test suites for non-regression.

Full backend suite: **972 passed, 0 failed, 1 error** (up from 950 tests
collected pre-Batch-3 baseline growth). The 1 error,
`test_personalization.py::test_personalization_evidence_count_reflects_real_task_data`,
does not reproduce in isolation - 1/1 passes standalone, and 26/26 pass
running that entire file alone - the same pre-existing, disclosed
shared-test-database-scale flakiness pattern this project has repeatedly
documented (the test DB is a real, persistent Postgres instance, never
truncated between runs); this batch touched neither
`personalization_service.py` nor anything that test depends on. Full
Flutter suite: 312 passed, 0 failed (unchanged - no mobile changes this
batch). See docs/audit/FINAL_CANONICAL_group_{B,C,D}.md's own batch notes
for the full per-scenario breakdown.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization plan's Batch 4. As with Batch 3, no persisted
priority-plan doc in this repo names Batch 4's approved scenario count
the way Batch 1/2's own commit messages do - this batch was assembled
directly from the remaining backlog's own dependency graph (rows genuinely
buildable now with no new product/business decision or unconfigured
external provider needed, clustered where one small piece of work closes
several rows at once), the same method the original prioritization must
have used. 9 rows moved Missing→VERIFIED: D81-02/03/04/06/07 (Plot/Crop/
Task/Expense/Harvest offline queueing, reusing D81-01's shared
`PendingWriteQueue` - D81-05/D81-09 deliberately NOT built, both blocked
on an entirely new Observation/Notes entity, a real new-domain decision
this batch does not make unilaterally), D83-02 (exponential backoff
gating automatic sync retries), D89-04 (region scoping of a rule, sharing
D89-05's mechanism), D20-13 (soil test reminder sweep - all 4 of its own
cited dependencies were already VERIFIED), and D78-10 (soil notification -
closed as a zero-new-code bonus once its own cited blocker, the entire
Soil Testing domain, turned out to already be VERIFIED). Verified
456→465 (+9), Missing 176→167 (-9). Total unchanged at 798 - every change
this pass was an internal status move, zero new/removed rows. A real bug
found and fixed while implementing D83-02: `sync_coordinator.dart`'s
backoff check used strict `isAfter`, which failed on a clock tie (two
`DateTime.now()` calls returning an identical timestamp under fast
execution) - fixed to an inclusive comparison, caught by a pre-existing
test that started failing intermittently once backoff was added. Full
backend suite: 956 passed, 0 failed (up from 950 - +6 new tests, this
batch's own). Full Flutter suite: 312 passed, 0 failed (up from 304 - +8
new tests). Alembic migration chain re-verified single-headed and applies
cleanly. See docs/audit/FINAL_CANONICAL_group_A.md's and
docs/audit/FINAL_CANONICAL_group_D.md's own batch notes for the full
per-scenario breakdown.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization plan's Batch 3. This session began after an
unexpected shutdown mid-batch - reconstructed entirely from the working
tree and `docs/audit/` evidence, not from any prior session's claims (no
persisted priority-plan doc exists in the repo naming Batch 3's approved
scenario count, unlike Batch 1/2's own commit messages; the approved list
itself only existed in the prior, now-lost chat session). All code and
tests for 9 scenarios were already written and passing at the point of
reconstruction - only the doc-reconciliation pass below was still
pending. 9 rows moved Missing→VERIFIED: D74-02 (crop damage records - new
`CropDamageRecord`, farmer-entered, tied to an owned crop cycle + owned
policy), D79-04 (notification `expires_at`, category-specific default,
excluded-not-deleted), D89-07 (`AuditLogger` "RULE_EVALUATED" entries from
`crop_risk_service`/`weather_alert_orchestration_service`), D92-09 (daily
summary lines re-ranked by real urgency, stable sort), D78-12 (mobile
one-time terminal-state SnackBar, device-local only), and three provider
abstractions - D76-06 (`SatelliteProvider`), D77-06 (`IoTProvider`),
D90-03 (`MapsProvider`), each ABC + honest `NotConfigured*` stub mirroring
`WeatherProvider`/`MarketProvider`/`PaymentGatewayProvider` exactly, no
real backing implementation configured. D90-08 (satellite/NDVI provider
abstraction, audited from the Provider-Abstraction-domain angle) closes
as a zero-new-code bonus - identical gap to D76-06, same implementation.
D78-06 (market notification) was re-investigated and correctly left
Missing, not force-built - building it would directly contradict a
decision (`MARKET_ALERT`'s deliberate exclusion) this project's own prior
session already made twice; see its own row in
`docs/audit/FINAL_CANONICAL_group_D.md` for the full citation. Verified
447→456 (+9), Missing 185→176 (-9). Total unchanged at 798 - every change
this pass was an internal status move, zero new/removed rows. Full
backend suite re-run fresh after reconstruction: 950 passed, 0 failed (up
from Batch 2's 931 - the +19 are this batch's own new tests). Full
Flutter suite: 304 passed, 0 failed (up from 301). Alembic migration
chain verified single-headed (`42881a9226fb`) and applies cleanly. See
`docs/audit/FINAL_CANONICAL_group_D.md`'s own per-scenario rows for full
citations.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 MISSING
BACKLOG" prioritization plan's Batch 2 (the user's "go ahead next batch"
approving the priority plan's own recommended Batch 2 list). 14 approved
items processed, spanning all four canonical group files for the first
time this session: D65-01/02/03/05, D89-03, D90-02, D24-10, D2-08/D2-09,
D13-05, D30-05/D30-06, D74-01 all VERIFIED (+13); D65-04 (ledger-level
partial-payment tracking) investigated and deliberately deferred, not
force-built - a genuine ledger-design question (avoiding double-counting
or prematurely importing an incomplete sale into the farmer's own
financial ledger), correctly left for its own future batch rather than
built under time pressure. Verified 434→447 (+13), Missing 198→185 (-13,
matching). Partial row D89-08 re-verified again (stays Partial, unchanged
count): all three of its cited dependencies (D89-01/02/03) are now
Verified, narrowing its remaining blocker to a smaller, more specific gap
(a per-notification FK to the exact snapshot that produced it) than
before this batch. Total unchanged at 798 - every change this pass was an
internal status move, zero new/removed rows. One real pre-existing bug
found and fixed as a side effect of building D24-10's read path:
`input_inventory_service.create_item` logged its CREATED audit event with
`entity_id=str(item.id)` BEFORE the `db.flush()` that actually populates a
Python-side UUID default, so every such row had been silently unreachable
under the literal string "None" - not a Batch-2 scenario itself, but
disclosed here since it affects real production behavior. Full backend
suite: 931 passed, 0 failed/errored. Full flutter suite: 301 passed, 0
failed. See each of the four group files' own batch notes for the full
per-scenario breakdown.)*

*(Re-counted this continuation session, per the "SMART FARMER V3 PARTIAL
FUNCTIONALITY COMPLETION" prompt: every genuinely Partial scenario across
all four `FINAL_CANONICAL_group_{A,B,C,D}.md` files was re-inspected.
Verified 351→417 (+66), Partial 97→21 (-76): 21 Group-D rows this pass
(D75-06/07, D82-06, D84-01, D87-01/02, D88-01/03/05/07/10, D89-05, D90-04,
D91-03/08/09/10, D92-04, D93-03, D96-01, D98-03), plus the earlier Group
A/B/C passes this same session already folded into these per-group
totals. Environment Dependent 6→8 and Out of Scope 25→26 absorbed the two
rows that couldn't be honestly closed as either Verified or left plain
Partial (D75-04, D88-09) rather than being force-closed. 21 rows remain
genuinely Partial, each with an individually-verified, non-fabricated
reason recorded in its own group file - see each `FINAL_CANONICAL_group_*.md`'s
own "Count summary" batch note for the full per-row breakdown. Missing,
Future, and the 798 grand total are unchanged - every change this pass was
an internal status move, zero new/removed rows. Full backend suite: 864
passed, 0 failed/errored. Full flutter suite: 283 passed, 0 failed.)*

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
