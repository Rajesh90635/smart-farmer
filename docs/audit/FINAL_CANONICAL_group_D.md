# Canonical Gap Matrix — Group D (Domains 73-100)

Reconciles `docs/audit/c11_schemes_insurance_disaster_satellite_iot.md` (D73-D77),
`docs/audit/c12_notifications_offline_sync.md` (D78-D87), and
`docs/audit/c13_governance_farmbrain_security.md` (D88-D98, D100) against the status
deltas recorded since 2026-09-04 in `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md` and
`docs/FINAL_GAP_REPORT.md`, plus one new finding from a fresh read of
`backend/app/services/task_service.py`. Every scenario ID from the three cluster files
appears exactly once below, in its final reconciled status.

## Reconciliation deltas applied

| Scenario ID | Domain | Was | Now | Source citation |
|---|---|---|---|---|
| D80-01 | 80 | PARTIAL | VERIFIED | Matrix §B, batch "P0": "Timeout-triggered reassignment, case-level unavailability handling, CRITICAL priority now reachable" |
| D84-02 | 84 | BROKEN | IMPLEMENTED | Matrix §A: `camera_capture_screen.dart:154` now checks `e.statusCode == 401` matching `sync_coordinator.dart`'s existing check |
| D84-04 | 84 | BROKEN | IMPLEMENTED | Matrix §A: `pending_upload_queue.dart:216-239` now exposes `needsManualAction` with a real revival path (commit `bd0857d`) |
| D87-04 | 87 | BROKEN | IMPLEMENTED | Matrix §A, same revival-path fix as D84-04 |
| D87-05 | 87 | BROKEN | IMPLEMENTED | Matrix §A, same revival-path fix |
| D87-06 | 87 | BROKEN | IMPLEMENTED | Matrix §A, same revival-path fix |
| D88-07 | 88 | MISSING | PARTIAL | Matrix §B, batch 9: "`rule_version` added to `CropRiskScoreResponse` only (not yet extended to weather rules)" |
| D89-08 | 89 | MISSING | PARTIAL | Gap Report, 9-row resolution table: "Partially resolved... `Notification.rule_version` is now populated... for every weather-alert-rule-triggered notification... A full versioned/dated threshold snapshot... remains genuinely FUTURE work; this closes the 'undecided' label, not the underlying PARTIAL" |
| D90-10 | 90 | PARTIAL | VERIFIED | Matrix §B, batch 11: "Real `PaymentGatewayProvider` ABC + `is_sandbox_completable` guard refusing sandbox behavior in a misconfigured 'production' deployment" |
| D91-07 | 91 | PARTIAL | IMPLEMENTED | Matrix §B, batch 9: "New `POST /ai/analysis/{id}/correction` ties farmer correction directly to a specific disease-detection result" |
| D91-09 | 91 | MISSING | PARTIAL | Matrix §B, batch 9: "Raw false-positive/false-negative signal now captured via `farmer_correction`; no aggregation/dashboard endpoint yet" |
| D91-10 | 91 | MISSING | PARTIAL | Matrix §B, batch 9, same citation as D91-09 |
| D92-01 | 92 | MISSING | VERIFIED | Matrix §B, batch 1 (Daily Brief): "`get_daily_summary()` now wires in disease/risk/finance lines (only when genuinely present)" |
| D92-02 | 92 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D92-06 | 92 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D92-08 | 92 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D93-01 | 93 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D93-04 | 93 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D93-09 | 93 | MISSING | VERIFIED | Matrix §B, batch 1, same citation |
| D94-08 | 94 | MISSING | VERIFIED | Gap Report, 9-row resolution table: "`FarmerProfile.last_daily_summary_snapshot`/`last_daily_summary_at`... `get_daily_summary` diffs against it... Test: `test_assistant_chat.py::test_daily_summary_flags_what_changed_since_last_visit`" |
| D96-03 | 96 | MISSING | VERIFIED* | Matrix §B, batch 2: "`actual_quantity` now read into comparison/learning outputs. *No production code path populates `actual_quantity` yet... tested via direct DB insertion simulating that future write path, so real farmer-facing value is currently zero; disclosed, not hidden" |
| D97-10 | 97 | MISSING | VERIFIED | Gap Report, 9-row resolution table: "`CropCycle.lessons_learned`, settable only via `CropCycleCloseRequest` at `close_my_crop_cycle`... Tests: `test_crop_cycles.py::test_close_crop_cycle_*lessons_learned*` (2)" |
| D98-02 | 98 | MISSING | VERIFIED* | Matrix §B, batch 2, same caveat as D96-03 (shared batch) |
| D100-09 | 100 | MISSING | VERIFIED | Matrix §B, batch 10: "`GET /farmers/me/data-export`, `POST /farmers/me/delete-account`; 8 new tests; explicitly a good-faith MVP, not a certified compliance review" |

23 scenario IDs changed status via the two source documents, plus 3 more resolved directly
this session by re-reading current code and tests (not from either source document):
D97-12 (new finding, BROKEN→VERIFIED after the fix below), D78-07 and D78-09
(MISSING→VERIFIED — `payment_service.py`/`input_inventory_service.py` already fire the
required notifications; D78-07 needed a new test, D78-09 already had one). See each row's
own entry in Sections 1/3/4 for the full evidence. All other scenario IDs in D73-D100 are
carried forward unchanged from their cluster-file classification.

## New finding this pass

**Confirmed BROKEN.** `backend/app/services/task_service.py::create_task` (lines 41-65)
never checks the parent `CropCycle.cultivation_status` before creating a task:

```
41  def create_task(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: TaskCreateRequest) -> TaskResponse:
42      farmer_uuid = uuid.UUID(farmer_id)
43      crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
44      if crop_cycle is None:
45          raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
46
47      if payload.depends_on_task_id is not None:
48          _validate_dependency(db, farmer_uuid, crop_cycle_id, payload.depends_on_task_id)
49
50      task = Task(
51          farmer_id=farmer_uuid,
...
60      task_repository.create(db, task)
```

Between the ownership check (line 43-45) and task construction (line 50), there is no
guard against `crop_cycle.cultivation_status` being `HARVESTED` or `CANCELLED`. This is
a genuine regression against the module's own established discipline, not an absent
feature:

- `complete_task`'s recurring-task auto-creation (same file, line 172) explicitly checks
  `crop_cycle.cultivation_status not in _TERMINAL_CULTIVATION_STATUSES` before spawning
  the next recurrence.
- `cancel_all_pending_for_crop_cycle` (lines 209-228) proactively cancels every PENDING
  task specifically because "a crop cycle ends (CANCELLED or HARVESTED)... a task still
  PENDING for it would otherwise stay open/overdue forever with no crop cycle left to
  act on" (its own docstring, citing D9-15).

`create_task` is the one path in this file that contradicts that established pattern: a
farmer (or any caller) can manually `POST` a brand-new task against a crop cycle that has
already been closed, and nothing rejects it. This affects Domain 97 (Season Closure) —
the checklist's "closed seasons cannot accidentally receive active-season tasks"
scenario — which has no existing scenario ID in `c13`'s Domain 97 table (D97-01 through
D97-11 are all about season-closure *data capture*, not task-creation guarding). It is
carried in this matrix as a new, additional entry: **D97-12 (new)**, classified BROKEN,
not MISSING or PARTIAL — the guard pattern already exists twice in the same file and was
simply not applied a third time here.

## Count summary (this group)

222 original scenario rows (38 in c11 + 69 in c12 + 115 in c13) plus 1 new finding = 223 total.

| Status | Count |
|---|---:|
| VERIFIED | 74 |
| IMPLEMENTED | 30 |
| PARTIAL | 31 |
| MISSING | 75 |
| BROKEN | 0 |
| FUTURE | 11 |
| OUT_OF_SCOPE | 2 |
| ENVIRONMENT_DEPENDENT | 0 |
| TOTAL | 223 |

*(Updated this session, P1 task-overdue-reminder cluster: D78-01 MISSING→VERIFIED (-1
MISSING, +1 VERIFIED). Further updated, weather-risk cluster: D75-01/D75-02
MISSING→VERIFIED (-2 MISSING, +2 VERIFIED), fixed via the same cumulative-rainfall/
consecutive-dry-days functions as D15-08/D15-09. Total unchanged.)*

*(Updated this session: D97-12 BROKEN→VERIFIED (-1 BROKEN, +1 VERIFIED);
D78-07 MISSING→VERIFIED, D78-09 MISSING→VERIFIED (-2 MISSING, +2 VERIFIED).
Total unchanged at 223 — all three were internal status moves, not new/
removed rows.)*

*(Further updated this continuation session — notification-wiring batch: D78-03 (disease)
MISSING→VERIFIED, D78-08 (dispute) MISSING→VERIFIED, D78-05 (harvest) MISSING→VERIFIED
(-3 MISSING, +3 VERIFIED); D78-13 (security/password-change) MISSING→PARTIAL (-1 MISSING,
+1 PARTIAL, not VERIFIED - see its own entry: the password-change half is built and
tested, but the new-device-login half is genuinely not built, no device/session
fingerprinting exists in this codebase, disclosed rather than fabricated). D78-03/08
required new `DISPUTE_ALERT`/reusing `DISEASE_ALERT` categories and new call sites;
D78-05 needed no code at all, confirmed already satisfied by `harvest_service.py`'s
existing D47-05 wiring. Total unchanged at 223 - all four were internal status moves.
See each row's own entry below.)*

*(Further updated this continuation session — season-closure batch: D97-02/D97-03/D97-04/
D97-05/D97-06/D97-07 PARTIAL→VERIFIED (-6 PARTIAL, +6 VERIFIED); D97-08/D97-09 MISSING→
VERIFIED (-2 MISSING, +2 VERIFIED). New `CropCycleClosureSnapshot` table, created once by
`close_my_crop_cycle`, consolidates what the source audit doc separately proposed as new
`CropCycle` columns (D97-02/03) and a shared table (D97-04..09) into one table - all eight
rows are the same "freeze at close time" concept. Total unchanged at 223 - all eight were
internal status moves. See each row's own entry below.)*

## 1. Attended (Verified + Implemented) — condensed list

| Scenario ID | Domain | Scenario Name | Status | One-line evidence |
|---|---|---|---|---|
| D78-02 | 78 | Weather notification | VERIFIED | `test_weather_check_creates_a_rain_notification` (test_notifications.py:29) |
| D78-07 | 78 | Payment notification | VERIFIED (this session, was Missing) | `payment_service._notify_payment_failed`; `test_payments.py::test_payment_failure_notifies_the_farmer` (new) |
| D78-09 | 78 | Stock notification | VERIFIED (this session, was Missing) | `input_inventory_service._check_low_stock`; `test_input_inventory.py::test_low_stock_alert_fires_once_then_stays_quiet_until_restocked` |
| D97-12 | 97 | Closed-season task-creation guard | VERIFIED (this session, was Broken) | `task_service.create_task`'s new `_TERMINAL_CULTIVATION_STATUSES` guard; `test_tasks.py::test_cannot_create_a_task_for_a_closed_crop_cycle` + `::test_can_create_a_task_for_a_cancelled_crop_cycle_is_also_rejected` (new) |
| D79-01 | 79 | Duplicate event | VERIFIED | `test_repeated_weather_checks_do_not_duplicate_the_same_alert` (test_notifications.py:42) |
| D79-02 | 79 | Duplicate notification | VERIFIED | same test as D79-01, verified via listing endpoint |
| D79-03 | 79 | Deduplication key | VERIFIED | same dedup test proves key construction end-to-end |
| D79-05 | 79 | Read state | VERIFIED | `test_mark_notification_read`/`test_mark_all_read`/`test_farmer_a_cannot_read_farmer_bs_notification` (test_notifications.py:65,79,92) |
| D80-01 | 80 | Critical | VERIFIED (delta) | CRITICAL priority now reachable per P0 batch — quiet-hours bypass no longer dead code |
| D80-02 | 80 | High | VERIFIED | `test_heavy_rain_alert_by_probability` (test_weather_alert_rules.py:26-30) |
| D80-04 | 80 | Low | VERIFIED | `test_light_rain_alert_at_threshold` (test_weather_alert_rules.py:19-24) |
| D80-05 | 80 | Priority rules | VERIFIED | 15 tests in `test_weather_alert_rules.py`, all passing |
| D80-06 | 80 | Farmer preferences | VERIFIED | `test_disabling_rain_alerts_suppresses_new_rain_notifications` (test_notifications.py:54) |
| D81-08 | 81 | Photo offline | VERIFIED | `pending_upload_queue_test.dart` (17/17) + `test_retry_with_same_client_upload_id_does_not_duplicate` (test_crop_photos.py:115) |
| D82-01 | 82 | Queue | VERIFIED | `enqueue adds an item with the default waitingForNetwork status` (pending_upload_queue_test.dart) |
| D82-03 | 82 | Retry (selection logic) | VERIFIED | queue-level `retryable` selection VERIFIED by test; coordinator orchestration itself IMPLEMENTED only (no dedicated test) |
| D82-07 | 82 | Duplicate prevention | VERIFIED | `test_retry_with_same_client_upload_id_does_not_duplicate`, `test_different_client_upload_ids_create_separate_photos` (test_crop_photos.py:115,132) |
| D83-04 | 83 | Retry failure (error captured) | VERIFIED | `failed upload retains its error message` (pending_upload_queue_test.dart) |
| D84-05 | 84 | Queue preservation | VERIFIED | `loadFromDisk with no prior manifest leaves the queue empty` + `toJson/fromJson round-trip` (pending_upload_queue_test.dart) |
| D86-01 | 86 | API idempotency | VERIFIED | `test_duplicate_checkout_with_same_idempotency_key_does_not_create_two_orders` (test_orders.py:136) |
| D86-02 | 86 | Event idempotency | VERIFIED | `test_repeated_weather_checks_do_not_duplicate_the_same_alert` (test_notifications.py:42) |
| D86-04 | 86 | Duplicate submission | VERIFIED | same as D86-01 |
| D86-05 | 86 | Duplicate event | VERIFIED | same as D86-02 |
| D86-06 | 86 | Duplicate notification | VERIFIED | same dedup test, DB constraint `uq_notifications_farmer_dedup_key` |
| D87-03 | 87 | Error reason | VERIFIED | `failed upload retains its error message` (pending_upload_queue_test.dart) |
| D88-08 | 88 | Model version recorded alongside every AI output | VERIFIED | `test_model_version_is_always_recorded` (test_ai_analysis.py:90-101) |
| D90-01 | 90 | Weather provider abstraction | VERIFIED | real `WeatherProvider` ABC + working `OpenMeteoProvider`; `test_weather.py`/`test_weather_actions.py` |
| D90-07 | 90 | AI/vision model provider abstraction | VERIFIED | `ModelProvider` ABC, `fake_model_provider.py` test double, `test_model_version_is_always_recorded` |
| D90-09 | 90 | OCR provider abstraction | VERIFIED | `OCRProvider` ABC + working `TesseractOCRProvider`; `test_flow_b_invoice_ocr_never_auto_creates_ledger_entry` |
| D90-10 | 90 | Payment provider abstraction | VERIFIED (delta) | Real `PaymentGatewayProvider` ABC + `is_sandbox_completable` guard |
| D91-02 | 91 | Model version captured on AI output | VERIFIED | `test_model_version_is_always_recorded` (test_ai_analysis.py:90) |
| D91-04 | 91 | Output captured | VERIFIED | same rows as D88-08/91-02 |
| D91-05 | 91 | Confidence captured and classified | VERIFIED | `test_high_confidence`/`test_medium_confidence`/`test_low_confidence` (test_ai_model_components.py:12-18) |
| D91-11 | 91 | Recommendation acceptance tracked | VERIFIED (for advisories) | `test_feedback_ratio_reflects_real_submitted_feedback` (test_personalization.py:133); MISSING specifically for disease-detection acceptance |
| D92-01 | 92 | One aggregation pulling all farm state together | VERIFIED (delta) | Daily Brief batch — `get_daily_summary()` now wires disease/risk/finance in when present |
| D92-02 | 92 | Current risks included in farm state | VERIFIED (delta) | same Daily Brief batch |
| D92-03 | 92 | Current tasks included | VERIFIED | `test_daily_summary_includes_overdue_task_count_reusing_the_real_task_repository` (test_assistant_chat.py:134) |
| D92-06 | 92 | Disease included | VERIFIED (delta) | Daily Brief batch |
| D92-08 | 92 | Finance included | VERIFIED (delta) | Daily Brief batch |
| D93-01 | 93 | Critical risks summarized | VERIFIED (delta) | Daily Brief batch |
| D93-02 | 93 | Overdue tasks summarized | VERIFIED | test_assistant_chat.py:134 |
| D93-04 | 93 | Disease/pest actions summarized | VERIFIED (delta) | Daily Brief batch |
| D93-09 | 93 | Finance summarized | VERIFIED (delta) | Daily Brief batch |
| D94-08 | 94 | "What changed since last visit" aggregator | VERIFIED (delta) | `test_daily_summary_flags_what_changed_since_last_visit` (test_assistant_chat.py) |
| D95-01 | 95 | Crop (disease) risk factor | VERIFIED | `test_disease_detected_analysis_produces_high_risk_factor` (test_crop_risk.py:37) |
| D95-02 | 95 | Weather risk factor | VERIFIED | `test_weather_spray_condition_produces_medium_risk_factor` (test_crop_risk.py:158) |
| D95-03 | 95 | Disease risk factor | VERIFIED | same evidence as D95-01 |
| D96-03 | 96 | Compare yield | VERIFIED* (delta) | tested via direct DB insertion; no production write path populates `actual_quantity` yet — real farmer-facing value currently zero, disclosed not hidden |
| D96-04 | 96 | Compare cost | VERIFIED | `test_comparison_treats_zero_actual_cost_as_a_real_equal_comparison_not_missing_data` (test_crop_performance.py:90,121) |
| D97-10 | 97 | Lessons learned captured at closure | VERIFIED (delta) | `test_crop_cycles.py::test_close_crop_cycle_*lessons_learned*` (2 tests) |
| D97-11 | 97 | Close cycle workflow itself | VERIFIED (workflow) | real, audited endpoint; comprehensive field capture (D97-02..09) separately PARTIAL/MISSING |
| D98-01 | 98 | Previous crop used in learning | VERIFIED | `test_one_treatment_does_not_create_a_strong_permanent_preference`, `test_no_history_produces_insufficient_data_for_all_signals` (test_personalization.py:26,37) |
| D98-02 | 98 | Previous yield used in learning | VERIFIED* (delta) | same production-path caveat as D96-03 |
| D100-01 | 100 | Authentication | VERIFIED | `test_jwt_round_trip`, `test_jwt_rejects_tampered_token` (test_security.py:18-28), passing |
| D100-04 | 100 | Farmer ownership | VERIFIED | `test_flow_a_never_leaks_to_another_farmer`, `test_cross_farmer_isolation_holds_across_the_entire_integrated_surface` (test_phase40_integration.py) |
| D100-07 | 100 | Tenant isolation (cross-farmer sweep) | VERIFIED | `test_cross_farmer_isolation_holds_across_the_entire_integrated_surface`, 9-endpoint sweep, all 404 |
| D100-08 | 100 | File access control | VERIFIED (indirectly) | exercised by `test_flow_b_invoice_ocr_never_auto_creates_ledger_entry` + cross-farmer sweep |
| D100-09 | 100 | Data privacy (GDPR-style export/deletion) | VERIFIED (delta) | `GET /farmers/me/data-export`, `POST /farmers/me/delete-account`; 8 new tests; good-faith MVP, not certified compliance |
| D100-10 | 100 | Consent | VERIFIED | typed/versioned `ConsentRecord`; 422 on missing required consent at registration |
| D100-11 | 100 | Automated-action consent | VERIFIED | `test_flow_b_invoice_ocr_never_auto_creates_ledger_entry` (test_phase40_integration.py:116-145) |
| D78-04 | 78 | Expert response | IMPLEMENTED | no test specifically asserts the notification row for `CASE_REVIEWED` |
| D80-03 | 80 | Normal (Medium) | IMPLEMENTED | tests assert alert fires by message_key, never assert `.priority.value == "medium"` |
| D82-02 | 82 | Upload | IMPLEMENTED | no `sync_coordinator_test.dart` exists |
| D82-04 | 82 | Connectivity recovery | IMPLEMENTED | no test file for `NetworkStatusChecker` subscription behavior |
| D82-05 | 82 | Server acknowledgement | IMPLEMENTED | queue-level `remove()` tested; coordinator's call to it is not |
| D83-01 | 83 | Network retry | IMPLEMENTED | no coordinator-level test; queue-level selection VERIFIED separately (D82-03) |
| D83-03 | 83 | Maximum retries | IMPLEMENTED | counting/transition logic untested; terminal-state filtering is |
| D83-05 | 83 | Manual retry | IMPLEMENTED | no widget test for `camera_capture_screen.dart` |
| D84-02 | 84 | Token expires during upload | IMPLEMENTED (delta) | `camera_capture_screen.dart:154` now checks `e.statusCode == 401` matching background path |
| D84-03 | 84 | Token expires during sync (background) | IMPLEMENTED | correct logic, no `sync_coordinator_test.dart` |
| D84-04 | 84 | Re-authentication (resume queue) | IMPLEMENTED (delta) | `needsManualAction` revival path now exists (commit `bd0857d`) |
| D87-04 | 87 | Retry (from dead-letter state) | IMPLEMENTED (delta) | same revival-path fix |
| D87-05 | 87 | Manual recovery | IMPLEMENTED (delta) | same revival-path fix — UI now exists |
| D87-06 | 87 | Visibility to user/admin | IMPLEMENTED (delta) | same revival-path fix — farmer-facing visibility now exists |
| D88-02 | 88 | Provider abstraction identity exposed with data | IMPLEMENTED | consistent across Weather/AI/OCR; no dedicated cross-provider test |
| D91-01 | 91 | Model identity captured on AI output | IMPLEMENTED | covered generically by AI-analysis tests |
| D91-06 | 91 | Expert agreement recorded | IMPLEMENTED | `final_verified_class` populated by real case-review workflow; no dedicated test cited |
| D91-07 | 91 | Farmer correction of an AI result | IMPLEMENTED (delta) | new `POST /ai/analysis/{id}/correction` ties correction to specific AI result |
| D92-05 | 92 | Weather included | IMPLEMENTED | `tools.get_weather_status` (tools.py:83-101) |
| D93-07 | 93 | Harvest summarized | IMPLEMENTED | conditional on status approaching/ready/listed |
| D96-05 | 96 | Compare revenue | IMPLEMENTED | covered by same comparison tests as D96-04 |
| D96-06 | 96 | Compare profit | IMPLEMENTED | same tests |
| D97-01 | 97 | Actual harvest (date) captured at closure | IMPLEMENTED | `CROP_CYCLE_CLOSED`/`CROP_CYCLE_STATUS_CHANGED` audit logged; no dedicated close-cycle test cited in this pass |
| D100-02 | 100 | Authorization | IMPLEMENTED | `require_role` dependency, consistently applied |
| D100-03 | 100 | RBAC | IMPLEMENTED | real `Role` enum; AUTOMATION_SERVICE-never-financial rule enforced per-site, not centrally |
| D100-05 | 100 | Expert access | IMPLEMENTED | scoped `CaseAssignment`/`PhotoAccessGrant`; no dedicated expert-scoping test in files reviewed |
| D100-06 | 100 | Admin access | IMPLEMENTED | `require_role(Role.ADMIN.value)` consistently gated |
| D100-12 | 100 | Audit events | IMPLEMENTED | append-only `AuditLog`, 27+ services; no dedicated content-assertion test found |
| D100-13 | 100 | Security events | IMPLEMENTED | distinct `LOGIN_FAILED`/`LOGIN_SUCCESS`/`PASSWORD_RESET`/`PASSWORD_CHANGED` actions |
| D100-15 | 100 | Input validation | IMPLEMENTED | Pydantic constraints spot-checked across multiple schemas |

## 2. Partial — full itemized (EVERY row, no aggregation)

### D75-04 — Storm alert/detection
- Domain: 75. Disaster Management
- Current implementation status: Partial
- Existing relevant files/classes/functions: `weather_alert_rules.py:71-80` `evaluate_extreme_weather_alerts()` (high-wind clause); `weather_alert_orchestration_service.py`; `NotificationCategory.WEATHER_ALERT`
- Missing component: storm/cyclone classification distinct from a generic "high wind" reading; no damage, evidence, inspection, or recovery workflow attached
- Required implementation: a `disaster_event_service.py` layering storm-severity tiers (e.g. sustained wind + gust pattern) on top of the existing wind reading, and a distinct `DISASTER_ALERT` category rather than folding storms into `WEATHER_ALERT`
- Dependencies: an external wind-gust/cyclone-track feed (e.g. IMD) — none ingested anywhere in this repo today
- Backend work: new `disaster_event_service.py` mirroring `weather_alert_rules.py`'s pure-function pattern; extend `NotificationCategory`
- Database/migration work: new `disaster_events` table (event_type, severity, source, farm_id FK)
- Mobile work: none beyond the existing notification list screen (reused)
- Automation work: scheduled ingestion of the external feed, using the `scheduler.py` (APScheduler) pattern already proven for Expert SLA and weather sweeps
- Notification work: new `DISASTER_ALERT` category, CRITICAL priority for a genuine cyclone
- Offline/sync impact: none — read-only alert like existing weather alerts
- Security/RBAC impact: none — additive, farmer-scoped like existing alerts
- Tests required: unit tests on storm-severity thresholds; integration test asserting a distinct disaster-category notification (not folded into `weather_alert`)
- Verification method: new `tests/test_disaster_alerts.py` mirroring `test_weather_alert_rules.py`'s structure

### D75-06 — Heat (heatwave) alert/detection
- Domain: 75. Disaster Management
- Current implementation status: Partial
- Existing relevant files/classes/functions: `weather_alert_rules.py:82-92` `evaluate_extreme_weather_alerts()`; test: `test_extreme_heat_detected` (test_weather_alert_rules.py:53-61)
- Missing component: damage detection, evidence capture, inspection, or recovery guidance beyond the single MEDIUM-priority notification
- Required implementation: a heat-specific advisory/recovery content block attached to the existing alert (e.g. "protect crop from heat stress" guidance), plus an optional farmer-logged damage report
- Dependencies: none blocking the advisory text; a damage-report entity would need the same disaster-event model proposed under D75-08/09
- Backend work: extend `weather_alert_orchestration_service.py` to attach static advisory content when `extreme_heat_alert` fires
- Database/migration work: none for the advisory text; shares D75-08/09's `disaster_events` table if damage capture is built
- Mobile work: surface the advisory text in the existing notification detail view
- Automation work: none — reuses the existing alert trigger
- Notification work: additive text field on the existing `WEATHER_ALERT`/`extreme_heat_alert` notification, no new category needed for the advisory itself
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: test asserting advisory text is attached when the heat alert fires
- Verification method: extend `tests/test_weather_alert_rules.py`

### D75-07 — Frost alert/detection
- Domain: 75. Disaster Management
- Current implementation status: Partial
- Existing relevant files/classes/functions: `weather_alert_rules.py:93-102` `evaluate_extreme_weather_alerts()`; test: `test_extreme_cold_detected` (test_weather_alert_rules.py:53-61)
- Missing component: the alert is labelled "extreme cold", never specifically "frost"; no crop-protection guidance or damage/recovery workflow attached
- Required implementation: a frost-specific message key distinct from generic extreme-cold wording, plus crop-protection advisory content
- Dependencies: none
- Backend work: add a `frost_alert` message-key variant to `weather_alert_rules.py`, conditioned on the same threshold, or an additional sub-classification
- Database/migration work: none
- Mobile work: none beyond existing notification rendering
- Automation work: none
- Notification work: message-key/text change only, same `WEATHER_ALERT` category and priority
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the frost-specific wording/advisory appears distinctly from generic cold wording
- Verification method: extend `tests/test_weather_alert_rules.py`

### D82-06 — Sync status
- Domain: 82. Sync
- Current implementation status: Partial
- Existing relevant files/classes/functions: `PendingUploadStatus` enum (6 values); `toJson/fromJson round-trip preserves all fields` test (pending_upload_queue_test.dart)
- Missing component: any farmer-visible UI reading `PendingUploadQueue`/status — `crop_photo_list_screen.dart` has zero references (confirmed by grep)
- Required implementation: wire `crop_photo_list_screen.dart` to subscribe to `PendingUploadQueue` and render a per-photo sync-status badge (queued/uploading/failed/retriesExhausted/needsManualAction)
- Dependencies: none — the data model already exists and is tested
- Backend work: none — purely a mobile-side gap
- Database/migration work: none
- Mobile work: extend `crop_photo_list_screen.dart` to read queue state and show status chips; dovetails with D87-05's now-implemented dead-letter revival UI
- Automation work: none
- Notification work: none directly (could later feed D78-12, still MISSING)
- Offline/sync impact: this IS the missing offline/sync visibility UI
- Security/RBAC impact: none
- Tests required: new widget test for `crop_photo_list_screen.dart` asserting status badges reflect queue state
- Verification method: new `flutter test test/features/crop_photo/crop_photo_list_screen_test.dart`

### D84-01 — Token expires during normal use
- Domain: 84. Auth Expiry
- Current implementation status: Partial
- Existing relevant files/classes/functions: `AuthRepository.restoreSession()` (auth_repository.dart:57-68, startup-only refresh); `ApiClient` (api_client.dart, no 401 interceptor outside the crop-photo sync path)
- Missing component: a mid-session 401 interceptor and a directed re-login prompt (farmer currently sees a generic "Request failed with status 401" error)
- Required implementation: a global response interceptor in `api_client.dart` that catches 401 on any call, attempts one silent refresh, and routes to a "please log in again" flow on failure instead of surfacing a raw `ApiException`
- Dependencies: none — `/auth/refresh` endpoint already exists and works
- Backend work: none — backend already supports refresh
- Database/migration work: none
- Mobile work: `api_client.dart` interceptor + a shared `SessionExpiredException` consumed uniformly by all screens
- Automation work: none
- Notification work: none
- Offline/sync impact: none directly, though this interacts with D84-02/03/04 (upload-path 401 handling), now IMPLEMENTED
- Security/RBAC impact: none — defensive UX only, no privilege change
- Tests required: widget/unit test asserting any 401 triggers the shared re-login flow, not a generic error toast
- Verification method: new `test/core/api_client_401_test.dart`

### D87-01 — Permanent failure
- Domain: 87. Dead-letter / Failed Sync
- Current implementation status: Partial
- Existing relevant files/classes/functions: `sync_coordinator.dart:126-133` (`retryCount` vs `kMaxAutomaticRetries=5`); `retriesExhausted` status
- Missing component: this concept exists only for crop photos (no other entity has offline sync at all, see D81-01..07/09); the counting/transition logic in `_recordFailureAndMaybeExhaust` itself has no dedicated test (only the resulting terminal-state filtering is tested)
- Required implementation: a dedicated unit test for `_recordFailureAndMaybeExhaust`'s counting/transition logic; broader "permanent failure" coverage is structurally blocked on other entities getting offline queues first
- Dependencies: none for the test gap; D81-01..07/09 for the broader entity coverage
- Backend work: none
- Database/migration work: none
- Mobile work: none beyond the new test
- Automation work: none
- Notification work: none
- Offline/sync impact: this is the offline/sync concept itself, narrowly scoped to photos only
- Security/RBAC impact: none
- Tests required: new `sync_coordinator_test.dart` (does not exist today) covering retry-count exhaustion transition directly
- Verification method: `flutter test test/features/crop_photo/sync_coordinator_test.dart` (new)

### D87-02 — Dead-letter state
- Domain: 87. Dead-letter / Failed Sync
- Current implementation status: Partial
- Existing relevant files/classes/functions: `pending_upload_queue.dart:214-215` `needsManualAction` getter (client-only, ephemeral manifest field)
- Missing component: any server-side/admin visibility — no backend dead-letter table exists at all; this is entirely a client-side, on-device concept
- Required implementation: a lightweight `POST /crop-photos/dead-letter-report` endpoint the client calls when an item first becomes `needsManualAction`, so an ops/admin view can see stuck uploads across farmers
- Dependencies: an admin panel/endpoint capable of surfacing it (none exists in this project per Domain 100's audit)
- Backend work: new endpoint gated by `require_role(Role.ADMIN)` for reading; farmer-authenticated for reporting
- Database/migration work: new `dead_letter_reports` table (farmer_id, client_upload_id, reason, reported_at)
- Mobile work: `SyncCoordinator` posts a best-effort report on first transition to `needsManualAction`
- Automation work: none
- Notification work: none (could notify ops/admin in a later phase, out of current scope)
- Offline/sync impact: extends the existing photo-only offline path with a reporting side-channel
- Security/RBAC impact: new admin-only read endpoint, using the existing `require_role(Role.ADMIN)` dependency pattern
- Tests required: backend test asserting only ADMIN can read the report list
- Verification method: new `tests/test_dead_letter_reports.py`

### D88-01 — Source recorded on returned data
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `weather_snapshot.py:6-8,42` (`provider` field), `ai_analysis.py:86` (`model_name`), `reference_price.py:20-26` (`source_type` enum)
- Missing component: no unified source concept across crop-risk factors, notifications, or rule outputs
- Required implementation: add a `source`/`derived_from` field to `AlertCandidate`/`RiskFactor` dataclasses and to the persisted `Notification` row
- Dependencies: `crop_risk_service.py` and `weather_alert_rules.py` would need to thread source metadata through their existing pure functions
- Backend work: extend `RiskFactor`/`AlertCandidate` with a `source` field; extend `Notification` model with `source_summary`
- Database/migration work: additive migration on `notifications.source_summary` (nullable)
- Mobile work: optionally surface source string in notification detail view
- Automation work: none
- Notification work: additive field only, no new category
- Offline/sync impact: none
- Security/RBAC impact: none — additive metadata field
- Tests required: test asserting every generated notification/risk-factor carries a non-empty source string
- Verification method: extend `test_notifications.py`/`test_crop_risk.py`

### D88-03 — Fetch date recorded
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `reference_price.py:43` `retrieved_at` column (exists in DB, dropped from `ReferencePriceResponse` schema at `schemas/price.py:20-28`)
- Missing component: exposing `retrieved_at` in the API response
- Required implementation: add `retrieved_at` to `ReferencePriceResponse`
- Dependencies: none — pure schema change, column already exists
- Backend work: `schemas/price.py` add field; `price_query_service.py` pass it through
- Database/migration work: none — column already exists
- Mobile work: display fetch recency in price screens
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: schema test asserting `retrieved_at` present in the response
- Verification method: extend `tests/test_prices.py`

### D88-04 — Effective date recorded
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `ReferencePrice.effective_date` (reference_price.py:42-43), required/indexed, intentionally distinct from `retrieved_at`
- Missing component: no effective-date concept for weather, AI results, or rule outputs
- Required implementation: naturally extends from D89's rule-versioning system (effective-date-scoped thresholds), not a standalone price-domain fix
- Dependencies: D89-02/03 (rule version, effective-date scoping of a rule)
- Backend work: tie to D89's rule-version service when built
- Database/migration work: none additional beyond D89's
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none additional beyond existing price tests until D89 is built
- Verification method: existing price tests already cover the implemented (price-only) part

### D88-05 — Region recorded
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `ReferencePrice.region` JSONB field (reference_price.py:40)
- Missing component: `FarmWeatherResponse` has no region field; no rule/risk output carries region
- Required implementation: surface the farm's already-seeded Mandal/Village (per project master-data) as a `region` field on `FarmWeatherResponse`
- Dependencies: Mandal (687) + Village (16,438) master data — already seeded per project memory
- Backend work: `schemas/weather.py` add `region` derived from `Farm`'s existing Mandal/Village FK
- Database/migration work: none — Farm already links to Mandal/Village
- Mobile work: optionally display region in weather screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting region populated when farm has a resolvable mandal/village
- Verification method: extend `tests/test_weather.py`

### D88-06 — Crop linkage recorded
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `AIAnalysis.crop_id`/`crop_cycle_id` FK (ai_analysis.py:76-81); `CropCycle.crop_id` (crop_cycle.py:82)
- Missing component: `ReferencePrice` has no crop linkage at all — only `product_id`, scoped to input products (seed/fertilizer), never crop-selling prices (Phase 32 note, `SMART_FARMER_V3_PHASE_TRACKER.md:30`)
- Required implementation: extend `ReferencePrice` (or add a sibling model) with a `crop_id` FK for output/selling prices
- Dependencies: revisiting the Phase 32 product-only scoping decision
- Backend work: `reference_price.py` model change or new sibling model; `price_query_service.py` new query path
- Database/migration work: migration adding a nullable `crop_id` FK column, or a new table
- Mobile work: none required beyond existing price screens
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a crop-linked reference-price query returns correct rows
- Verification method: extend `tests/test_prices.py`

### D88-07 — Rule version recorded alongside a rule-driven output
- Domain: 88. Data Provenance
- Current implementation status: Partial (delta: was MISSING)
- Existing relevant files/classes/functions: `rule_version` added to `CropRiskScoreResponse` only (Matrix §B batch 9); `weather_action_rules.py` still carries no version parameter
- Missing component: extend the same `rule_version` field to weather-action outputs — currently only crop-risk (and, per D89-08, weather-alert-rule notifications) carry it
- Required implementation: add a `RULE_VERSION` constant to `weather_action_rules.py` mirroring `crop_risk_v1`/`weather_alert_rules.RULE_VERSION`, surfaced on `WeatherActionResponse`
- Dependencies: none — same pattern already proven twice
- Backend work: `weather_action_rules.py` add `RULE_VERSION`; `weather_action_engine_service.py` thread it into the response
- Database/migration work: none — response-field only, no persistence needed unless D89-08's full history is later built
- Mobile work: none required
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting `WeatherActionResponse.rule_version` is always populated, mirroring `test_model_version_is_always_recorded`
- Verification method: extend `tests/test_weather_actions.py`

### D88-09 — Confidence recorded alongside AI output
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: VERIFIED for AI — `AIAnalysis.confidence` (raw float) + `top_k_predictions` JSONB (ai_analysis.py:89-91), bucketed via `ai/confidence.py`; `test_high_confidence`/`test_medium_confidence`/`test_low_confidence` (test_ai_model_components.py:12-18)
- Missing component: no confidence field at all on weather or market/price schemas
- Required implementation: either document why weather/price are not predictions in the same sense as AI classification (rain probability already functions as weather's confidence analog), or add an explicit `confidence` field to `ReferencePriceResponse` if the checklist insists on a literal field for every data type
- Dependencies: none
- Backend work: alias/clarify existing `rain_probability` as weather's confidence analog in docs; add a schema field for price only if genuinely required
- Database/migration work: none unless a literal price-confidence field is added
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none required if documented as non-applicable; if built, extend `tests/test_weather.py`
- Verification method: documentation clarification, or new schema field plus test if built

### D88-10 — Freshness/staleness flagged
- Domain: 88. Data Provenance
- Current implementation status: Partial
- Existing relevant files/classes/functions: VERIFIED for weather — `is_stale` flag computed and surfaced (`schemas/weather.py:46`); `test_stale_weather_is_flagged_in_notes` (test_weather_actions.py:105)
- Missing component: no freshness/staleness indicator on AI analysis or reference-price data
- Required implementation: add an `is_stale`-equivalent computed flag to `AIAnalysisResponse` (based on `inference_timestamp` age) and to `ReferencePriceResponse` (based on `retrieved_at` age vs `effective_date`)
- Dependencies: none — same computed-flag pattern as weather's `is_stale`
- Backend work: `ai_analysis_service.py`/`price_query_service.py` add staleness computation mirroring `weather_action_engine_service`'s pattern
- Database/migration work: none — computed, not persisted
- Mobile work: surface staleness badge in AI-result and price screens
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: tests asserting stale AI/price data is flagged, not silently served as fresh
- Verification method: extend `tests/test_ai_analysis.py`, `tests/test_prices.py`

### D89-05 — Crop scoping of a rule
- Domain: 89. Rule Versioning
- Current implementation status: Partial
- Existing relevant files/classes/functions: `evaluate_crop_weather_alert(*, crop_name, cultivation_status, ...)` (weather_alert_rules.py:107) accepts crop_name/stage but only interpolates them into message text/dedup key
- Missing component: genuine crop-conditional threshold branching — the actual decision logic (line 117) is identical for every crop
- Required implementation: make wind/rain/heat thresholds crop-specific via a lookup table, falling back to the current global default when a crop has no specific entry
- Dependencies: an authoritative per-crop threshold reference — must not be fabricated; would need a real agronomic source
- Backend work: extend `weather_alert_rules.py` to accept a per-crop threshold map
- Database/migration work: new `crop_weather_thresholds` table (crop_id, metric, threshold), or a static config dict if no DB-driven need
- Mobile work: none
- Automation work: none
- Notification work: none — same categories, different threshold value
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a crop-specific threshold overrides the global default when present
- Verification method: extend `tests/test_weather_alert_rules.py`

### D89-08 — Historical reproducibility of a past rule decision
- Domain: 89. Rule Versioning
- Current implementation status: Partial (delta: was MISSING; the "undecided justification" label is now closed, the underlying gap is not)
- Existing relevant files/classes/functions: per `docs/FINAL_GAP_REPORT.md`'s exact resolution — `Notification.rule_version` is now populated (`weather_alert_rules.RULE_VERSION`) for every weather-alert-rule-triggered notification, mirroring D88-07's `crop_risk_v1` precedent (test: `test_proactive_weather_sweep.py`)
- Missing component: the full versioned/dated threshold-snapshot system (D89-01 rule identifier + D89-02 rule version + D89-03 effective-date-scoping) — a history table letting anyone recompute exactly what a past decision would have been under the threshold set active at that time. This is stated exactly as documented: partially resolved (rule_version populated for weather-alert-rule notifications), but the full rule-versioning system remains future work
- Required implementation: a `RuleVersionSnapshot` table (rule_id, version, effective_from, effective_to, threshold_values JSONB) plus a lookup service resolving "what were the thresholds on date X"
- Dependencies: D89-01 (rule identifier) and D89-02 (rule version) both still MISSING as general concepts — this is their natural full-system predecessor
- Backend work: new `rule_version_service.py`; extend `weather_alert_rules.py`/`crop_risk_service.py` to record which snapshot fired
- Database/migration work: new `rule_version_snapshots` table + FK from `notifications`/risk-score history to the snapshot that produced them
- Mobile work: none — backend only
- Automation work: none — this is a data-modeling gap, not a scheduling gap
- Notification work: none — additive metadata only
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: a test that changes a threshold, then asserts a query for an old date still reproduces the old decision
- Verification method: new `tests/test_rule_versioning.py`

### D90-04 — Notification delivery provider abstraction (push/SMS)
- Domain: 90. Provider Abstraction
- Current implementation status: Partial
- Existing relevant files/classes/functions: `notification_service.py` (writes DB rows only, no send-side abstraction); `services/notifications/__init__.py` empty placeholder package; docstring: "this phase has no background push scheduler"
- Missing component: an actual `NotificationDeliveryProvider` ABC analogous to `WeatherProvider`/`ModelProvider`/`OCRProvider`/`AIProvider`, plus a real or honestly-stubbed implementation
- Required implementation: `NotificationDeliveryProvider(ABC)` with abstract `send(farmer_id, payload) -> DeliveryResult`; a `NotConfiguredDeliveryProvider` stub (mirrors `NotConfiguredWeatherProvider`) returning `delivered=False` until a real FCM/SMS gateway is wired
- Dependencies: a real push (FCM/APNs) or SMS gateway account — none configured, same "free-first" posture as D90-05/06's STT/TTS
- Backend work: new `app/services/notifications/push_provider.py` (ABC) + `not_configured_push_provider.py`; `notification_service.py` calls it best-effort after the DB write, never blocking on it
- Database/migration work: optional nullable `delivered_at`/`delivery_provider` columns on `notifications`
- Mobile work: register for push token, send to backend on login (new endpoint)
- Automation work: none beyond existing notification-creation triggers
- Notification work: this scenario IS the notification-delivery layer itself
- Offline/sync impact: none — push failure should never block or duplicate the in-app row
- Security/RBAC impact: none — additive
- Tests required: unit test asserting `NotConfiguredDeliveryProvider` returns `delivered=False` honestly rather than raising or fabricating success
- Verification method: new `tests/test_notification_delivery_provider.py`

### D91-03 — Input metadata captured
- Domain: 91. AI Governance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `preprocessing_version`, `inference_timestamp`, `processing_time_ms` (ai_analysis.py:106-108)
- Missing component: image EXIF/capture-condition metadata (device, lighting estimate, GPS accuracy)
- Required implementation: extend `PhotoUploadMetadata` (schemas/crop_photo.py:60-84, already captures lat/long) with optional `device_model`/`capture_condition` fields, threaded onto `AIAnalysis`
- Dependencies: none — client already sends some metadata for lat/long validation
- Backend work: `crop_photo_service.py` persist extra fields onto `AIAnalysis`/`CropPhoto`
- Database/migration work: migration adding nullable columns
- Mobile work: `camera_capture_screen.dart` collect and send the extra metadata fields
- Automation work: none
- Notification work: none
- Offline/sync impact: extra fields ride along in the existing manifest/upload payload, no new sync concept
- Security/RBAC impact: none — additive
- Tests required: schema test asserting new fields round-trip
- Verification method: extend `tests/test_crop_photos.py`

### D91-08 — Outcome tracked against a recommendation
- Domain: 91. AI Governance
- Current implementation status: Partial
- Existing relevant files/classes/functions: `treatment_service.get_effectiveness()` (treatment_service.py:108-146), compares before/after `AIAnalysis.result_status` as an outcome proxy
- Missing component: a distinct "was the AI's original call correct" signal, separate from treatment effectiveness
- Required implementation: extend the new D91-07 correction endpoint with an outcome-linkage field back to the specific triggering `AIAnalysis`
- Dependencies: D91-07's new `POST /ai/analysis/{id}/correction` endpoint (now IMPLEMENTED) is the natural attachment point
- Backend work: `treatment_service.py` or the correction endpoint records whether the original AI call was later judged correct
- Database/migration work: add `original_call_judged_correct` (nullable bool) to the correction/feedback table
- Mobile work: none required beyond existing correction UI
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a correction record can express "AI was wrong" distinct from "treatment didn't work"
- Verification method: extend `tests/test_ai_analysis.py` or the new correction-endpoint test file

### D91-09 — False positive tracking
- Domain: 91. AI Governance
- Current implementation status: Partial (delta: was MISSING)
- Existing relevant files/classes/functions: raw false-positive signal now captured via `farmer_correction` (the new D91-07 endpoint); `ai/evaluation.py` still a dormant, dataset-driven framework fed no real data
- Missing component: aggregation/dashboard endpoint turning individual `farmer_correction` rows into a precision/recall-style metric feeding `confidence.py`'s thresholds
- Required implementation: a job/endpoint reading `farmer_correction` rows implying a false positive (AI said diseased, farmer/expert confirmed healthy) and computing an aggregate rate
- Dependencies: sufficient volume of real correction data (just started being captured)
- Backend work: new `ai_evaluation_aggregation_service.py` reading `farmer_correction` rows, feeding `ai/evaluation.py`'s existing `EvaluationReport` with real data instead of synthetic pairs
- Database/migration work: none new — reuses the correction table added for D91-07
- Mobile work: none — backend/admin only
- Automation work: periodic aggregation job on the existing `scheduler.py` (APScheduler), mirroring the Expert SLA sweep pattern
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none if farmer-facing; admin-only if exposed as a dashboard
- Tests required: test asserting the aggregation correctly separates false-positive from false-negative corrections and computes a rate
- Verification method: new `tests/test_ai_evaluation_aggregation.py`

### D91-10 — False negative tracking
- Domain: 91. AI Governance
- Current implementation status: Partial (delta: was MISSING)
- Existing relevant files/classes/functions: same dormant `ai/evaluation.py`, same raw signal now captured via `farmer_correction`
- Missing component: same aggregation gap as D91-09, mirrored for the false-negative direction (AI said healthy, later shown diseased)
- Required implementation: identical mechanism to D91-09, filtering the opposite correction direction
- Dependencies: same as D91-09
- Backend work: shared `ai_evaluation_aggregation_service.py` with D91-09
- Database/migration work: none new
- Mobile work: none — backend/admin only
- Automation work: shared scheduler job with D91-09
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none if farmer-facing; admin-only if exposed as a dashboard
- Tests required: shared test suite with D91-09, asserting the false-negative rate is computed distinctly
- Verification method: same new `tests/test_ai_evaluation_aggregation.py`

### D92-04 — Current crop stages included
- Domain: 92. Farm Brain
- Current implementation status: Partial
- Existing relevant files/classes/functions: `tools.get_crop_status` (tools.py:34-58), covers only a single "most-recently-updated active crop cycle", used at `assistant_extras_service.py:88-90`
- Missing component: farm-wide, all-active-crop-cycles coverage for a multi-crop farm
- Required implementation: extend `get_daily_summary`/`tools.get_crop_status` to iterate all of the farmer's active crop cycles, not just the most recent
- Dependencies: none — `crop_cycle_repository` already supports listing all cycles
- Backend work: `assistant_extras_service.py` loop over `crop_cycle_repository.list_active_for_farmer` instead of a single most-recent lookup
- Database/migration work: none
- Mobile work: none — backend-only text composition
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a multi-crop farm's summary lists every active cycle's stage, not just one
- Verification method: extend `tests/test_assistant_chat.py`

### D92-07 — Market included
- Domain: 92. Farm Brain
- Current implementation status: Partial
- Existing relevant files/classes/functions: `tools.get_buyer_offers` (tools.py:121-137), buyer-offer count only
- Missing component: price/reference-price/market-trend data
- Required implementation: add a `price_query_service` call surfacing the farmer's relevant crop's current reference-price trend
- Dependencies: none — `price_query_service` already exists
- Backend work: `assistant_extras_service.py` add a market-price line, never invented when no price exists for the farmer's crop
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a market line appears only when a real reference price exists (never fabricated)
- Verification method: extend `tests/test_assistant_chat.py`

### D93-03 — Weather actions summarized
- Domain: 93. Daily Farm Brief
- Current implementation status: Partial
- Existing relevant files/classes/functions: `assistant_extras_service.py:77-86` (temperature/rain probability only); `FarmWeatherResponse.crop_action` (schemas/weather.py:50) exists but is not surfaced
- Missing component: the spray-advisory/`crop_action` field
- Required implementation: `tools.get_weather_status` return `crop_action` alongside temp/rain; `get_daily_summary` include it when present
- Dependencies: none — field already exists on the schema
- Backend work: `tools.py:83-101` extend return value; `assistant_extras_service.py:77-86` surface it
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting `crop_action` appears in the daily summary when the weather response carries one
- Verification method: extend `tests/test_assistant_chat.py`

### D93-06 — Crop-stage actions summarized
- Domain: 93. Daily Farm Brief
- Current implementation status: Partial
- Existing relevant files/classes/functions: `assistant_extras_service.py:88-90` (current stage as a status readout only)
- Missing component: a recommended next action tied to the current stage
- Required implementation: a small stage-to-suggested-action lookup, reusing any existing per-stage advisory content or a new lightweight static table — must avoid inventing agronomic claims not already elsewhere in the project
- Dependencies: none identified beyond authoring the stage-action text
- Backend work: `assistant_extras_service.py` add the mapped action text
- Database/migration work: none, or a small static config table
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting each `cultivation_status` maps to a non-empty, non-fabricated action string
- Verification method: extend `tests/test_assistant_chat.py`

### D93-08 — Market summarized
- Domain: 93. Daily Farm Brief
- Current implementation status: Partial
- Existing relevant files/classes/functions: `assistant_extras_service.py:96-98`, buyer-offer count only, same underlying gap as D92-07
- Missing component: price/trend data in the daily brief
- Required implementation: shared fix with D92-07 — add the market-price line to `get_daily_summary`
- Dependencies: none — `price_query_service` already exists
- Backend work: shared with D92-07
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: shared with D92-07's new test
- Verification method: extend `tests/test_assistant_chat.py`

### D96-01 — Compare crop
- Domain: 96. Season Comparison
- Current implementation status: Partial
- Existing relevant files/classes/functions: `crop_comparison_service.py:44` — only `cultivation_status` ("crop_stage") compared, marked `not_directly_comparable`/`equal`
- Missing component: an actual "same crop / different crop" comparability signal — crop identity itself isn't a metric
- Required implementation: add a `same_crop` boolean derived from `CropCycle.crop_id` equality, surfaced alongside the stage comparison
- Dependencies: none — `crop_id` already exists on both cycles
- Backend work: `crop_comparison_service.py` add the derived field
- Database/migration work: none
- Mobile work: surface "comparing across different crops" caveat in the comparison screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting `same_crop` is correctly true/false
- Verification method: extend `tests/test_crop_performance.py`

### D97-02 — Actual quantity captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: new `CropCycleClosureSnapshot.harvest_quantity`/`harvest_quantity_unit`, populated by `crop_cycle_service._create_closure_snapshot` from the linked `HarvestRecord` (`actual_quantity` if harvested, else `estimated_quantity`) at `close_my_crop_cycle` time — consolidated into one shared table rather than a separate `CropCycle` column (see the model's own docstring)
- Missing component: none
- Required implementation: none
- Dependencies: D96-03/D98-02's own disclosed caveat still applies (no production path populates `actual_quantity` yet in real farmer flows) - honestly reflected as `estimated_quantity` fallback, never fabricated
- Backend work: done — `crop_cycle_service.py`, `models/crop_cycle_closure_snapshot.py`
- Database/migration work: done — `b3c4d5e6f7a8_create_crop_cycle_closure_snapshots.py`
- Mobile work: surface captured quantity on the close-cycle confirmation screen (unverified this pass, backend-only re-check)
- Automation work: none
- Notification work: none
- Offline/sync impact: closure request already queues like any other write; no new sync concept
- Security/RBAC impact: none — additive, farmer-owned
- Tests required: `tests/test_crop_cycles.py::test_closing_a_crop_cycle_with_no_harvest_or_finances_creates_an_honest_empty_snapshot` (new), `::test_closing_a_crop_cycle_snapshots_the_linked_harvest_and_ledger` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-03 — Actual quality captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: new `CropCycleClosureSnapshot.quality_grade`/`harvest_status`, shared implementation with D97-02
- Missing component: none
- Required implementation: none
- Dependencies: none beyond D97-02's shared implementation
- Backend work: shared with D97-02's closure-snapshot step
- Database/migration work: shared with D97-02
- Mobile work: surface captured quality grade at close-cycle confirmation (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond existing closure-request queueing
- Security/RBAC impact: none — additive
- Tests required: shared with D97-02's tests
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-04 — Sale captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: new `crop_cycle_closure_snapshots` table (`CropCycleClosureSnapshot`), populated once by `crop_cycle_service._create_closure_snapshot` calling the existing `crop_financial_service.get_financial_summary()` at close time — frozen thereafter, verified by a dedicated test that a later ledger edit never changes the snapshot
- Missing component: none
- Required implementation: none
- Dependencies: `crop_financial_service.get_financial_summary()` (already existed, reused as-is)
- Backend work: done — `crop_cycle_service.py`
- Database/migration work: done — `b3c4d5e6f7a8_create_crop_cycle_closure_snapshots.py`
- Mobile work: closure confirmation screen shows the frozen snapshot (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond existing closure-request queueing
- Security/RBAC impact: none — additive
- Tests required: `tests/test_crop_cycles.py::test_closure_snapshot_stays_frozen_after_a_later_ledger_entry` (new)
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-05 — Revenue captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `CropCycleClosureSnapshot.actual_revenue`, shared implementation with D97-04
- Missing component: none
- Required implementation: none
- Dependencies: shared with D97-04
- Backend work: shared closure-snapshot step
- Database/migration work: shared `crop_cycle_closure_snapshots` table
- Mobile work: shared confirmation-screen display (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: shared with D97-04's tests
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-06 — Costs captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `CropCycleClosureSnapshot.actual_cost`, shared implementation with D97-04
- Missing component: none
- Required implementation: none
- Dependencies: shared with D97-04
- Backend work: shared closure-snapshot step
- Database/migration work: shared `crop_cycle_closure_snapshots` table
- Mobile work: shared confirmation-screen display (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: shared with D97-04's tests
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-07 — Profit captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Partial)
- Existing relevant files/classes/functions: `CropCycleClosureSnapshot.actual_profit_loss`, shared implementation with D97-04
- Missing component: none
- Required implementation: none
- Dependencies: shared with D97-04
- Backend work: shared closure-snapshot step
- Database/migration work: shared `crop_cycle_closure_snapshots` table
- Mobile work: shared confirmation-screen display (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: shared with D97-04's tests
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D98-03 — Previous costs used in learning
- Domain: 98. Historical Learning
- Current implementation status: Partial
- Existing relevant files/classes/functions: `actual_cost_so_far` used only as a raw feature-snapshot field for a future, non-existent ML pipeline (learning_foundation_service.py:49-53)
- Missing component: turning the captured feature into an actual descriptive observation (not a forward recommendation — that is D98-07, correctly FUTURE)
- Required implementation: extend `personalization_service.py`'s descriptive-pattern style (like `_preferred_crop_signal`) with a `_cost_pattern_signal()` describing past cost trends, gated by the same evidence-floor discipline (≥3 events)
- Dependencies: none — same evidence-floor pattern already proven for crop preference
- Backend work: `personalization_service.py` new signal function
- Database/migration work: none — reuses existing `crop_cost_estimates`/`ledger_entries`
- Mobile work: surface in personalization profile screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test mirroring `test_one_treatment_does_not_create_a_strong_permanent_preference` for cost patterns
- Verification method: extend `tests/test_personalization.py`

### D100-14 — Rate limiting
- Domain: 100. Security / Privacy / Audit
- Current implementation status: **PARTIAL, re-verified this session — the two concrete
  gaps this row's own citation named are now CLOSED, but not by this session's own work.**
  Direct re-read this session found `InMemoryRateLimiter` already wired into
  `auth_service.py` (login, request-reset-otp, reset-password) **and**
  `crop_photo_service.py::_upload_limiter` (image upload, 20 requests/300s, keyed by
  `farmer_id`), each with its own passing test — `test_login.py`, `test_reset_password.py`,
  and `test_crop_photos.py::test_upload_is_rate_limited_per_farmer` /
  `::test_upload_rate_limit_is_scoped_per_farmer_not_global` — plus unit-level coverage in
  `test_rate_limit.py`. This closes the specific "not wired into OTP-request or
  image-upload endpoints" gap this row previously cited; that citation is now stale, code
  was fixed by a prior pass this matrix hadn't caught up to.
- Remaining, genuinely-still-PARTIAL gap: not registered as global ASGI middleware (still
  three separate per-call-site limiter instances, not a single cross-cutting policy), and
  still in-memory/single-process — not safe under a multi-instance deployment. This is the
  same class of honestly-disclosed architectural limitation as this project's other
  environment-scale gaps (e.g. D14's live-weather-reachability rows): fixing it needs a
  provisioned Redis instance (or equivalent shared store), which does not exist in this
  project/environment today, so it is not fabricated here.
- Required implementation (if a shared-store deployment is ever provisioned): extend
  `middleware/rate_limit.py` with a pluggable backend (in-memory default, Redis-backed when
  configured) and register it as global ASGI middleware rather than per-call-site opt-in.
- Dependencies: a Redis instance (or equivalent shared store) — none provisioned in this
  project today; not something this session fabricates
- Security/RBAC impact: the concrete, actionable part of this row (per-endpoint throttling
  on the highest-abuse-risk paths: login, OTP request/verify, photo upload) is done and
  tested; the remaining gap is a deployment-scale concern, not an unaddressed code path
- Verification method: automated tests (pre-existing), confirmed passing in the full suite
  re-run this session

## 3. Missing — full itemized (EVERY row, no aggregation)

### D73-01 — Scheme discovery (browse/search available central & state schemes)
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `app/api/v1/*` for a scheme route module (zero hits); no `Scheme` model in `app/models/`
- Missing component: scheme catalog data model, browse/search API, mobile screen
- Required implementation: new `Scheme` model (name, description, department, deadline, source_url) + `GET /schemes`, `GET /schemes/{id}` with search/filter params
- Dependencies: an authoritative scheme dataset (govt-published or manually curated) — no such feed exists in this repo today
- Backend work: `app/models/scheme.py`, `app/repositories/scheme_repository.py`, `app/services/scheme_service.py`, `app/api/v1/schemes.py` (mirrors `reference_price.py`'s catalog-style read pattern)
- Database/migration work: new Alembic migration creating a `schemes` table
- Mobile work: new `mobile/lib/features/schemes/` list/search screen (mirrors existing marketplace list screens)
- Automation work: none — a catalog read is not itself automatable
- Notification work: none (D73-05 covers scheme-specific notifications separately)
- Offline/sync impact: none — read-only catalog, no offline write path needed
- Security/RBAC impact: none — additive read endpoint
- Tests required: catalog CRUD/search tests
- Verification method: new `tests/test_schemes.py`

### D73-02 — Eligibility check against farmer profile (land size, crop, category)
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: eligibility-rule model + evaluation against the farmer's own profile/plot/crop data
- Required implementation: `SchemeEligibilityRule` (land-size range, crop list, category) + `evaluate_eligibility(farmer, scheme)` pure function
- Dependencies: D73-01's `Scheme` model must exist first
- Backend work: `scheme_service.py::check_eligibility`, reusing `Farm`/`Plot`/`CropCycle` data already on file
- Database/migration work: new `scheme_eligibility_rules` table
- Mobile work: eligibility badge on the scheme list/detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-scoped read
- Tests required: eligibility-match unit tests across boundary cases (land-size edges, crop mismatch)
- Verification method: extend `tests/test_schemes.py`

### D73-03 — Required-documents checklist for a scheme
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: a document-requirements list attached to each scheme
- Required implementation: `SchemeDocumentRequirement` (scheme_id, document_name, description)
- Dependencies: D73-01's `Scheme` model
- Backend work: `scheme_service.py` returns the checklist alongside scheme detail
- Database/migration work: new `scheme_document_requirements` table
- Mobile work: checklist display on scheme detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the checklist is returned per scheme
- Verification method: extend `tests/test_schemes.py`

### D73-04 — Application status tracking (submitted/under review/approved/rejected)
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: an application record and a status feed synced from a govt portal
- Required implementation: `SchemeApplication` (farmer_id, scheme_id, status, submitted_at) — status itself would need to mirror an external govt-portal feed this project has no access to; the record-keeping/status-mirror UI is buildable now, the real status sync is not
- Dependencies: a real govt-portal integration for live status (none available) — the record/status-mirror shell can be built without it, defaulting to a manually-entered/self-reported status
- Backend work: `scheme_application_service.py`, `POST/GET /schemes/{id}/applications`
- Database/migration work: new `scheme_applications` table
- Mobile work: application-status screen
- Automation work: none until a real portal feed exists
- Notification work: status-change notification once a feed exists
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-scoped
- Tests required: CRUD tests for application record and status transitions
- Verification method: new `tests/test_scheme_applications.py`

### D73-05 — Notifications for new schemes / deadline reminders
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: `NotificationCategory` enum (notification.py:27-33) has no scheme category, not even as a disclosed future placeholder
- Missing component: a `SCHEME_ALERT` category and a deadline-reminder trigger
- Required implementation: add `SCHEME_ALERT` to `NotificationCategory`; a scheduled job (via `scheduler.py`) checking upcoming scheme deadlines against farmer eligibility
- Dependencies: D73-01/02 (scheme catalog + eligibility) must exist first
- Backend work: extend `notification_service.py::create_alert_notification` call sites; new scheduler job mirroring the Expert SLA/weather-sweep pattern
- Database/migration work: enum migration adding `SCHEME_ALERT`
- Mobile work: none beyond existing notification list rendering
- Automation work: scheduled deadline-check job on `scheduler.py`
- Notification work: this scenario IS the notification itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a deadline-approaching scheme produces exactly one deduplicated notification
- Verification method: new `tests/test_scheme_notifications.py`

### D73-06 — Official-source boundary (never present app-generated scheme info as the govt's own record; never submit on farmer's behalf without redirect)
- Domain: 73. Government Schemes
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — nothing to police since no scheme feature exists
- Missing component: a design guardrail (UI copy + no auto-submission path) that must ship alongside D73-01/04, not retrofitted after
- Required implementation: scheme detail screens always show a "redirect to official portal to apply/verify" affordance; the app never claims to be the authoritative record
- Dependencies: D73-01/04
- Backend work: none — this is a UI/copy discipline, mirrors the project's existing "never fabricate" posture (e.g. `crop_risk_service.py` reporting UNKNOWN rather than inferring)
- Database/migration work: none
- Mobile work: explicit "Apply on official portal" link/redirect on scheme screens; never a fake "Submit" button
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none — this is a design constraint verified by review, not automatable behavior
- Verification method: manual review checklist item when D73-01/04 are built, cross-referenced against this row

### D74-01 — Policy record (view own crop insurance policy details)
- Domain: 74. Crop Insurance
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no `insurance*.py` anywhere in `app/api` or `app/models`
- Missing component: `Policy`/`Insurance` model + read endpoint
- Required implementation: `InsurancePolicy` (policy_number, insurer, sum_insured, premium, crop_id, season) + `GET /farmers/me/insurance-policies`
- Dependencies: policy data would be farmer-entered (self-reported), since no insurer integration exists
- Backend work: `app/models/insurance_policy.py`, `app/services/insurance_service.py`, `app/api/v1/insurance.py`
- Database/migration work: new `insurance_policies` table
- Mobile work: policy detail screen (farmer-entered form + view)
- Automation work: none
- Notification work: none (see D74-05 boundary note)
- Offline/sync impact: none — farmer-entered record like other farm data
- Security/RBAC impact: none — farmer-owned via standard `get_owned` pattern
- Tests required: CRUD + ownership isolation tests
- Verification method: new `tests/test_insurance.py`

### D74-02 — Crop damage record for insurance purposes (loss type, extent, date)
- Domain: 74. Crop Insurance
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: a damage record linked to a crop cycle + policy
- Required implementation: `CropDamageRecord` (crop_cycle_id, policy_id, loss_type, extent_percent, occurred_on)
- Dependencies: D74-01 (policy record), D75's disaster-event model if damage is disaster-triggered
- Backend work: `insurance_service.py::record_damage`
- Database/migration work: new `crop_damage_records` table
- Mobile work: damage-record entry form, reusing existing crop-photo capture as evidence
- Automation work: none
- Notification work: none
- Offline/sync impact: none — farmer-entered, same queueing as other writes if offline support is added later (currently no entity beyond photos has offline queueing, see D81)
- Security/RBAC impact: none — farmer-owned
- Tests required: CRUD tests
- Verification method: extend `tests/test_insurance.py`

### D74-03 — Evidence capture (photos/geotag/timestamp bound to a specific claim)
- Domain: 74. Crop Insurance
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_photo` module (mobile/lib/features/crop_photo/) captures photos for AI disease analysis only — no `claim_id`/`policy_id` field on any photo/analysis record
- Missing component: a claim-linkage field on the existing photo/analysis tables
- Required implementation: add optional `claim_id` FK to `CropPhoto` (or a join table), reusing the existing capture pipeline rather than building a new one
- Dependencies: D74-02 (damage record) or a future claim entity to link to
- Backend work: migration adding nullable `claim_id` to `crop_photos`; `crop_photo_service.py` accept it on upload
- Database/migration work: nullable FK column
- Mobile work: `camera_capture_screen.dart` optionally tag a photo with a claim/damage-record id
- Automation work: none
- Notification work: none
- Offline/sync impact: reuses the existing photo offline queue (`PendingUploadQueue`) — additive metadata field only
- Security/RBAC impact: none — same ownership rules as existing photos
- Tests required: test asserting a photo can be linked to a claim/damage record and is retrievable by it
- Verification method: extend `tests/test_crop_photos.py`

### D74-05 — Claim status tracking (pending/approved/denied, even as a passive mirror of an insurer's status)
- Domain: 74. Crop Insurance
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no feature, not even a read-only status mirror
- Missing component: a status field mirrorable from an insurer feed
- Required implementation: `InsuranceClaim.status` enum (pending/approved/denied), manually updatable until a real insurer feed exists
- Dependencies: a real insurer status feed for genuine automation (none available) — the mirror shell itself doesn't require one
- Backend work: `insurance_service.py::update_claim_status` (manual/admin-entered until integration exists)
- Database/migration work: new `insurance_claims` table with status enum
- Mobile work: claim-status screen
- Automation work: none until a real feed exists
- Notification work: status-change notification once a feed exists
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-owned read; status writes would be admin/insurer-only if automated later
- Tests required: CRUD + status-transition tests
- Verification method: extend `tests/test_insurance.py`

### D75-01 — Flood alert/detection
- Domain: 75. Disaster Management
- Current implementation status: **VERIFIED (fixed this session via the same cumulative-
  rainfall fix as D15-08, was Missing)** — this row's own citation was written before the
  cross-domain reconciliation identified D15-08 (Weather Risk, same finding, same cluster)
  as the identical underlying gap; `weather_snapshots` history turned out to already exist
  and accumulate correctly (confirmed by direct read of `weather_service.py` — CURRENT rows
  are appended per fetch, never overwritten), so "historical rainfall accumulation storage
  does not currently exist" was not accurate. Deliberately reuses `WEATHER_ALERT` rather
  than inventing a new `DISASTER_ALERT`/`FLOOD_ALERT` category — the detection and
  farmer-facing content are identical to D15-08's; a second category for the same
  underlying event would be notification-category proliferation, not a real distinction.
  See `docs/audit/FINAL_CANONICAL_group_A.md`'s D15-08 entry for the full evidence.
- Verification method: automated test (same tests as D15-08), confirmed passing

### D75-02 — Drought alert/detection
- Domain: 75. Disaster Management
- Current implementation status: **VERIFIED (fixed this session via the same consecutive-
  dry-days fix as D15-09, was Missing)** — same reconciliation finding as D75-01: this row's
  "no multi-week deficit aggregation" premise predates identifying D15-09 as the identical
  gap. Deliberately reuses `WEATHER_ALERT`, not a new `DISASTER_ALERT`/`DROUGHT_ALERT`
  category, for the same reason as D75-01. See D15-09's entry above.
- Verification method: automated test (same tests as D15-09), confirmed passing

### D75-03 — Hail alert/detection
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `hail`, zero hits; `WeatherReading` dataclass has no precipitation-type field at all
- Missing component: precipitation-type data from the weather provider
- Required implementation: extend `WeatherReading`/`OpenMeteoProvider` to surface precipitation type if the underlying Open-Meteo API exposes it, then a hail-specific alert rule
- Dependencies: confirming Open-Meteo (or the current provider) actually returns a precipitation-type field
- Backend work: `open_meteo_provider.py` parse precipitation type; new hail rule in `weather_alert_rules.py`
- Database/migration work: none
- Mobile work: none
- Automation work: none beyond existing pull-based weather check
- Notification work: new `hail_alert` message key under `WEATHER_ALERT` or a new `DISASTER_ALERT` category
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit test on precipitation-type parsing and alert trigger
- Verification method: extend `tests/test_weather_alert_rules.py`

### D75-05 — Cyclone alert/detection (named storm system, path/landfall warning)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `cyclone`, zero hits; no IMD cyclone-bulletin ingestion
- Missing component: a cyclone track/warning feed ingestion and alert
- Required implementation: `disaster_event_service.py` (shared with D75-04/01/08) consuming an IMD-equivalent feed
- Dependencies: a real IMD cyclone-bulletin feed — none available
- Backend work: new ingestion adapter + alert rule
- Database/migration work: shared `disaster_events` table
- Mobile work: none beyond existing notification rendering
- Automation work: scheduled bulletin poll via `scheduler.py`
- Notification work: new `DISASTER_ALERT` category, CRITICAL priority
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit tests on bulletin parsing and alert trigger
- Verification method: new `tests/test_disaster_alerts.py`

### D75-08 — Damage detection (automated, from imagery/sensors/reports)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — nearest analog `crop_risk_service.py` explicitly reports "unknown" for anything it can't evidence (crop_risk_service.py:1-17) rather than inferring disaster damage
- Missing component: automated damage inference from imagery/sensors/farmer reports
- Required implementation: a farmer-reported damage form as the realistic near-term implementation (automated imagery/sensor inference would require satellite/IoT domains, both entirely MISSING per D76/D77)
- Dependencies: D76 (satellite) and D77 (IoT) for any genuinely automated detection — neither exists
- Backend work: `disaster_event_service.py::record_farmer_reported_damage` as the buildable subset
- Database/migration work: shared `disaster_events` table with a `reported_by` field (farmer vs automated)
- Mobile work: damage-report form, reusing `crop_photo` capture
- Automation work: none until D76/D77 exist
- Notification work: none directly — see D75-04/06/07 for the alert side
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-owned
- Tests required: test asserting a farmer-reported damage record never claims to be "automated" when it is manual
- Verification method: new `tests/test_disaster_alerts.py`

### D75-09 — Evidence capture (disaster-specific: geotag/timestamp/photo tied to a declared disaster event)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: general `crop_photo` capture exists for disease AI only (see D74-03); no disaster-event entity to link to
- Missing component: a `disaster_event_id` linkage field on photo/analysis records, mirroring D74-03's claim-linkage recommendation
- Required implementation: add optional `disaster_event_id` FK to `CropPhoto`
- Dependencies: D75-08's `disaster_events` table must exist first
- Backend work: migration adding nullable `disaster_event_id` to `crop_photos`
- Database/migration work: nullable FK column
- Mobile work: `camera_capture_screen.dart` optionally tag a photo with a disaster-event id
- Automation work: none
- Notification work: none
- Offline/sync impact: reuses existing photo offline queue, additive metadata only
- Security/RBAC impact: none — same ownership rules as existing photos
- Tests required: test asserting a photo can be linked to a disaster event
- Verification method: extend `tests/test_crop_photos.py`

### D75-10 — Inspection (field-agent/expert on-site disaster inspection workflow)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: existing expert `case_service.py`/case routing (`docs/CASE_ROUTING.md`) handles disease case escalation only; `CaseStatus` enum has no disaster/damage state
- Missing component: a disaster-inspection case type
- Required implementation: extend `CaseType`/`CaseStatus` enums with a disaster-inspection variant, reusing the entire existing case-routing infrastructure (assignment, SLA scheduler, consent)
- Dependencies: D75-08's `disaster_events` table as the thing a case gets opened against
- Backend work: `case_service.py` accept a disaster-event case type; reuse `scheduler.py`'s SLA monitoring for disaster cases too
- Database/migration work: enum extension on `case_type`/`case_status`; FK from `crop_health_case`-equivalent to `disaster_events`
- Mobile work: none beyond existing case-status screens, extended to show disaster case type
- Automation work: none beyond the already-existing SLA scheduler, reused
- Notification work: reuses existing `_notify_case_event` pattern
- Offline/sync impact: none
- Security/RBAC impact: reuses existing expert-scoping (`CaseAssignment`/`PhotoAccessGrant`) pattern — no new access model needed
- Tests required: test asserting a disaster-type case follows the same assignment/SLA rules as a disease case
- Verification method: extend `tests/test_cases.py`

### D75-11 — Recovery (post-disaster recovery guidance/workflow for the farmer)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: recovery advisory content per disaster type
- Required implementation: static advisory content keyed by disaster type, surfaced after a disaster event/alert (similar to D75-06/07's advisory recommendation)
- Dependencies: D75-08's `disaster_events` table
- Backend work: `disaster_event_service.py::get_recovery_guidance(event_type)`
- Database/migration work: none — static content, or a small config table
- Mobile work: recovery-guidance screen linked from the disaster notification
- Automation work: none
- Notification work: none — guidance is pulled, not pushed separately
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting every disaster type maps to non-empty, non-fabricated guidance text
- Verification method: new `tests/test_disaster_alerts.py`

### D75-12 — Insurance boundary (disaster event correctly stopping short of declaring/asserting an insurance claim outcome)
- Domain: 75. Disaster Management
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no disaster-to-insurance linkage exists to overstep the boundary in the first place
- Missing component: a design guardrail to ship alongside D75-08/D74-02 if/when a disaster event is ever linked to an insurance claim
- Required implementation: when D74/D75 linkage is built, the disaster-event record must never itself assert a claim outcome — only ever a farmer-initiated referral to D74-04's OUT_OF_SCOPE claim-adjudication boundary
- Dependencies: D74-02 (damage record), D75-08 (damage detection)
- Backend work: none until the linkage exists — this is a constraint on that future work, not separate code today
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until built — flag for review when D74/D75 linkage is implemented
- Verification method: manual review checklist item at implementation time

### D76-01 — Plot boundary (polygon/geofence per plot, prerequisite for any imagery lookup)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: `Farm`/`Plot` store only a single private point (`latitude`,`longitude` `Numeric(9,6)`, farm.py:50-51, plot.py:45-46; docs/PLOT_MODULE.md:14) — no polygon field, no PostGIS
- Missing component: polygon/multi-point geometry per plot
- Required implementation: add a PostGIS `geometry(Polygon)` column (or a JSON point-array as a lighter-weight interim) to `Plot`, with farmer-drawn boundary capture in the mobile add/edit-plot screen
- Dependencies: PostGIS extension on the Postgres instance (not currently enabled, per single-point-only model)
- Backend work: `plot.py` model change; migration enabling PostGIS; `plot_service.py` accept/validate polygon input
- Database/migration work: `CREATE EXTENSION postgis` + new geometry column migration
- Mobile work: map-based polygon-drawing UI on `add_edit_plot_screen.dart`
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same write pattern as other plot fields (currently no offline queue for plot writes at all, see D81-02)
- Security/RBAC impact: none — same ownership rules as existing plot data
- Tests required: test asserting a polygon persists and round-trips correctly
- Verification method: new `tests/test_plot_boundary.py`

### D76-02 — Vegetation signal (NDVI or similar index per plot)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `ndvi`, `vegetation`, zero hits anywhere
- Missing component: satellite imagery feed + NDVI computation
- Required implementation: `SatelliteProvider` (see D76-06) returning an NDVI value per plot polygon
- Dependencies: D76-01 (plot boundary polygon) as the geometry NDVI would be computed over; a real satellite-imagery API (e.g. Sentinel Hub) — none integrated
- Backend work: `satellite_service.py::get_ndvi(plot_id)`
- Database/migration work: new `ndvi_readings` table (plot_id, value, captured_on)
- Mobile work: NDVI display on plot detail screen
- Automation work: scheduled periodic NDVI pull via `scheduler.py`
- Notification work: none directly (see D76-03 for anomaly alerts)
- Offline/sync impact: none
- Security/RBAC impact: none — farmer-scoped read
- Tests required: unit tests against a fake `SatelliteProvider`
- Verification method: new `tests/test_satellite.py`

### D76-03 — Stress anomaly detection (vegetation-index deviation flags possible crop stress)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: historical NDVI baseline + anomaly threshold
- Required implementation: a rule comparing current NDVI to a rolling baseline, mirroring `weather_alert_rules.py`'s pure-function pattern
- Dependencies: D76-02 (NDVI readings) must exist and accumulate history first
- Backend work: `satellite_alert_rules.py` (new, mirrors `weather_alert_rules.py`)
- Database/migration work: reuses D76-02's `ndvi_readings` table
- Mobile work: none beyond existing notification rendering
- Automation work: scheduled anomaly check via `scheduler.py`
- Notification work: new `SATELLITE_ALERT` category
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit tests on anomaly-threshold logic
- Verification method: new `tests/test_satellite.py`

### D76-04 — Change detection (multi-date imagery diff, e.g. sudden canopy loss)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: none
- Missing component: time-series imagery comparison
- Required implementation: extend D76-02/03's NDVI history with a diff-over-time computation flagging sudden drops
- Dependencies: D76-02 (NDVI readings, accumulated over time)
- Backend work: `satellite_alert_rules.py` extended with a change-detection function
- Database/migration work: none new — reuses `ndvi_readings`
- Mobile work: none
- Automation work: shared scheduler job with D76-03
- Notification work: shared `SATELLITE_ALERT` category
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit tests on diff-threshold logic
- Verification method: extend `tests/test_satellite.py`

### D76-05 — Inspection trigger (satellite anomaly automatically opens a field/expert inspection case)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — would reuse existing `case_service.py` routing if built
- Missing component: a link from a satellite anomaly (D76-03) to the existing case-routing system
- Required implementation: `satellite_alert_rules.py`'s anomaly detection calls `case_service.py::create_case` with a new satellite-anomaly case type, reusing the same assignment/SLA/consent infrastructure as disease cases
- Dependencies: D76-03 (anomaly detection), and a `CaseType` extension mirroring D75-10's recommendation
- Backend work: `case_service.py` accept a satellite-anomaly case type
- Database/migration work: enum extension on `case_type`
- Mobile work: none beyond existing case-status screens
- Automation work: none beyond the existing SLA scheduler, reused
- Notification work: reuses existing `_notify_case_event` pattern
- Offline/sync impact: none
- Security/RBAC impact: reuses existing expert-scoping pattern
- Tests required: test asserting an anomaly automatically creates a case
- Verification method: extend `tests/test_cases.py`

### D76-06 — Provider abstraction (a SatelliteProvider interface analogous to WeatherProvider)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: `app/services/weather/weather_provider.py` (abstract base + `WeatherReading` dataclass) is the exact pattern to mirror; no equivalent exists for satellite
- Missing component: `SatelliteProvider(ABC)` + a `NotConfiguredSatelliteProvider` honest stub + a real implementation (e.g. Sentinel Hub client)
- Required implementation: `SatelliteProvider(ABC)` with abstract `provider_name`/`get_ndvi(polygon, date_range)`, following the exact `WeatherProvider`/`ModelProvider`/`OCRProvider`/`AIProvider` pattern already used four times in this codebase
- Dependencies: a real satellite-imagery API account (none configured)
- Backend work: `app/services/satellite/satellite_provider.py` (ABC) + `not_configured_satellite_provider.py` + `fake_satellite_provider.py` test double
- Database/migration work: none — interface only
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit test asserting `NotConfiguredSatelliteProvider` returns `available=False` honestly, mirroring `test_model_version_is_always_recorded`'s "never fabricate when unconfigured" pattern
- Verification method: new `tests/test_satellite_provider.py`

### D76-07 — Never declare crop failure from satellite signal alone (safety guardrail)
- Domain: 76. Satellite
- Current implementation status: Missing
- Existing relevant files/classes/functions: no satellite feature exists, so the guardrail is trivially unviolated but also unimplemented/unverifiable; `crop_risk_service.py` (reports "unknown" rather than fabricating) and `weather_alert_rules.py` ("never claims certainty from a probability") are the demonstrated patterns this guardrail should follow
- Missing component: an explicit code-level guard that must ship simultaneously with D76-02/03/04, not retrofitted after
- Required implementation: any satellite-anomaly output must be surfaced as a risk *factor* feeding into `crop_risk_service.py` (never a standalone "crop failed" declaration), consistent with how disease/weather factors already work
- Dependencies: D76-02/03 must not ship without this guard built in from day one
- Backend work: `satellite_alert_rules.py` outputs must be typed as a `RiskFactor`, never a terminal failure verdict
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test explicitly asserting no satellite-derived output ever sets a crop-cycle status to a failure state directly
- Verification method: new `tests/test_satellite.py` (this test should exist before D76-02/03 ship, per the priority note)

### D77-01 — Soil moisture (live field-sensor feed)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: `irrigation_intelligence_service.py:11-13` explicitly hardcodes `soil_moisture_available=False` in every response, with a docstring stating this was "confirmed absent from this project by inspection... never silently omitted" — the honest-absence handling itself is correct and should be preserved, not removed, when this is eventually built
- Missing component: live sensor telemetry ingestion
- Required implementation: `IoTProvider` (see D77-06) with a `get_soil_moisture(sensor_id)` method; `irrigation_intelligence_service.py` flips `soil_moisture_available` to `True` only once a real reading is present, never fabricated in the interim
- Dependencies: physical sensor hardware + a telemetry ingestion channel — none exists
- Backend work: `app/services/iot/iot_provider.py` (ABC), real implementation once hardware exists
- Database/migration work: new `soil_moisture_readings` table (sensor_id, farm_id, value, recorded_at)
- Mobile work: soil-moisture display once available
- Automation work: telemetry ingestion job
- Notification work: low-moisture alert once real data exists
- Offline/sync impact: none
- Security/RBAC impact: sensor registration would need farmer-ownership scoping, same `get_owned` pattern
- Tests required: test asserting `soil_moisture_available` stays `False` until a real provider is configured (preserves the existing honest-absence guarantee)
- Verification method: extend `tests/test_irrigation_intelligence.py`

### D77-02 — Temperature (on-farm IoT sensor, distinct from forecast-API temperature)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — all `temperature_c` comes from the Open-Meteo forecast API via `WeatherReading`, never a physical sensor; grepped `weather_station`, `sensor`, zero hits
- Missing component: physical sensor telemetry ingestion for on-farm temperature, distinct from forecast data
- Required implementation: same `IoTProvider` (D77-06) pattern, `get_temperature(sensor_id)`, clearly labelled as sensor-sourced vs. forecast-sourced in any UI that shows both
- Dependencies: physical sensor hardware — none exists
- Backend work: shared `IoTProvider` with D77-01/03/04
- Database/migration work: shared sensor-reading table, or a `metric_type` column on a shared table
- Mobile work: label sensor-sourced temperature distinctly from forecast temperature
- Automation work: telemetry ingestion job
- Notification work: none beyond existing weather alerts (kept distinct)
- Offline/sync impact: none
- Security/RBAC impact: sensor registration ownership scoping
- Tests required: test asserting sensor-sourced and forecast-sourced temperature are never conflated
- Verification method: new `tests/test_iot.py`

### D77-03 — Humidity (on-farm IoT sensor)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: `humidity_percent` on `WeatherReading` is forecast-API data, not a farm sensor
- Missing component: physical humidity sensor telemetry
- Required implementation: same `IoTProvider` pattern as D77-02, `get_humidity(sensor_id)`
- Dependencies: physical sensor hardware
- Backend work: shared `IoTProvider`
- Database/migration work: shared sensor-reading table
- Mobile work: label sensor-sourced humidity distinctly from forecast humidity
- Automation work: telemetry ingestion job
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: sensor registration ownership scoping
- Tests required: shared with D77-02
- Verification method: new `tests/test_iot.py`

### D77-04 — Weather station (on-farm physical station as a data source)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `weather_station`/"weather station", zero hits; only external Open-Meteo API is used
- Missing component: station registration + telemetry ingestion
- Required implementation: `WeatherStation` model (farm_id, station_id, install_date) + telemetry ingestion feeding into the same `IoTProvider`
- Dependencies: physical station hardware
- Backend work: `app/models/weather_station.py`, registration endpoint
- Database/migration work: new `weather_stations` table
- Mobile work: station registration screen
- Automation work: telemetry ingestion job
- Notification work: none directly
- Offline/sync impact: none
- Security/RBAC impact: farmer-owned via `get_owned` pattern
- Tests required: registration + ownership isolation tests
- Verification method: new `tests/test_iot.py`

### D77-05 — Irrigation controller (remote actuation of a physical valve/pump)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: `irrigation_intelligence_service.py` only ever returns a textual recommendation (`DELAY`/`MONITOR`/`IRRIGATE_NOW`/`NO_ACTION`/`UNKNOWN`); it never issues a hardware command; grepped `actuator`, `valve`, `relay`, `mqtt`, zero hits (only unrelated Flutter `TextEditingController` widgets match "Controller")
- Missing component: a hardware command channel
- Required implementation: an `IrrigationActuationProvider` (ABC) distinct from the read-only recommendation service, with an explicit farmer-confirmation gate before any command is sent (see D77-07)
- Dependencies: physical valve/pump hardware with a command interface (MQTT or vendor API) — none exists; this is also a physical-safety-relevant feature that should not be built without the D77-07 consent gate shipping simultaneously
- Backend work: new `app/services/iot/irrigation_actuation_provider.py` (ABC), real implementation only once hardware exists
- Database/migration work: new `irrigation_commands` table (farm_id, command, issued_at, confirmed_by)
- Mobile work: explicit confirmation dialog before sending any command
- Automation work: none — should remain farmer-triggered, not automatic, given the physical-safety stakes
- Notification work: command-result notification
- Offline/sync impact: a command should never be silently queued and replayed later without re-confirmation
- Security/RBAC impact: explicit consent gate required (see D77-07) — this is the one MISSING row in this cluster with real physical-safety implications
- Tests required: test asserting no command is ever sent without an explicit, current farmer confirmation
- Verification method: new `tests/test_irrigation_actuation.py`

### D77-06 — Provider abstraction (an IoTProvider/device-integration interface analogous to WeatherProvider)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: no such module exists anywhere in `app/services/`
- Missing component: `IoTProvider(ABC)` mirroring `WeatherProvider`/`ModelProvider`/`OCRProvider`/`AIProvider`/`SatelliteProvider` (D76-06)
- Required implementation: `IoTProvider(ABC)` with abstract `provider_name`/`get_reading(sensor_id, metric)`, a `NotConfiguredIoTProvider` honest stub, feeding D77-01/02/03/04
- Dependencies: none to build the interface itself; real implementations depend on actual hardware
- Backend work: `app/services/iot/iot_provider.py` (ABC) + `not_configured_iot_provider.py` + `fake_iot_provider.py` test double
- Database/migration work: none — interface only
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit test asserting `NotConfiguredIoTProvider` returns `available=False` honestly
- Verification method: new `tests/test_iot_provider.py`

### D77-07 — Authorization-before-hardware-control (explicit farmer consent gate prior to any actuation command)
- Domain: 77. IoT
- Current implementation status: Missing
- Existing relevant files/classes/functions: no hardware control exists at all, so there is no actuation path to gate yet; the project's existing `ConsentRecord`/`CaseConsent` pattern (domain 100) is the model to reuse
- Missing component: an explicit consent-gate design that must ship with D77-05 on day one, not retrofitted after
- Required implementation: reuse the existing typed/versioned `ConsentRecord` pattern — a dedicated `IRRIGATION_ACTUATION` consent type, required and re-confirmed per command (not a one-time blanket grant), consistent with how `CROP_IMAGE_PROCESSING`/`LOCATION_USAGE` are handled today
- Dependencies: D77-05 (irrigation controller) — this guard must exist before that feature, never after
- Backend work: extend `consent_record.py`'s `ConsentType` enum; `irrigation_actuation_provider.py` checks consent before sending any command
- Database/migration work: enum extension on `consent_records.consent_type`
- Mobile work: explicit per-command confirmation dialog (shared with D77-05)
- Automation work: none — automation must never bypass this gate
- Notification work: none
- Offline/sync impact: none — a command must never be queued offline and silently replayed once connectivity returns without a fresh confirmation
- Security/RBAC impact: this IS the security control — real device actuation is physical-safety-relevant and must never ship without it
- Tests required: test asserting no actuation command is ever sent without a current, matching `ConsentRecord`
- Verification method: new `tests/test_irrigation_actuation.py` (shared with D77-05, gate-specific assertions)

### D78-01 — Task notification
- Domain: 78. Notifications
- Current implementation status: **VERIFIED (fixed this session via the same sweep as
  D9-16/D9-03/D37-04, was Missing)**
- Fix applied exactly as this row's own citation specified: `NotificationCategory.TASK_ALERT`
  (migration `a1b2c3d4e5f6`), a scheduled job (`scheduler.py`'s `task_overdue_alert_sweep`,
  reusing the proven Expert-SLA/weather-sweep pattern) that fires one deduplicated
  notification per overdue task (`task_service.run_overdue_task_alert_sweep`, gated by
  `Task.overdue_alerted_at`). See `docs/audit/FINAL_CANONICAL_group_A.md`'s D9-16 entry for
  the full evidence — this row, D9-16, D9-03, and D37-04 are one cluster, one build.
- Tests: same as D9-16 (`test_tasks.py::test_overdue_sweep_sends_one_alert_and_never_duplicates`,
  `::test_overdue_sweep_ignores_tasks_without_a_due_date`)
- Verification method: automated test, confirmed passing

### D78-03 — Disease notification
- Domain: 78. Notifications
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `ai_analysis_service.py::_run_analysis` now calls the new `_notify_disease_detected` helper when `analysis.result_status == ResultStatus.DISEASE_DETECTED`, firing `NotificationCategory.DISEASE_ALERT` via `notification_service.create_alert_notification`, reusing the existing `ai_result_disease_detected` message template
- Missing component: none
- Required implementation: none
- Dependencies: none
- Backend work: done — `ai_analysis_service.py`
- Database/migration work: none — enum already existed
- Mobile work: none beyond existing notification rendering
- Automation work: none — synchronous with the existing analysis call
- Notification work: this scenario IS the notification itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: `tests/test_ai_analysis.py::test_disease_detected_result_notifies_the_farmer` (new)
- Verification method: automated test (new), confirmed passing in the full 765-test suite re-run this session

### D78-05 — Harvest notification
- Domain: 78. Notifications
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `harvest_service.py`'s existing D47-05 wiring (`_notify_harvest_status` calling `create_alert_notification(category=HARVEST_ALERT, ...)`) already satisfies this row's exact wording — no separate Notifications-domain call site was needed
- Missing component: none
- Required implementation: none - direct re-read confirmed the batch 7/D47-05 fix already fully resolves this row
- Dependencies: D47-05 (VERIFIED)
- Backend work: none - already done
- Database/migration work: none — enum already exists
- Mobile work: none
- Automation work: none
- Notification work: this scenario IS the notification itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none new - `tests/test_harvest.py`/`tests/test_data_privacy.py` already assert `harvest_alert` notifications
- Verification method: direct code read this session (`harvest_service.py:150-171`), confirmed passing in the full 765-test suite re-run

### D78-06 — Market notification
- Domain: 78. Notifications
- Current implementation status: Missing
- Existing relevant files/classes/functions: no `MARKET_ALERT` category exists at all; deliberately excluded per `docs/NOTIFICATION_ARCHITECTURE.md:48-51` ("deliberately excluded rather than added as unused placeholders") — though per Matrix §B batch 6, D59-07 (a related market scenario) was separately reclassified FUTURE, not built
- Missing component: `MARKET_ALERT`/`ORDER_ALERT` categories and their trigger points
- Required implementation: add `MARKET_ALERT` to `NotificationCategory`; wire it to reference-price changes or new buyer offers
- Dependencies: D94-05 (market-changed diffing) would share the same trigger logic
- Backend work: `notification_service.py` new category + call sites in `offer_service.py`/`price_query_service.py`
- Database/migration work: enum migration
- Mobile work: none beyond existing notification rendering
- Automation work: none — synchronous with existing offer/price write paths
- Notification work: this scenario IS the notification itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new dedup + trigger tests
- Verification method: new `tests/test_market_notifications.py`

### D78-07 — Payment notification
- Domain: 78. Notifications
- Current implementation status: **VERIFIED (reclassified this session, was Missing)**
- Direct re-read this session confirms `payment_service.py::_notify_payment_failed` (lines 113-126) fires exactly this: a `NotificationCategory.PAYMENT_ALERT`/`message_key="PAYMENT_FAILED"` notification on payment failure, added for D64-06/D66-04 but satisfying D78-07's exact wording (a farmer-visible payment notification) regardless of which scenario ID originally motivated the code.
- New test added and passing this session: `tests/test_payments.py::test_payment_failure_notifies_the_farmer` asserts a `payment_alert` notification appears via `GET /api/v1/notifications` after a failed payment. No further work required.
- Verification method: automated test (new), confirmed passing in the full suite re-run this session.

### D78-08 — Dispute notification
- Domain: 78. Notifications
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `dispute_service.py::resolve_dispute` now calls the new `_notify_dispute_resolved` helper on both RESOLVED (refunded or not) and REJECTED outcomes, firing the new `NotificationCategory.DISPUTE_ALERT`
- Missing component: none
- Required implementation: none
- Dependencies: none
- Backend work: done — `dispute_service.py`
- Database/migration work: done — `f1a2b3c4d5e6_add_dispute_alert_security_alert_categories.py`
- Mobile work: none
- Automation work: none — synchronous with existing dispute-resolution write path
- Notification work: this scenario IS the notification itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: `tests/test_orders.py::test_dispute_and_admin_resolution_with_refund` (extended) and `::test_rejected_dispute_notifies_the_farmer` (new)
- Verification method: automated test (new/extended), confirmed passing in the full 765-test suite re-run this session

### D78-09 — Stock notification
- Domain: 78. Notifications
- Current implementation status: **VERIFIED (reclassified this session, was Missing)**
- Direct re-read this session confirms `input_inventory_service.py::_check_low_stock` fires a `NotificationCategory.STOCK_ALERT`/`message_key="INPUT_LOW_STOCK"` notification, added for D22-06/D24-08/D24-09 but satisfying D78-09's exact wording (a farmer-visible stock notification) regardless of which scenario ID originally motivated the code.
- Already covered by an existing, passing test: `tests/test_input_inventory.py::test_low_stock_alert_fires_once_then_stays_quiet_until_restocked` directly asserts `stock_alert` notification creation, dedup-on-repeat, and re-alert-on-restock-then-drop. No further work required.
- Verification method: automated test (pre-existing), confirmed passing in the full suite re-run this session.

### D78-10 — Soil notification
- Domain: 78. Notifications
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no soil-data feature exists anywhere in the repo
- Missing component: an entire soil-data domain to notify about (structurally blocked, same as D20-14's FUTURE reclassification in the wider gap report)
- Required implementation: N/A until Soil Testing (a domain outside this group) is built
- Dependencies: the entire Soil Testing domain (D20-01..14, domain 20, outside this group)
- Backend work: none until the dependency exists
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: would reuse the same `create_alert_notification` pattern once soil data exists
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until the dependency exists
- Verification method: revisit once Soil Testing is built

### D78-11 — Disaster notification
- Domain: 78. Notifications
- Current implementation status: Missing
- Existing relevant files/classes/functions: extreme heat/cold/high-wind are folded into the generic `WEATHER_ALERT` category (weather_alert_rules.py:65-104); no flood/drought/cyclone-specific "disaster" concept exists
- Missing component: a distinct `DISASTER_ALERT` category, separate from `WEATHER_ALERT`
- Required implementation: shared with D75-01/02/04/05/06/07's `disaster_event_service.py` recommendation — once built, its alerts should use a new `DISASTER_ALERT` category rather than reusing `WEATHER_ALERT`, so this notification-domain scenario and the disaster-domain scenarios resolve together
- Dependencies: D75 domain build-out
- Backend work: shared with D75's recommendations
- Database/migration work: enum migration adding `DISASTER_ALERT`
- Mobile work: none beyond existing notification rendering
- Automation work: shared with D75
- Notification work: this scenario IS the category-separation itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting flood/drought/cyclone alerts use `DISASTER_ALERT`, not `WEATHER_ALERT`
- Verification method: extend `tests/test_disaster_alerts.py` (shared with D75)

### D78-12 — Sync notification
- Domain: 78. Notifications
- Current implementation status: Missing
- Existing relevant files/classes/functions: `sync_coordinator.dart` never calls any notification API on sync success/failure (confirmed by grep)
- Missing component: a farmer-facing "your queued photo synced" / "failed to sync" signal
- Required implementation: `SyncCoordinator` calls a new lightweight local (in-app, not backend-notification-table) signal on terminal states (`uploaded`, `failed`, `needsManualAction`), reusing the same UI surface recommended for D82-06's sync-status badge rather than inventing a separate backend notification round-trip for a purely device-local event
- Dependencies: D82-06 (sync status UI) — natural shared implementation
- Backend work: none — this is a device-local signal, not a server notification
- Database/migration work: none
- Mobile work: `sync_coordinator.dart` triggers a local snackbar/badge update on terminal queue-item states; wire into D82-06's status UI
- Automation work: none
- Notification work: local/in-app only, no backend `Notification` row needed for a device-local sync event
- Offline/sync impact: this scenario IS part of the offline/sync visibility gap (shared with D82-06/D87-02)
- Security/RBAC impact: none
- Tests required: widget test asserting a terminal queue state triggers the local signal
- Verification method: extend the new `test/features/crop_photo/crop_photo_list_screen_test.dart` (shared with D82-06)

### D78-13 — Security notification
- Domain: 78. Notifications
- Current implementation status: PARTIAL (this continuation session, was Missing) — password-change half VERIFIED, new-device-login half genuinely not built
- Existing relevant files/classes/functions: `auth_service.py`'s `change_password` and `reset_password` now both call the new `_notify_password_changed` helper, firing the new `NotificationCategory.SECURITY_ALERT` (CRITICAL priority, not gated by any preference toggle), scoped to the farmer role only (matching `NotificationPreference`'s "one row per farmer" design)
- Missing component: new-device/new-context login alerting - genuinely not built. Confirmed by grep: `RefreshToken` has no `user_agent`/`ip_address`/`device_id` column anywhere, so there is no device/session fingerprinting concept to alert on. Building it would mean adding an entire device-tracking feature, not wiring an existing trigger point - out of this row's original "small" sizing
- Required implementation: (remaining) add device/session fingerprinting to `RefreshToken` (or a new `LoginSession` model) before a genuine "new device" signal can exist; deliberately not fabricated here
- Dependencies: none for the password-change half (done); a new device-tracking model for the login half
- Backend work: done for password-change; login-alert half remains
- Database/migration work: done — `f1a2b3c4d5e6_add_dispute_alert_security_alert_categories.py` (adds `SECURITY_ALERT`); a further migration would be needed for device tracking
- Mobile work: none beyond existing notification rendering
- Automation work: none — synchronous with existing password-change flow
- Notification work: this scenario IS the notification itself (password-change half)
- Offline/sync impact: none
- Security/RBAC impact: directly security-relevant — closes the password-change half of the gap (farmer now knows if their own account's password changed); the new-device-login half remains open
- Tests required: `tests/test_change_password.py::test_changing_password_notifies_the_farmer` (new), `tests/test_reset_password.py::test_reset_password_notifies_the_farmer` (new)
- Verification method: automated test (new), confirmed passing in the full 765-test suite re-run this session

### D79-04 — Expiry
- Domain: 79. Notification Dedup
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no TTL/expiry field on `Notification`, no archival job, no scheduler at all existed when this cluster was written (confirmed by grep of `notification.py`, `notification_service.py`, `notification_repository.py`)
- Missing component: a TTL/expiry concept so notifications don't accumulate forever
- Required implementation: add `expires_at` (nullable) to `Notification`; a scheduled archival/soft-delete job on `scheduler.py` (now that it exists, per the P0 batch) removing or hiding expired rows
- Dependencies: `scheduler.py` (APScheduler) already exists, added for Expert SLA/weather sweeps — this can now reuse it rather than needing a new scheduling mechanism from scratch
- Backend work: `notification_service.py` set `expires_at` at creation (category-specific default, e.g. weather alerts expire in 48h); new `notification_expiry_sweep_service.py` on `scheduler.py`
- Database/migration work: migration adding nullable `expires_at` column
- Mobile work: hide expired notifications from the default list view
- Automation work: scheduled sweep job
- Notification work: this scenario IS the expiry mechanism itself
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting an expired notification is excluded from the default list but not physically deleted (audit trail preserved)
- Verification method: new `tests/test_notification_expiry.py`

### D81-01 — Farm offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: `farm_repository.dart` calls `ApiClient` directly with no local queue (confirmed by reading the file)
- Missing component: an offline write queue for farm create/edit, analogous to `PendingUploadQueue`
- Required implementation: a generic `PendingWriteQueue<T>` abstraction extracted from `PendingUploadQueue`'s proven pattern (enqueue/retry/status/manifest-persistence), specialized for farm create/edit payloads
- Dependencies: this is the first of seven identical-shaped gaps (D81-01..07/09) — recommend building the generic queue once and reusing it, rather than seven bespoke queues
- Backend work: none — farm create/edit endpoints already support idempotent retry via normal validation; no server change needed
- Database/migration work: none
- Mobile work: `farm_repository.dart` route writes through the new generic queue instead of `ApiClient` directly
- Automation work: none — reuses `SyncCoordinator`'s existing connectivity-triggered retry loop, generalized
- Notification work: none directly (shared with D78-12's sync-status signal once built)
- Offline/sync impact: this scenario IS the offline/sync gap itself
- Security/RBAC impact: none — same ownership rules as the existing online path
- Tests required: unit tests mirroring `pending_upload_queue_test.dart`'s structure, generalized
- Verification method: new `test/core/pending_write_queue_test.dart`

### D81-02 — Plot offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: `plot_repository.dart`, same direct-`ApiClient` pattern as D81-01
- Missing component: same generic offline queue gap
- Required implementation: same generic `PendingWriteQueue<T>` (shared build with D81-01), specialized for plot payloads
- Dependencies: D81-01's generic queue
- Backend work: none
- Database/migration work: none
- Mobile work: `plot_repository.dart` route through the shared generic queue
- Automation work: none — shared `SyncCoordinator` generalization
- Notification work: none directly
- Offline/sync impact: shared gap with D81-01
- Security/RBAC impact: none
- Tests required: shared test suite, plot-specific payload cases
- Verification method: extend `test/core/pending_write_queue_test.dart`

### D81-03 — Crop offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: crop-cycle repository, same direct-`ApiClient` pattern
- Missing component: same generic offline queue gap
- Required implementation: same shared `PendingWriteQueue<T>`, specialized for crop-cycle payloads
- Dependencies: D81-01's generic queue
- Backend work: none
- Database/migration work: none
- Mobile work: crop-cycle repository route through the shared generic queue
- Automation work: none
- Notification work: none directly
- Offline/sync impact: shared gap with D81-01
- Security/RBAC impact: none
- Tests required: shared test suite, crop-cycle-specific payload cases
- Verification method: extend `test/core/pending_write_queue_test.dart`

### D81-04 — Task offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: `task_repository.dart` calls `ApiClient` directly
- Missing component: same generic offline queue gap
- Required implementation: same shared `PendingWriteQueue<T>`, specialized for task-create/complete payloads
- Dependencies: D81-01's generic queue
- Backend work: none
- Database/migration work: none
- Mobile work: `task_repository.dart` route through the shared generic queue
- Automation work: none
- Notification work: none directly
- Offline/sync impact: shared gap with D81-01
- Security/RBAC impact: none
- Tests required: shared test suite, task-specific payload cases
- Verification method: extend `test/core/pending_write_queue_test.dart`

### D81-05 — Observation offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: no `Observation`/diary model exists at all in `backend/app/models` (confirmed by direct file search); only ever a documented future intent (`docs/OFFLINE_ARCHITECTURE.md:27` "diary entries")
- Missing component: the entity itself doesn't exist, so offline support for it structurally cannot exist yet
- Required implementation: N/A until an `Observation`/diary entity is built (a new backend domain, not just a mobile queueing gap like its siblings)
- Dependencies: a new `Observation` model/API — genuinely absent, not just unqueued
- Backend work: `app/models/observation.py`, `app/services/observation_service.py`, `app/api/v1/observations.py`, once prioritized
- Database/migration work: new `observations` table
- Mobile work: new observation-entry screen + the shared `PendingWriteQueue<T>` for offline capture
- Automation work: none
- Notification work: none
- Offline/sync impact: this row is blocked on the entity existing before offline queueing is even meaningful
- Security/RBAC impact: none — farmer-owned via standard pattern
- Tests required: entity CRUD tests first, then offline-queue tests shared with D81-01..07/09
- Verification method: new `tests/test_observations.py`

### D81-06 — Expense offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: ledger/expense screens call `ApiClient` directly, no queue
- Missing component: same generic offline queue gap
- Required implementation: same shared `PendingWriteQueue<T>`, specialized for ledger/expense payloads
- Dependencies: D81-01's generic queue
- Backend work: none
- Database/migration work: none
- Mobile work: ledger/expense repository route through the shared generic queue
- Automation work: none
- Notification work: none directly
- Offline/sync impact: shared gap with D81-01
- Security/RBAC impact: none
- Tests required: shared test suite, expense-specific payload cases
- Verification method: extend `test/core/pending_write_queue_test.dart`

### D81-07 — Harvest offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: harvest recording screens call `ApiClient` directly, no queue
- Missing component: same generic offline queue gap
- Required implementation: same shared `PendingWriteQueue<T>`, specialized for harvest-record payloads
- Dependencies: D81-01's generic queue
- Backend work: none
- Database/migration work: none
- Mobile work: harvest repository route through the shared generic queue
- Automation work: none
- Notification work: none directly
- Offline/sync impact: shared gap with D81-01
- Security/RBAC impact: none
- Tests required: shared test suite, harvest-specific payload cases
- Verification method: extend `test/core/pending_write_queue_test.dart`

### D81-09 — Notes offline
- Domain: 81. Offline
- Current implementation status: Missing
- Existing relevant files/classes/functions: no standalone "Notes" entity/model exists anywhere in the backend (confirmed by file search)
- Missing component: same structural gap as D81-05 — entity doesn't exist yet
- Required implementation: N/A until a "Notes" entity is built (may be the same entity as D81-05's Observation/diary, worth unifying rather than building twice)
- Dependencies: same as D81-05 — recommend a single unified Observation/Note entity rather than two
- Backend work: shared with D81-05 if unified
- Database/migration work: shared with D81-05 if unified
- Mobile work: shared with D81-05 if unified
- Automation work: none
- Notification work: none
- Offline/sync impact: blocked on the entity existing, same as D81-05
- Security/RBAC impact: none — farmer-owned via standard pattern
- Tests required: shared with D81-05 if unified
- Verification method: new `tests/test_observations.py` (shared with D81-05)

### D83-02 — Exponential/backoff strategy
- Domain: 83. Retry
- Current implementation status: Missing
- Existing relevant files/classes/functions: `sync_coordinator.dart:38-64`, read in full — no `Duration`, `Timer`, or backoff math anywhere; `syncNow()` retries immediately on every connectivity event with zero throttling
- Missing component: exponential/backoff delay between automatic retry attempts
- Required implementation: add a backoff calculation (e.g. `min(2^retryCount * baseDelay, maxDelay)`) gating `syncNow()`'s automatic retries, so connectivity flapping doesn't trigger rapid repeated attempts
- Dependencies: none — purely additive to existing `sync_coordinator.dart`
- Backend work: none — mobile-only concern
- Database/migration work: none
- Mobile work: `sync_coordinator.dart` add a `Duration`-based backoff check before each automatic retry attempt, using `retryCount` already tracked on `PendingUpload`
- Automation work: none — this IS the automation-throttling fix
- Notification work: none
- Offline/sync impact: this scenario IS an offline/sync reliability gap
- Security/RBAC impact: none
- Tests required: new test asserting rapid connectivity flapping doesn't trigger back-to-back attempts within the backoff window
- Verification method: new `sync_coordinator_test.dart` (does not exist today — shared need with D82-02/D83-01/03's other untested coordinator logic)

### D89-01 — Rule identifier
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — rules are identified only by Python function name (`assess_spray_conditions`, `evaluate_rain_alerts`, `_disease_recurrence_factor`, etc.); no `rule_id`/`RuleVersion` model exists
- Missing component: a stable identifier per rule, independent of its function/file name
- Required implementation: a `RULE_ID` constant per rule module (e.g. `weather_alert_rules.RULE_ID = "weather_alert_v1"`), the natural predecessor to D89-02's version and D89-08's full history
- Dependencies: none
- Backend work: add `RULE_ID` constants across `weather_action_rules.py`, `weather_alert_rules.py`, `crop_risk_service.py`
- Database/migration work: none until persisted (see D89-08)
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting every rule module exposes a non-empty `RULE_ID`
- Verification method: new `tests/test_rule_versioning.py` (shared with D89-02/07/08)

### D89-02 — Rule version
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — zero matches for `rule_version`/`RULE_VERSION`/`RuleVersion` anywhere in `backend/app` at the time this cluster was written; note D88-07/D89-08 have since added `RULE_VERSION` to `crop_risk_service.py`/`weather_alert_rules.py` specifically (per the deltas above) — this row (the general concept as a checklist item) should be re-scored once that partial rollout is complete across all rule modules
- Missing component: `RULE_VERSION` on `weather_action_rules.py` (still absent per D88-07's own note)
- Required implementation: same as D88-07's recommendation — add `RULE_VERSION` to the one remaining rule module
- Dependencies: none — pattern already proven twice
- Backend work: `weather_action_rules.py` add `RULE_VERSION`
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: shared with D88-07's test
- Verification method: extend `tests/test_weather_actions.py`

### D89-03 — Effective date scoping of a rule
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: thresholds are single current `Settings` values (`app/core/config.py:84-89`, e.g. `weather_rain_probability_threshold: float = 40.0`), no dated/versioned threshold table
- Missing component: a date range a given threshold set was in force
- Required implementation: part of D89-08's full `RuleVersionSnapshot` system (effective_from/effective_to columns)
- Dependencies: D89-08's full system
- Backend work: shared with D89-08
- Database/migration work: shared `rule_version_snapshots` table
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: shared with D89-08
- Verification method: shared `tests/test_rule_versioning.py`

### D89-04 — Region scoping of a rule
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: no rule function takes a region argument; thresholds are global
- Missing component: region-conditional threshold branching
- Required implementation: extend the same per-crop threshold-lookup mechanism proposed for D89-05 with a region dimension, using the already-seeded Mandal/Village master data
- Dependencies: D89-05's crop-scoping work (natural shared implementation), Mandal/Village master data (already seeded)
- Backend work: extend the threshold-lookup table with a region key
- Database/migration work: shared with D89-05's proposed threshold table
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a region-specific threshold overrides the global default when present
- Verification method: extend `tests/test_weather_alert_rules.py`

### D89-06 — Crop-stage scoping of a rule
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: `cultivation_status` passed through as a display string only; no stage-conditional branch anywhere in `weather_action_rules.py`/`weather_alert_rules.py`/`crop_risk_service.py`
- Missing component: stage-conditional threshold logic
- Required implementation: extend the per-crop threshold-lookup mechanism (D89-05) with a stage dimension (e.g. flowering-stage crops more sensitive to heat than seedling-stage)
- Dependencies: D89-05's crop-scoping work, an authoritative per-stage sensitivity reference (must not be fabricated)
- Backend work: extend the threshold-lookup table with a stage key
- Database/migration work: shared with D89-05
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a stage-specific threshold overrides the default when present
- Verification method: extend `tests/test_weather_alert_rules.py`

### D89-07 — Audit of which rule/version fired
- Domain: 89. Rule Versioning
- Current implementation status: Missing
- Existing relevant files/classes/functions: no `AuditLogger` call exists in `weather_action_rules.py`, `weather_alert_rules.py`, or `crop_risk_service.py`; contrast with `payment_service.py:40,62,66`, which does audit-log, showing the pattern exists elsewhere but isn't applied here
- Missing component: an audit-log entry naming the rule+version that fired
- Required implementation: add `AuditLogger(db).log("RULE_EVALUATED", ..., entity="rule", entity_id=rule_id_and_version)` at the point a rule produces a notification/risk-factor, reusing the exact `AuditLogger` pattern from `payment_service.py`
- Dependencies: D89-01/02 (rule identifier + version) must exist first to have something meaningful to log
- Backend work: `weather_alert_orchestration_service.py`/`crop_risk_service.py` call `AuditLogger` at rule-firing time
- Database/migration work: none — reuses the existing `audit_logs` table
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive audit trail
- Tests required: test asserting an `AuditLog` row is written with the correct rule_id/version when a rule fires
- Verification method: extend `tests/test_weather_alert_rules.py`/`tests/test_crop_risk.py`

### D90-02 — Market provider abstraction
- Domain: 90. Provider Abstraction
- Current implementation status: Missing
- Existing relevant files/classes/functions: `price_comparison.py`/`price_query_service.py` operate purely on `ReferencePrice` DB rows (admin/dealer-entered); no `MarketProvider` ABC, nothing pluggable, no live external market-price API call anywhere
- Missing component: architecting the existing DB-backed feature as a swappable provider interface the way Weather/AI/OCR/AI-assistant already are
- Required implementation: `MarketProvider(ABC)` with abstract `get_reference_price(product_id/crop_id, region)`; a `DatabaseMarketProvider` implementation wrapping the current `ReferencePrice` query (so today's real, working feature becomes the first concrete implementation, not a stub), leaving room for a future live-API-backed implementation
- Dependencies: none — this is a refactor of an existing working feature into the established interface shape, not new functionality
- Backend work: `app/services/market/market_provider.py` (ABC) + `database_market_provider.py`; `price_query_service.py` calls through the interface instead of the DB directly
- Database/migration work: none — same underlying table
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting `DatabaseMarketProvider` produces identical results to the current direct-query path (non-regression)
- Verification method: new `tests/test_market_provider.py`

### D90-03 — Maps/geocoding provider abstraction
- Domain: 90. Provider Abstraction
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `maps_provider`/`geocod`/`MapsProvider`/`reverse_geocode`, zero real hits; location handling is static Mandal/Village master data, not live geocoding
- Missing component: any geocoding capability at all
- Required implementation: `MapsProvider(ABC)` with abstract `reverse_geocode(lat, lng)`/`geocode(address)`; a `NotConfiguredMapsProvider` honest stub until a real geocoding API (e.g. an OSM-based service) is configured
- Dependencies: a real geocoding API account — none configured; must respect the same "free-first" posture as other providers
- Backend work: `app/services/maps/maps_provider.py` (ABC) + `not_configured_maps_provider.py`
- Database/migration work: none — interface only
- Mobile work: none until a real implementation exists
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: unit test asserting the stub returns `available=False` honestly
- Verification method: new `tests/test_maps_provider.py`

### D90-08 — Satellite/NDVI provider abstraction
- Domain: 90. Provider Abstraction
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — grepped `satellite`/`ndvi`/`remote_sensing`, zero hits
- Missing component: this is the same gap as D76-06, audited from the Provider-Abstraction-domain angle
- Required implementation: identical to D76-06's recommendation — `SatelliteProvider(ABC)` + `NotConfiguredSatelliteProvider`
- Dependencies: shared with D76-06 — build once, satisfies both scenario IDs
- Backend work: shared with D76-06
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: shared with D76-06
- Verification method: shared `tests/test_satellite_provider.py`

### D92-09 — Priority calculation across all of the above
- Domain: 92. Farm Brain
- Current implementation status: Missing
- Existing relevant files/classes/functions: lines are appended in a fixed hardcoded order (weather→crop→harvest→offers→delivery→expert→overdue-tasks); no sort/scoring function exists (`assistant_extras_service.py:75-125`)
- Missing component: a ranking/scoring function ordering the summary by actual urgency rather than a fixed hardcoded sequence
- Required implementation: a `_priority_score(line_type, severity)` function reordering the composed lines — e.g. a CRITICAL disease alert should outrank a routine harvest-approaching note even though "harvest" is hardcoded earlier today
- Dependencies: D92-01/02/06/08 (now VERIFIED per the Daily Brief batch) provide the individual data lines this would reorder
- Backend work: `assistant_extras_service.py` add a scoring/sort step before composing the final text
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a CRITICAL-severity line always appears before a LOW-severity line regardless of hardcoded category order
- Verification method: extend `tests/test_assistant_chat.py`

### D93-05 — Irrigation summarized
- Domain: 93. Daily Farm Brief
- Current implementation status: Missing
- Existing relevant files/classes/functions: no irrigation concept exists in `tools.py`/`assistant_extras_service.py` at all (zero "irrigation" string matches in either file), despite `irrigation_intelligence_service.py` existing elsewhere (Phase 38) and simply not being wired in
- Missing component: an irrigation-recommendation line in the daily brief
- Required implementation: add a `tools.get_irrigation_status` wrapping the existing `irrigation_intelligence_service.py`, called from `get_daily_summary` only when a recommendation other than `NO_ACTION`/`UNKNOWN` exists
- Dependencies: none — `irrigation_intelligence_service.py` already exists and is reusable as-is
- Backend work: `tools.py` new function; `assistant_extras_service.py` add the line
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting an irrigation line appears only when a real, non-trivial recommendation exists (never fabricated)
- Verification method: extend `tests/test_assistant_chat.py`

### D94-01 — Weather changed since last check
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: no diff/delta logic anywhere; weather is computed live each call, rule-triggered notifications fire on threshold crossing, not on "changed since you last looked"
- Missing component: a stored-snapshot diff, distinct from the existing threshold-crossing alert
- Required implementation: reuse D94-08's now-VERIFIED `FarmerProfile.last_daily_summary_snapshot`/`last_daily_summary_at` mechanism — extend its diffing to include a weather-specific "temperature changed by X° / rain probability changed by Y%" line, rather than building a separate weather-only diff system
- Dependencies: D94-08's existing snapshot infrastructure (now VERIFIED) is the natural extension point
- Backend work: extend `get_daily_summary`'s existing diff logic (per D94-08) with a weather-specific comparison
- Database/migration work: none — reuses `FarmerProfile.last_daily_summary_snapshot`
- Mobile work: none
- Automation work: none
- Notification work: none — this is a pull-based "what changed" view, not a new push
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a weather-changed line appears only when the new reading differs meaningfully from the snapshot
- Verification method: extend `tests/test_assistant_chat.py` (alongside D94-08's existing test)

### D94-02 — Crop stage changed
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: status transitions are stored (`crop_cycle_service.py`, `ALLOWED_TRANSITIONS`) but nothing surfaces "stage changed since you last opened the app"
- Missing component: a stage-change line in the "what changed" view
- Required implementation: extend D94-08's diff mechanism with a stage-comparison line
- Dependencies: D94-08's existing snapshot infrastructure
- Backend work: extend `get_daily_summary`'s diff logic
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a stage-change line appears only when `cultivation_status` differs from the snapshot
- Verification method: extend `tests/test_assistant_chat.py`

### D94-03 — Risk changed
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_risk_service.get_risk_score()` (crop_risk_service.py:32) is stateless/computed fresh on every read, nothing persisted to diff against
- Missing component: a persisted prior risk score to compare against
- Required implementation: extend `FarmerProfile.last_daily_summary_snapshot` (D94-08) to also capture the last-seen risk score per crop cycle, or a small `risk_score_snapshots` table if per-crop-cycle granularity is needed beyond what the daily-summary snapshot already stores
- Dependencies: D94-08's snapshot infrastructure
- Backend work: extend the snapshot/diff mechanism with a risk-score field
- Database/migration work: possibly a new `risk_score_snapshots` table if the daily-summary snapshot's granularity isn't sufficient
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a risk-changed line appears only when the score category (e.g. LOW→HIGH) actually shifts
- Verification method: extend `tests/test_assistant_chat.py`

### D94-04 — Task changed
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: only current overdue-count surfaced in daily summary, no delta/history feed
- Missing component: a "N tasks completed / N new tasks" delta line
- Required implementation: extend D94-08's diff mechanism with a task-count comparison
- Dependencies: D94-08's snapshot infrastructure
- Backend work: extend `get_daily_summary`'s diff logic
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a task-delta line reflects real completed/created counts since the last snapshot
- Verification method: extend `tests/test_assistant_chat.py`

### D94-05 — Market changed
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: no price-change/offer-change delta concept anywhere
- Missing component: a market-delta line
- Required implementation: extend D94-08's diff mechanism with a price/offer-count comparison, sharing the underlying data source recommended for D92-07/D93-08's market-line fix
- Dependencies: D94-08's snapshot infrastructure, D92-07's market-data wiring
- Backend work: extend `get_daily_summary`'s diff logic
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a market-delta line reflects real price/offer changes
- Verification method: extend `tests/test_assistant_chat.py`

### D94-06 — Expert responded
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: no dedicated "expert responded" `NotificationCategory` exists (categories are WEATHER_ALERT/RAIN_ALERT/HEAVY_RAIN_ALERT/CROP_ALERT/DISEASE_ALERT/HARVEST_ALERT/STOCK_ALERT/PAYMENT_ALERT); expert case status is pull-only via `tools.get_expert_case_status`
- Missing component: a push event on case-review completion
- Required implementation: `case_service.py:238`'s existing `_notify_case_event(db, case, "CASE_REVIEWED", ...)` call (per D78-04, already IMPLEMENTED) already creates a notification using `CROP_ALERT` — this "what changed" scenario would surface that same event in the diff-based view too, rather than needing a wholly separate mechanism
- Dependencies: D78-04's existing notification (reuse, not rebuild) + D94-08's snapshot infrastructure for the diff-view angle
- Backend work: extend `get_daily_summary`'s diff logic to include recent `CASE_REVIEWED`-category notifications since the last snapshot
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none new — reuses D78-04's existing notification
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a recently-reviewed case appears in the "what changed" view
- Verification method: extend `tests/test_assistant_chat.py`

### D94-07 — Payment changed
- Domain: 94. What Changed
- Current implementation status: Missing
- Existing relevant files/classes/functions: no payment-status-change notification or diff; order/delivery status is pull-only via `tools.get_delivery_status`/`get_my_orders`
- Missing component: a push/diff event on payment or order status change
- Required implementation: extend D94-08's diff mechanism with a payment/order-status comparison; if D78-07's payment-notification gap (flagged for re-audit above) is resolved first, reuse that same event here too
- Dependencies: D94-08's snapshot infrastructure; possibly D78-07's resolution
- Backend work: extend `get_daily_summary`'s diff logic
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none new if D78-07 already covers the underlying event
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting a payment/order status change appears in the "what changed" view
- Verification method: extend `tests/test_assistant_chat.py`

### D95-04 — Pest risk factor
- Domain: 95. Risk Dashboard
- Current implementation status: Missing
- Existing relevant files/classes/functions: the disease-detection factor doesn't distinguish pest from disease; no separate pest factor exists among the 6-7 factors computed (`crop_risk_service.py` lines 38-48)
- Missing component: a distinct pest-vs-disease signal — structurally blocked on Pest not being modeled as distinct from Disease anywhere in the AI pipeline (per the Gap Report's own "Pest is not modeled as distinct from Disease" note, D28-*)
- Required implementation: N/A until the AI model/vision pipeline distinguishes pest from disease classes (a much larger dependency than the risk-score computation itself)
- Dependencies: D28-* (pest-vs-disease AI classification, domain 28, outside this group)
- Backend work: `crop_risk_service.py` would add a `_pest_factor` once the underlying classification exists
- Database/migration work: none until the dependency is built
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until the dependency exists
- Verification method: revisit once pest-vs-disease AI classification exists

### D95-05 — Water/irrigation risk factor
- Domain: 95. Risk Dashboard
- Current implementation status: Missing
- Existing relevant files/classes/functions: `irrigation_intelligence_service.py` (Phase 38) computes irrigation recommendations separately but is never reused as a risk-score factor; soil moisture is explicitly always `False` (`SMART_FARMER_V3_PHASE_TRACKER.md:36`)
- Missing component: an irrigation-adequacy factor in the risk-score's factor list
- Required implementation: `crop_risk_service.py` add a `_irrigation_factor` calling the existing `irrigation_intelligence_service.py`, reporting UNKNOWN (never fabricated MEDIUM/LOW) when soil moisture is unavailable — consistent with the project's existing honest-absence discipline
- Dependencies: none — `irrigation_intelligence_service.py` already exists and is reusable
- Backend work: `crop_risk_service.py` new factor function calling the existing service
- Database/migration work: none
- Mobile work: none — surfaces automatically via existing risk-score screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the factor reports UNKNOWN (not a fabricated risk level) while soil moisture remains unavailable
- Verification method: extend `tests/test_crop_risk.py`

### D95-06 — Harvest risk factor
- Domain: 95. Risk Dashboard
- Current implementation status: Missing
- Existing relevant files/classes/functions: no harvest-timing risk factor in the list
- Missing component: a harvest-timing/readiness risk factor
- Required implementation: `crop_risk_service.py` add a `_harvest_timing_factor` reusing existing harvest-readiness computation (the same logic behind `HARVEST_APPROACHING`/`HARVEST_READY` notifications, D47-05)
- Dependencies: none — harvest-readiness logic already exists elsewhere in the project
- Backend work: `crop_risk_service.py` new factor function
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the factor reflects real harvest-window proximity
- Verification method: extend `tests/test_crop_risk.py`

### D95-07 — Market risk factor
- Domain: 95. Risk Dashboard
- Current implementation status: Missing
- Existing relevant files/classes/functions: no market/price factor in the list
- Missing component: a price-volatility signal
- Required implementation: `crop_risk_service.py` add a `_market_volatility_factor` using `price_query_service`'s existing reference-price history, reporting UNKNOWN when insufficient price history exists (never fabricated)
- Dependencies: sufficient reference-price history to compute volatility meaningfully
- Backend work: `crop_risk_service.py` new factor function
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the factor reports UNKNOWN with insufficient history, a real value otherwise
- Verification method: extend `tests/test_crop_risk.py`

### D95-08 — Payment risk factor
- Domain: 95. Risk Dashboard
- Current implementation status: Missing
- Existing relevant files/classes/functions: no payment factor in the list
- Missing component: a payment/delivery-delay signal
- Required implementation: `crop_risk_service.py` add a `_payment_delay_factor` using existing order/payment status data (`tools.get_delivery_status`/`get_my_orders`'s underlying repositories)
- Dependencies: none — order/payment data already exists
- Backend work: `crop_risk_service.py` new factor function
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the factor reflects real payment-delay data
- Verification method: extend `tests/test_crop_risk.py`

### D96-02 — Compare variety
- Domain: 96. Season Comparison
- Current implementation status: Missing
- Existing relevant files/classes/functions: `CropCycle.variety_id` exists on the model (crop_cycle.py:106-108) but `crop_comparison_service.py` never references it
- Missing component: a variety-comparison metric
- Required implementation: `crop_comparison_service.py` add a `variety` comparison field (same/different, like D96-01's proposed `same_crop`)
- Dependencies: none — `variety_id` already exists
- Backend work: `crop_comparison_service.py` add the field
- Database/migration work: none
- Mobile work: display variety comparison in comparison screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting variety comparison is correctly computed
- Verification method: extend `tests/test_crop_performance.py`

### D96-07 — Compare disease history
- Domain: 96. Season Comparison
- Current implementation status: Missing
- Existing relevant files/classes/functions: no disease-recurrence metric reused from `crop_risk_service`/`health_timeline_service`, despite both existing elsewhere
- Missing component: a disease-history comparison metric
- Required implementation: `crop_comparison_service.py` add a disease-recurrence-count comparison, reusing `crop_risk_service._disease_recurrence_factor`/`health_timeline_service`'s existing computation rather than re-deriving it
- Dependencies: none — both source services already exist
- Backend work: `crop_comparison_service.py` new comparison metric calling the existing services
- Database/migration work: none
- Mobile work: display disease-history comparison in comparison screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting disease-history comparison reflects real recurrence counts for both cycles
- Verification method: extend `tests/test_crop_performance.py`

### D96-08 — Compare weather impact
- Domain: 96. Season Comparison
- Current implementation status: Missing
- Existing relevant files/classes/functions: `weather_action_engine_service`/`irrigation_intelligence_service` outputs are not fed into comparison at all
- Missing component: a weather-impact comparison metric
- Required implementation: `crop_comparison_service.py` add a weather-action-count/severity comparison, reusing existing weather-action history rather than re-deriving it
- Dependencies: none — weather-action data already exists per crop cycle
- Backend work: `crop_comparison_service.py` new comparison metric
- Database/migration work: none
- Mobile work: display weather-impact comparison in comparison screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting weather-impact comparison reflects real recorded weather actions for both cycles
- Verification method: extend `tests/test_crop_performance.py`

### D96-09 — Compare market realization
- Domain: 96. Season Comparison
- Current implementation status: Missing
- Existing relevant files/classes/functions: only aggregate `actual_revenue` is compared, not per-unit price/market-realization
- Missing component: a per-unit price-achieved comparison, distinct from total revenue
- Required implementation: `crop_comparison_service.py` add `actual_revenue / actual_quantity` as a per-unit realization metric — subject to the same D96-03/D98-02 caveat that `actual_quantity` has no production write path yet, so this metric would honestly report insufficient-data until that's resolved
- Dependencies: D96-03's `actual_quantity` production write-path gap must close first for this to be meaningfully non-null
- Backend work: `crop_comparison_service.py` new comparison metric, gated on quantity being present
- Database/migration work: none
- Mobile work: display per-unit realization comparison once meaningful
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: test asserting the metric reports insufficient-data (never a fabricated per-unit price) while quantity is absent
- Verification method: extend `tests/test_crop_performance.py`

### D97-08 — Disease history captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `CropCycleClosureSnapshot.disease_summary` (JSONB), populated by `_create_closure_snapshot` directly from this cycle's `AIAnalysis` rows (`ai_analysis_repository.list_for_crop_cycle`) - counts and distinct diagnoses only (`total_photos_analyzed`, `disease_detected_count`, `diseases_observed`), not a reuse of the broader `health_timeline_service.py` (which mixes unrelated event types - a narrower, more precise source was used instead)
- Missing component: none
- Required implementation: none
- Dependencies: D97-04's shared snapshot mechanism
- Backend work: done — `crop_cycle_service.py`
- Database/migration work: done — shared `crop_cycle_closure_snapshots` table
- Mobile work: closure confirmation screen shows the frozen disease summary (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: `tests/test_crop_cycles.py::test_closing_a_crop_cycle_with_no_harvest_or_finances_creates_an_honest_empty_snapshot` (new) asserts the honest-empty case
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D97-09 — Weather impact captured at closure
- Domain: 97. Season Closure
- Current implementation status: VERIFIED (this continuation session, was Missing)
- Existing relevant files/classes/functions: `CropCycleClosureSnapshot.weather_impact_summary` (JSONB), populated by `_create_closure_snapshot` from `Notification` rows already tied to this crop cycle (`related_entity_type="crop_cycle"`, new `notification_repository.list_for_related_entity`), filtered to weather-related categories - counts and distinct categories only (`weather_alert_count`, `categories`)
- Missing component: none
- Required implementation: none
- Dependencies: D97-04's shared snapshot mechanism
- Backend work: done — `crop_cycle_service.py`, `notification_repository.py`
- Database/migration work: done — shared `crop_cycle_closure_snapshots` table
- Mobile work: closure confirmation screen shows the frozen weather-impact summary (unverified this pass)
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — additive
- Tests required: `tests/test_crop_cycles.py::test_closing_a_crop_cycle_with_no_harvest_or_finances_creates_an_honest_empty_snapshot` (new) asserts the honest-empty case
- Verification method: automated test (new), confirmed passing in the full backend suite re-run this session

### D98-04 — Previous disease used in learning
- Domain: 98. Historical Learning
- Current implementation status: Missing
- Existing relevant files/classes/functions: neither `personalization_service.py` nor `learning_foundation_service.py` references `AIAnalysis`, disease history, or `crop_health_case` data at all
- Missing component: a disease-history-based descriptive signal
- Required implementation: extend `personalization_service.py` with a `_disease_pattern_signal()` describing observed disease recurrence for this farmer's crops, gated by the same evidence-floor discipline as `_preferred_crop_signal`
- Dependencies: none — `AIAnalysis`/`crop_health_case` data already exists
- Backend work: `personalization_service.py` new signal function
- Database/migration work: none
- Mobile work: surface in personalization profile screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test mirroring `test_one_treatment_does_not_create_a_strong_permanent_preference` for disease patterns
- Verification method: extend `tests/test_personalization.py`

### D98-05 — Previous weather impact used in learning
- Domain: 98. Historical Learning
- Current implementation status: Missing
- Existing relevant files/classes/functions: neither file references weather data
- Missing component: a weather-impact-based descriptive signal
- Required implementation: extend `personalization_service.py` with a `_weather_impact_signal()`, same evidence-floor discipline
- Dependencies: none — weather-action history already exists
- Backend work: `personalization_service.py` new signal function
- Database/migration work: none
- Mobile work: surface in personalization profile screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test mirroring the existing evidence-floor pattern for weather-impact signals
- Verification method: extend `tests/test_personalization.py`

### D98-06 — Previous market realization used in learning
- Domain: 98. Historical Learning
- Current implementation status: Missing
- Existing relevant files/classes/functions: no price/market data referenced in either file
- Missing component: a market-realization-based descriptive signal
- Required implementation: extend `personalization_service.py` with a `_market_realization_signal()`, subject to the same D96-03/D98-02 caveat (needs `actual_quantity`'s production write-path gap resolved to be meaningful for per-unit realization; total-revenue-based observations could proceed independently)
- Dependencies: D96-03's `actual_quantity` gap for the per-unit variant; none for a revenue-only variant
- Backend work: `personalization_service.py` new signal function
- Database/migration work: none
- Mobile work: surface in personalization profile screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test mirroring the existing evidence-floor pattern for market-realization signals
- Verification method: extend `tests/test_personalization.py`

## 4. Broken

No scenario ID from any of the three cluster files (D73-D100) remains BROKEN — all 12
originally-disclosed BROKEN rows in the wider project were independently re-verified as
fixed in `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §A, and the 5 of those 12 that fell
within this group (D84-02, D84-04, D87-04, D87-05, D87-06) are folded into the
reconciliation-deltas table above as IMPLEMENTED.

D97-12 (the new finding from a prior pass, below) was the only BROKEN row in this group;
it has since been fixed and tested this session (P0 of `docs/FINAL_IMPLEMENTATION_PLAN.md`)
and is reclassified VERIFIED. **0 BROKEN scenario rows remain in this group.**

### D97-12 (new) — Closed seasons cannot accidentally receive active-season tasks
- Domain: 97. Season Closure
- Current implementation status: **VERIFIED (fixed and tested this session, was Broken)**
- Existing relevant files/classes/functions: `backend/app/services/task_service.py::create_task` (lines 41-65); contrast with the same file's `complete_task` (line 172, guards recurring-task creation with `crop_cycle.cultivation_status not in _TERMINAL_CULTIVATION_STATUSES`) and `cancel_all_pending_for_crop_cycle` (lines 209-228, proactively cancels PENDING tasks precisely because a HARVESTED/CANCELLED cycle shouldn't have live tasks, citing D9-15)
- Missing component: N/A — this was not an absent feature. The guard pattern already existed twice in the same file; `create_task` was the one call path that omitted it.
- Fix applied this session, `backend/app/services/task_service.py::create_task`, immediately after `crop_cycle_repository.get_owned` resolves the crop cycle and before constructing the `Task`:
  ```python
  if crop_cycle.cultivation_status in _TERMINAL_CULTIVATION_STATUSES:
      raise AppError(
          error_codes.VALIDATION_ERROR,
          "Cannot create a task for a crop cycle that has already ended.",
          409,
      )
  ```
- Dependencies: none — `_TERMINAL_CULTIVATION_STATUSES` was already defined at the top of the same file (line 30)
- Backend work: done — the four-line guard above
- Database/migration work: none
- Mobile work: none done — backend validation only; the mobile task-creation screen should surface the new 409 as a clear "this season has ended" message rather than a generic error (not yet done, tracked as a small follow-up, not a gap in this scenario's own backend-verified status)
- Automation work: none
- Notification work: none
- Offline/sync impact: none — task creation has no offline queue today (see D81-04); this fix applies equally whether or not that gap is later closed
- Security/RBAC impact: none — this is a business-rule validation, not an access-control change; ownership (`get_owned`) is already correctly enforced before this check would run
- Tests added and passing: `tests/test_tasks.py::test_cannot_create_a_task_for_a_closed_crop_cycle` (HARVESTED) and `::test_can_create_a_task_for_a_cancelled_crop_cycle_is_also_rejected` (CANCELLED), both asserting 409; existing `test_create_task` continues to pass unchanged as the regression check that active-cycle task creation still succeeds
- Verification method: automated test, confirmed passing in the full suite re-run this session

## 5. Future — with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D85-01 | 85 | Server wins | `docs/OFFLINE_ARCHITECTURE.md:32` — "MVP: last-write-wins with a visible warning... Full conflict-resolution UI is a P2 feature per the approved architecture, not MVP"; `docs/OFFLINE_MEDIA_SYNC.md:58-60` — "No conflict resolution — not applicable here" (the only shipped offline path, photos, is create-only) |
| D85-02 | 85 | Client wins | Same citations as D85-01 |
| D85-03 | 85 | Latest timestamp | Same citations as D85-01 |
| D85-04 | 85 | Merge | Same citations as D85-01 |
| D85-05 | 85 | Manual resolution | Same citations as D85-01; "P2 feature" implies a farmer-facing manual-resolution UI is the deferred target |
| D85-06 | 85 | Entity-specific strategy | Same citations as D85-01; only one entity (crop photo) even has an offline path, and it structurally cannot conflict (create-only, idempotency-key based) |
| D85-07 | 85 | Audit (of conflict resolution decisions) | Same citations as D85-01 |
| D86-03 | 86 | Job idempotency | `docs/NOTIFICATION_ARCHITECTURE.md:37-44` — scheduler deliberately deferred ("do not introduce a complicated distributed architecture unnecessarily"), interfaces (`AlertCandidate`) pre-designed so a future scheduler/job needs no redesign. Note: `scheduler.py` (APScheduler) has since been added for Expert SLA/weather sweeps (Matrix §B, "P0" batches, domains 35/16 — outside this group), which may partially supersede this citation's premise; neither reconciliation document reclassifies D86-03 itself, so it is carried forward unchanged rather than independently re-audited in this documentation-synthesis pass |
| D90-05 | 90 | Speech-to-text provider abstraction | `api/v1/assistant.py:1-6` — explicit architectural decision: STT is handled entirely client-side via device-native APIs, "this backend only ever sees and returns text," consistent with a stated "free-first, no-paid-speech-API" requirement |
| D90-06 | 90 | Text-to-speech provider abstraction | `ai_result_localization_service.py:3` + `assistant.py:3-4` — same explicit, documented client-side-by-design decision as D90-05 |
| D98-07 | 98 | Next-season recommendations generated | `learning_foundation_service.py`'s own `_ML_READINESS_NOTE`; `SMART_FARMER_V3_PHASE_TRACKER.md:37` — "No trained ML model exists or was fabricated - ml_training_justified always false" |

All 11 FUTURE rows in this group carry a real, specific citation to a documented deferral
already present in the project's own code/docs before this audit ran. None are flagged
UNJUSTIFIED.

## 6. Out of Scope — with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D74-04 | 74 | Claim boundary (submitting a claim to a real insurer for adjudication) | Requires a real regulated relationship with a licensed insurer — this app cannot legally/ethically originate or transmit a binding claim on its own |
| D74-06 | 74 | Settlement boundary (declaring/crediting a payout amount to the farmer) | A farmer-facing app cannot self-declare or fabricate an insurance payout — settlement is exclusively the insurer's regulated act |

Both rows are correctly justified — neither is flagged UNJUSTIFIED.

**Tenant isolation note (Domain 100):** the checklist's "tenant isolation" scenario has no
separate OUT_OF_SCOPE row in `c13_governance_farmbrain_security.md`. This project has a
single-farmer-per-account architecture, not a multi-tenant/organization model, so the
cluster file directly scored the checklist's tenant-isolation intent as **D100-07**
("Tenant isolation (cross-farmer sweep)") — a real 9-endpoint sweep asserting Farmer B
gets 404 against every one of Farmer A's crop-cycle-scoped resources — and classified it
**VERIFIED** (see Section 1 above), not OUT_OF_SCOPE. This matches the expectation stated
in this task's brief: farmer-ownership isolation is the real functional analog of tenant
isolation for this architecture, and it is correctly VERIFIED rather than being carried
as an OUT_OF_SCOPE row with no functional equivalent.

## 7. Environment Dependent — exact dependency

None. This group (Domains 73-100) contains zero ENVIRONMENT_DEPENDENT rows. The
project's only 6 ENVIRONMENT_DEPENDENT scenarios (D14-01, D14-03, D14-04, D14-05, D14-06,
D14-08 — "whether the live Open-Meteo API is actually reachable from a given deployment
network," per `docs/FINAL_GAP_REPORT.md`) all fall within Domain 14 (Weather), which is
outside this group.
