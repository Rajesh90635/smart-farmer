# Canonical Gap Matrix — Group B (Domains 27-46)

Source cluster files folded into this document: `docs/audit/c05_disease_ai.md` (domains
27-32), `docs/audit/c06_expert_network.md` (domains 33-39), `docs/audit/c07_voice_language_community.md`
(domains 40-46) — 47 + 43 + 59 = **149 scenario rows**, every one individually reconciled
below against `docs/FINAL_100_DOMAIN_SCENARIO_MATRIX.md` and `docs/FINAL_GAP_REPORT.md`.

Compound-status rows (a cluster file gave two labels, e.g. "VERIFIED for pipeline... but
ENVIRONMENT_DEPENDENT for real accuracy") are bucketed by their primary/leading label, with
the secondary caveat preserved in the evidence text — the same convention
`FINAL_100_DOMAIN_SCENARIO_MATRIX.md` itself discloses using for its own ±1-row ambiguity
(D59-03). Affected rows here: D27-04, D29-04, D31-04 (all bucketed VERIFIED).

## Reconciliation deltas applied

| Scenario ID | Domain | Was | Now | Source citation |
|---|---|---|---|---|
| D33-02 | 33 (Expert Escalation) | PARTIAL | VERIFIED | `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §B, batch "5 (Expert case routing)". Confirmed in code this session: `backend/app/services/case_service.py:97-136` `_build_match_criteria` now populates crop/language/state/district from the case's real context (docstring explicitly names D33-02); `disease_category` is deliberately left unpopulated (no fabrication from free-text `predicted_class`). |
| D33-06 | 33 (Expert Escalation) | PARTIAL | VERIFIED | Same batch 5. Confirmed: `case_service.py:301-308` adds a distinct `CASE_ESCALATED` audit-log action (previously only the status label changed) — comment cites D33-06 verbatim. |
| D34-01 | 34 (Expert Assignment) | PARTIAL | VERIFIED | Same batch 5. Confirmed: `nearby_professional_service.py:50-57` now hard-excludes `AvailabilityStatus.OFFLINE` professionals from candidacy (previously only soft-scored 0) — comment cites D34-01 verbatim. |
| D36-02 | 36 (Expert Recommendation) | PARTIAL | VERIFIED | Same batch 5. Confirmed: `backend/app/schemas/case.py:32-37` adds `CaseResponse.latest_review_notes`, surfacing the professional's free-text explanation to the farmer's case-detail view for the first time — comment cites D36-02 verbatim. |
| D34-03 | 34 (Expert Assignment) | PARTIAL | VERIFIED | `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §B, batch "P0 (Expert SLA scheduler)" row 2 ("Timeout-triggered reassignment"). Confirmed: `backend/app/services/case_sla_service.py` docstring lines 10-14 names D34-03 directly; `_expire_reassign_or_escalate` (lines 102-150) re-invokes `case_service._try_auto_assign` for an expired assignment, excluding the non-responsive professional. |
| D35-05 | 35 (Expert SLA) | PARTIAL | VERIFIED | Same P0 batch row 2 ("case-level unavailability handling"). Confirmed: `case_sla_service.py` docstring lines 18-23 names D35-05 directly — a non-responding professional's expiry is now the detection signal for case-level unavailability. |
| D35-02 | 35 (Expert SLA) | MISSING | VERIFIED | Same batch, "P0 (Expert SLA scheduler)" row 1. Confirmed: `backend/app/services/scheduler.py` (new APScheduler-based background job, `case_sla_sweep`) + `case_sla_service.run_case_sla_sweep` now actually reads `CaseAssignment.expires_at` — docstring names D35-02 directly. |
| D35-03 | 35 (Expert SLA) | MISSING | VERIFIED | Same batch. Confirmed: `case_sla_service._send_expiry_reminders` (lines 71-99) sends one `CASE_ASSIGNMENT_REMINDER` notification per assignment nearing `expires_at` — docstring names D35-03 directly. |
| D35-04 | 35 (Expert SLA) | MISSING | VERIFIED | Same batch. Confirmed: `case_sla_service._expire_reassign_or_escalate` (lines 122-139) escalates to `CaseStatus.ESCALATED` with a `CASE_SLA_BREACH_ESCALATED` audit action + CRITICAL notification once `case_sla_max_reassignment_attempts` is exceeded — docstring names D35-04 directly. |
| D38-06 | 38 (Follow-up) | MISSING | VERIFIED | `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §B, batch "P0" row 3 ("worsened-treatment auto-escalation"). Confirmed: `case_service.escalate_case_for_worsened_treatment` (lines 426-452) — docstring quotes D38-06/D39-07 verbatim ("a worsening outcome never automatically triggers any escalation"), is idempotent (guards against re-escalating an already ESCALATED/CLOSED/CANCELLED case), logs `CASE_ESCALATED_WORSENED_TREATMENT`, and sends a CRITICAL notification. |
| D39-07 | 39 (Reinspection) | MISSING | VERIFIED | Same P0 batch row 3, same function (`escalate_case_for_worsened_treatment`), same docstring citation. |
| D35-06 | 35 (Expert SLA) | FUTURE | VERIFIED | **Not explicitly named as a changed scenario ID in either `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` or `FINAL_GAP_REPORT.md`.** This is an additional finding from this reconciliation pass, not a pre-existing delta — flagged so the caller can double-check it. D35-06 ("Case timeout": "24h assignment window elapses with no response... `expires_at` is never read/compared") is functionally identical to what `case_sla_service._expire_reassign_or_escalate` (lines 102-150) now does on every scheduler tick: it reads `expires_at` against `now`, marks the assignment `EXPIRED`, and then either reassigns (D34-03) or escalates (D35-04). The three named deltas (D35-02/03/04, D34-03) collectively close the exact gap D35-06 described; no separate code path remains unimplemented for it. Recommend the next full-matrix reconciliation pass add D35-06 to the official batch table. |

Explicitly out of this group's scope, confirmed and skipped per task instructions: **D80-01**
(PARTIAL→VERIFIED, "CRITICAL priority now reachable") belongs to domain 80, not domain
33-46 — it is not a scenario ID in any of the three source cluster files for this group.

No other scenario ID in `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §A (BROKEN fixes), the
remaining §B batches (1,2,3,4,6,7,8,9,10,11), or `FINAL_GAP_REPORT.md`'s 9-row resolution /
D44-13 / D60-01 / D61-01 notes falls within domains 27-46. (D44-13, "Transporter role," is
discussed in `FINAL_GAP_REPORT.md` as a borderline case but its resolution is "kept as
MISSING, not FUTURE" — i.e. **no status change** — so it appears below with no delta-table
row, unchanged from the cluster file.)

## Count summary (this group)

| Status | Count |
|---|---:|
| VERIFIED | 61 |
| IMPLEMENTED | 4 |
| PARTIAL | 20 |
| MISSING | 63 |
| BROKEN | 0 |
| FUTURE | 1 |
| OUT_OF_SCOPE | 0 |
| ENVIRONMENT_DEPENDENT | 0 |
| TOTAL | 149 |

*(Updated this session, P1 task-overdue-reminder cluster: D37-04 MISSING→VERIFIED (-1
MISSING, +1 VERIFIED); D37-03 MISSING→PARTIAL (-1 MISSING, +1 PARTIAL — the
recommendation-derived half remains blocked on unbuilt D37-01). Total unchanged.)*

(47 rows from c05 + 43 rows from c06 + 59 rows from c07 = 149; matches the sum of every
bucket above.)

## 1. Attended (Verified + Implemented) — condensed list

| Scenario ID | Domain | Scenario Name | Status | One-line evidence |
|---|---|---|---|---|
| D27-01 | 27 Disease | Disease risk | VERIFIED | `crop_risk_service.py:55-98,194-205`; `test_crop_risk.py::test_no_data_at_all_returns_insufficient_data_not_fabricated_low` |
| D27-03 | 27 Disease | Photo inspection | VERIFIED | `test_crop_photos.py::test_get_photo_detail` etc. |
| D27-04 | 27 Disease | Photo diagnosis | VERIFIED (pipeline; real-model accuracy is ENVIRONMENT_DEPENDENT/FUTURE, disclosed) | `prediction_validator.py:1-103`; `test_ai_analysis.py::test_disease_detected_result_with_fake_provider` |
| D27-05 | 27 Disease | Disease history | VERIFIED | `health_timeline_service.py:61-70,128-141`; `test_health_timeline.py` (14 tests) |
| D27-07 | 27 Disease | Follow-up | VERIFIED | `treatment_service.py:108-146`; `test_treatments.py` (16 tests) |
| D29-01 | 29 AI Diagnosis | Photo input | VERIFIED | `ai_analysis_service.py:110-113`; `test_ai_analysis.py` |
| D29-04 | 29 AI Diagnosis | Disease detection | VERIFIED (pipeline; same caveat as D27-04) | same evidence as D27-04 |
| D29-07 | 29 AI Diagnosis | Multiple possibilities | VERIFIED | `ai_analysis.py:91`; `test_ai_model_components.py::test_top_k_predictions_are_preserved_in_result` |
| D29-08 | 29 AI Diagnosis | Confidence | VERIFIED | `confidence.py:25-30`; `test_ai_model_components.py::TestConfidenceEvaluator` |
| D29-09 | 29 AI Diagnosis | Model version | VERIFIED | `ai_analysis.py:82-87`; `test_ai_analysis.py::test_model_version_is_always_recorded` |
| D29-10 | 29 AI Diagnosis | Unknown diagnosis | VERIFIED | `prediction_validator.py:56-63,74-81`; `test_unsupported_crop_result` |
| D29-11 | 29 AI Diagnosis | Insufficient information | VERIFIED | `prediction_validator.py:87-94`; `test_low_confidence_result_never_names_a_disease` |
| D30-01 | 30 Image Quality | Blur | VERIFIED | `image_quality.py:33-37,40-62`; `test_image_pipeline.py::test_quality_flags_flat_image_as_blurry` |
| D30-02 | 30 Image Quality | Poor lighting | VERIFIED | `image_quality.py:27-31`; `test_image_pipeline.py::test_quality_flags_too_dark` |
| D30-07 | 30 Image Quality | Upload failure | VERIFIED | `pending_upload_queue.dart`; `pending_upload_queue_test.dart` (11 tests, flutter test re-run) |
| D30-08 | 30 Image Quality | Quality rejection | VERIFIED | `ai_analysis_service.py:58-63` 422 gate; `test_analysis_requires_accepted_photo_quality` |
| D30-09 | 30 Image Quality | Retake guidance | VERIFIED | `farmer_messages.py:23`; `test_ai_localization.py` |
| D31-01 | 31 AI Confidence | High confidence | VERIFIED | `prediction_validator.py:96-102`; `test_high_confidence_healthy` |
| D31-02 | 31 AI Confidence | Medium confidence | VERIFIED | `prediction_validator.py:101`; `test_medium_confidence_disease_requires_review` |
| D31-03 | 31 AI Confidence | Low confidence | VERIFIED | `prediction_validator.py:87-94`; `test_low_confidence_never_names_a_class` |
| D31-04 | 31 AI Confidence | Confidence threshold | VERIFIED (mechanism; numeric calibration honestly disclosed as FUTURE) | `confidence.py:1-13`; `test_boundary_at_high_threshold_is_high` |
| D31-06 | 31 AI Confidence | Confidence stored | VERIFIED | `ai_analysis.py:90`; `test_disease_detected_result_with_fake_provider` |
| D31-07 | 31 AI Confidence | Confidence explanation | VERIFIED | `ai_result_localization_service.py:27-30,76-82`; `test_ai_localization.py` |
| D32-01 | 32 Unknown Diagnosis | AI cannot identify | VERIFIED | `prediction_validator.py:56-63,74-81`; `test_unsupported_crop_result` |
| D32-02 | 32 Unknown Diagnosis | Insufficient evidence | VERIFIED | `treatment_service.py:122-131`; `test_effectiveness_is_insufficient_evidence_with_no_follow_up` |
| D32-03 | 32 Unknown Diagnosis | Ask for better photo | VERIFIED | `ai_result_localization_service.py:84-85`; `test_ai_localization.py` |
| D32-06 | 32 Unknown Diagnosis | Never invent diagnosis | VERIFIED | `prediction_validator.py` (all branches); `test_crop_mismatch_is_never_silently_diagnosed` |
| D33-01 | 33 Expert Escalation | Create case | VERIFIED | `case_service.py:43-48,70,76-82`; `test_create_case_auto_assigns_to_verified_expert` |
| D33-02 | 33 Expert Escalation | Route case | VERIFIED (delta) | `case_service.py:97-136 _build_match_criteria`; batch-5 fix (see deltas table) |
| D33-03 | 33 Expert Escalation | Assign expert | VERIFIED | `case_service.py:105-125`; `test_assigned_expert_can_access_the_authorized_photo` |
| D33-05 | 33 Expert Escalation | Track status | VERIFIED | `api/v1/cases.py:42-58,120-145`; `test_farmer_a_cannot_access_farmer_bs_case` |
| D33-06 | 33 Expert Escalation | Escalate when required | VERIFIED (delta) | `case_service.py:291-308`; batch-5 fix (see deltas table) |
| D34-01 | 34 Expert Assignment | Expert availability | VERIFIED (delta) | `nearby_professional_service.py:50-57`; batch-5 fix (see deltas table) |
| D34-02 | 34 Expert Assignment | Assignment | VERIFIED | duplicate of D33-03 |
| D34-03 | 34 Expert Assignment | Reassignment | VERIFIED (delta) | `case_sla_service.py` timeout-reassignment path; P0 batch (see deltas table) |
| D34-05 | 34 Expert Assignment | Case completion | VERIFIED | `case_service.py:243-261`; `test_close_case_revokes_photo_access` |
| D35-02 | 35 Expert SLA | SLA monitoring | VERIFIED (delta) | `scheduler.py` + `case_sla_service.run_case_sla_sweep`; P0 batch |
| D35-03 | 35 Expert SLA | Reminder | VERIFIED (delta) | `case_sla_service._send_expiry_reminders`; P0 batch |
| D35-04 | 35 Expert SLA | Escalation (on SLA breach) | VERIFIED (delta) | `case_sla_service._expire_reassign_or_escalate` lines 122-139; P0 batch |
| D35-05 | 35 Expert SLA | Expert unavailable | VERIFIED (delta) | `case_sla_service.py` docstring lines 18-23; P0 batch |
| D35-06 | 35 Expert SLA | Case timeout | VERIFIED (inferred delta — flag for confirmation) | `case_sla_service._expire_reassign_or_escalate`; see deltas table note |
| D36-01 | 36 Expert Recommendation | Recommendation | VERIFIED | `case_review.py:28-29`; `test_expert_submits_confirmed_review` |
| D36-02 | 36 Expert Recommendation | Explanation | VERIFIED (delta) | `schemas/case.py:32-37 latest_review_notes`; batch-5 fix (see deltas table) |
| D38-03 | 38 Follow-up | Farmer response | VERIFIED | `treatment_follow_up.py:1-6`; `test_cannot_create_follow_up_for_another_farmers_treatment` |
| D38-04 | 38 Follow-up | Outcome | VERIFIED | `treatment_service.py:1-16,108-146`; `test_effectiveness_improved_disease_to_healthy` |
| D38-06 | 38 Follow-up | Escalation | VERIFIED (delta) | `case_service.escalate_case_for_worsened_treatment`; P0 batch |
| D39-01 | 39 Reinspection | New photo | VERIFIED | `treatment_follow_up.py:1-6`; `test_effectiveness_improved_disease_to_healthy` |
| D39-02 | 39 Reinspection | Before/after comparison | VERIFIED | `treatment_service.py:47-48`; effectiveness tests |
| D39-04 | 39 Reinspection | Improvement | VERIFIED | `treatment_service.py:132-133`; `test_effectiveness_improved_disease_to_healthy` |
| D39-05 | 39 Reinspection | No improvement | VERIFIED | `treatment_service.py:136-137`; `test_effectiveness_no_significant_change_disease_to_disease` |
| D39-06 | 39 Reinspection | Worsening | VERIFIED | `treatment_service.py:134-135`; `test_effectiveness_worsened_healthy_to_disease` |
| D39-07 | 39 Reinspection | Expert escalation | VERIFIED (delta) | `case_service.escalate_case_for_worsened_treatment`; P0 batch |
| D40-04 | 40 Voice | Voice answer | VERIFIED | `assistant_screen.dart:106-119,236`; `voice_service_test.dart` (5 tests) |
| D40-07 | 40 Voice | Provider abstraction | VERIFIED | `voice_service.dart` + `flutter_tts_voice_service.dart`; `voice_service_test.dart` |
| D41-01 | 41 Local Language | Language selection | VERIFIED | `locale_controller.dart:13`; `language_switch_live_test.dart` |
| D41-05 | 41 Local Language | Local-language audio | VERIFIED | `flutter_tts_voice_service.dart:9-17,69-70`; `flutter_tts_voice_service_test.dart` |
| D41-06 | 41 Local Language | Language persistence | VERIFIED | `locale_controller.dart:25-30`; `voice_language_controller_test.dart` |
| D41-07 | 41 Local Language | Language change | VERIFIED | `profile_screen.dart:77-98`; `language_switch_live_test.dart` |
| D41-08 | 41 Local Language | Audio matching selected language | VERIFIED | `daily_briefing_screen.dart:60-87`; `voice_language_controller_test.dart` |
| D44-01 | 44 Nearby Services | Expert | VERIFIED | `nearby_professional_service.py:7-11,54-96` |
| D33-04 | 33 Expert Escalation | Notify expert | IMPLEMENTED | `case_service.py:308-334` (`NotificationService`); no dedicated test asserts the row |
| D35-01 | 35 Expert SLA | SLA start | IMPLEMENTED | `case_service.py:41,111,123` `expires_at` set; no test asserts the value |
| D36-05 | 36 Expert Recommendation | Recommendation history | IMPLEMENTED | `health_timeline_service.py:154`, `assistant/tools.py:189`; no test for multi-review ordering |
| D40-06 | 40 Voice | Voice help | IMPLEMENTED | `intent_router.py:62`; `farmer_messages.py:76`; no dedicated end-to-end test |

## 2. Partial — full itemized (EVERY row, no aggregation)

### D27-02 — Disease observation
- Domain: 27 (Disease)
- Scenario ID: D27-02
- Exact scenario name: Disease observation
- Current implementation status: Partial
- Existing relevant files/classes/functions: `backend/app/schemas/case.py:11-17` (`CaseCreateRequest`, no notes field); `backend/app/models/crop_health_case.py:41-45` (`CaseReason` 4-value enum); photo capture via `POST /api/v1/crop-photos`
- Missing component: No structured or free-text symptom-description field anywhere in the observation flow — only photo capture or a fixed-vocabulary case reason
- Required implementation: Add an optional `symptom_description: str | None` (length-capped, e.g. 500 chars) to `CaseCreateRequest`/`crop_health_cases`, surfaced read-only to the assigned professional
- Dependencies: Feeds D33-01 (Create case); no scenario depends on this being built first
- Backend work: `backend/app/schemas/case.py`, `backend/app/models/crop_health_case.py`, `backend/app/services/case_service.py` (persist + return the field)
- Database/migration work: New nullable `crop_health_cases.symptom_description` column
- Mobile work: `mobile/lib/features/expert_case` case-creation screen — add a free-text field
- Automation work: none
- Notification work: none — additive to existing `CASE_CREATED` flow
- Offline/sync impact: none (case creation is already online-only)
- Security/RBAC impact: none — same ownership/consent scoping as the rest of `CaseCreateRequest`
- Tests required: a service-level test asserting the field round-trips and is scoped to the case owner/assignee, mirroring `test_cases.py`'s existing style
- Verification method: automated test (backend pytest)

### D29-02 — Crop identification
- Domain: 29 (AI Diagnosis)
- Scenario ID: D29-02
- Exact scenario name: Crop identification
- Current implementation status: Partial
- Existing relevant files/classes/functions: `model_provider.py:29` (`crop_match` boolean), `prediction_validator.py:65-72` (CROP_MISMATCH branch)
- Missing component: No open-set "identify which crop this photo shows" capability — the crop is always fixed earlier via `CropCycle.crop_id`, never derived from the photo itself
- Required implementation: Would require a distinct crop-identification model/provider method (`predict_crop(image_bytes) -> ranked crop candidates`) analogous to `predict_disease`, plus a new `ResultStatus` or separate response field for the ranked guess
- Dependencies: Blocked on the same "no real trained model" constraint as D27-04/D29-04 (`NotConfiguredModelProvider`); would be additive to, not a replacement for, `crop_match`
- Backend work: `backend/app/services/ai/model_provider.py` (new method signature), `prediction_validator.py` (new branch), `ai_analysis_service.py`
- Database/migration work: New column(s) on `ai_analyses` for a crop-identification result, or a new sibling table if kept independent from disease diagnosis
- Mobile work: none beyond surfacing a new result field once it exists
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same analyze-request flow as existing diagnosis
- Security/RBAC impact: none — additive
- Tests required: new fake-provider tests mirroring `test_crop_mismatch_result`/`test_crop_mismatch_is_never_silently_diagnosed`
- Verification method: automated test, once a real or fake crop-ID provider exists; real-world accuracy would be ENVIRONMENT_DEPENDENT like disease diagnosis

### D30-03 — Wrong framing
- Domain: 30 (Image Quality)
- Scenario ID: D30-03
- Exact scenario name: Wrong framing
- Current implementation status: Partial
- Existing relevant files/classes/functions: `image_quality.py`, `image_validation.py` (no framing check); `photo_guidance_screen.dart:17` (pre-capture tip only)
- Missing component: No automated post-capture framing/composition detection or rejection — mitigation is guidance text only
- Required implementation: A composition heuristic (e.g. subject-occupies-frame ratio via edge/contour detection, or a lightweight bounding-box check) added to the existing `image_quality.py` pipeline, emitting a new `quality_reasons` value (e.g. `poor_framing`)
- Dependencies: Shares infrastructure with D30-04 (Wrong plant part) — both would likely be added in the same pass since they extend the same quality-check module
- Backend work: `backend/app/services/image_quality.py` (new check function), `ai_analysis_service.py` (no change — quality gate is upstream of analysis)
- Database/migration work: none — `quality_reasons` is already a flexible list/JSON field
- Mobile work: `mobile/lib/features/crop_photo` — surface the new reason via the existing `qualityFriendlyMessages` mapping
- Automation work: none — runs synchronously on upload like the existing checks
- Notification work: none
- Offline/sync impact: none — same synchronous upload-time check as blur/lighting
- Security/RBAC impact: none — additive
- Tests required: unit tests mirroring `test_image_pipeline.py::test_quality_flags_flat_image_as_blurry`, plus a friendly-message mapping test mirroring `crop_photo_quality_result_test.dart`
- Verification method: automated test (backend pytest + Flutter widget test)

### D30-04 — Wrong plant part
- Domain: 30 (Image Quality)
- Scenario ID: D30-04
- Exact scenario name: Wrong plant part
- Current implementation status: Partial
- Existing relevant files/classes/functions: same as D30-03; `photo_guidance_screen.dart:21` ("Capture the affected area" tip only)
- Missing component: No automated post-capture detection of which plant part is shown — mitigation is guidance text only
- Required implementation: Would need a plant-part classifier (leaf/stem/whole-plant/close-up) — either a lightweight heuristic or a small auxiliary model — emitting a new `quality_reasons` value (e.g. `wrong_plant_part`)
- Dependencies: Same infrastructure as D30-03; also relates to D29-03 (Plant-part identification, MISSING) — building this would likely subsume or directly enable D29-03
- Backend work: `backend/app/services/image_quality.py` or a new `plant_part_classifier.py`
- Database/migration work: none — reuses `quality_reasons`
- Mobile work: surface via existing friendly-message mapping
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: mirrors D30-03's test plan
- Verification method: automated test; real accuracy would be ENVIRONMENT_DEPENDENT/FUTURE like disease diagnosis if a real model is involved

### D31-05 — Expert escalation
- Domain: 31 (AI Confidence)
- Scenario ID: D31-05
- Exact scenario name: Expert escalation
- Current implementation status: Partial
- Existing relevant files/classes/functions: `prediction_validator.py` (`requires_review` set automatically); `case_service._try_auto_assign` (`case_service.py:95-129`, fully automatic once a case exists); `CaseReason.AI_LOW_CONFIDENCE`/`AI_UNKNOWN` (`crop_health_case.py`)
- Missing component: Nothing auto-creates a `CropHealthCase` when `requires_review` becomes true — the farmer must tap "Request Expert Review"; professional matching/assignment is automatic only after that manual step
- Required implementation: An opt-in auto-escalation path: when `ai_analysis_service` completes an analysis with `requires_review=True` (MEDIUM confidence, or UNKNOWN/CROP_MISMATCH), optionally auto-create a `CropHealthCase` with `reason=CaseReason.AI_LOW_CONFIDENCE`/`AI_UNKNOWN` — gated behind an explicit farmer consent setting (consent is already required at case creation, so this must not silently share data)
- Dependencies: D32-05 (Unknown Diagnosis → Expert escalation) has the identical gap and would share the same fix
- Backend work: `backend/app/services/ai_analysis_service.py` (call into `case_service.create_case`-equivalent after analysis, behind a consent check), `case_service.py`
- Database/migration work: possibly a new `farmer_profile.auto_escalate_low_confidence` boolean if made opt-in per farmer
- Mobile work: a settings toggle if opt-in is added; otherwise none
- Automation work: none — this is a synchronous post-analysis action, not a scheduled sweep
- Notification work: reuses existing `CASE_ASSIGNED` notification once a case is auto-created
- Offline/sync impact: none — same online-only case-creation constraint as today
- Security/RBAC impact: consent must still gate any data sharing — this is the one place where "purely additive" is not quite true, since auto-creating a case without an explicit tap changes the consent flow; must not bypass `CaseConsent`
- Tests required: a test asserting a MEDIUM-confidence/UNKNOWN analysis with consent-on auto-creates a case, and one asserting consent-off never does
- Verification method: automated test (backend pytest, mirroring `test_cases.py::test_create_case_auto_assigns_to_verified_expert`)

### D32-05 — Expert escalation (Unknown Diagnosis)
- Domain: 32 (Unknown Diagnosis)
- Scenario ID: D32-05
- Exact scenario name: Expert escalation
- Current implementation status: Partial
- Existing relevant files/classes/functions: same as D31-05 — `CaseReason.AI_UNKNOWN` (`crop_health_case.py:44`), `case_service._try_auto_assign`
- Missing component: identical gap to D31-05 — nothing auto-opens a case purely because `result_status` became UNKNOWN
- Required implementation: same fix as D31-05 (shared implementation, triggered for the UNKNOWN branch specifically)
- Dependencies: Shares a fix with D31-05 — implement once, covers both
- Backend work: same as D31-05
- Database/migration work: same as D31-05
- Mobile work: same as D31-05
- Automation work: none
- Notification work: reuses `CASE_ASSIGNED`
- Offline/sync impact: none
- Security/RBAC impact: same consent caveat as D31-05
- Tests required: same test plan as D31-05, UNKNOWN-branch variant
- Verification method: automated test

### D34-04 — Expert response
- Domain: 34 (Expert Assignment)
- Scenario ID: D34-04
- Exact scenario name: Expert response
- Current implementation status: Partial
- Existing relevant files/classes/functions: `case_service.py:156-192` (`accept`/`decline` logic, VERIFIED by test); `mobile/lib/features/expert_case/` (only `case_models.dart`/`case_repository.dart` — farmer-facing subset)
- Missing component: No professional-facing Flutter UI exists at all to accept/decline/review a case — only reachable via direct API calls
- Required implementation: A new professional-role mobile flow: case inbox list, case detail, accept/decline buttons, review-submission form — a parallel screen set to the farmer-facing `expert_case` feature, gated by `Role` check
- Dependencies: Depends on whatever this project's plan is for a professional-facing app surface at all (may be a distinct app target, not just a new screen in the farmer app) — this is a scope decision, not just an engineering task
- Backend work: none — `POST /cases/{id}/accept`/`/decline`/`/review` already exist and are tested
- Database/migration work: none
- Mobile work: new `mobile/lib/features/professional_case/` (or equivalent) screens: case list, detail, accept/decline, review form
- Automation work: none
- Notification work: none new — existing `CASE_ASSIGNED`/`CASE_REVIEWED` notifications already fire correctly
- Offline/sync impact: to be designed — the farmer-facing case flow is online-only today; a new professional flow should follow the same convention unless there's a reason to diverge
- Security/RBAC impact: new screens must enforce `Role` checks matching the existing backend endpoint guards — no new backend RBAC needed since the endpoints already exist
- Tests required: new Flutter widget tests for the professional screens; backend tests already exist and pass
- Verification method: live manual verification (a new UI surface) once built, backed by the already-passing backend tests

### D36-03 — Evidence
- Domain: 36 (Expert Recommendation)
- Scenario ID: D36-03
- Exact scenario name: Evidence
- Current implementation status: Partial
- Existing relevant files/classes/functions: `case_review.py`, `case_service.py` (AI vs. expert result kept independent); `test_expert_disagreement_recorded_without_touching_ai_result` (`tests/test_cases.py:110`)
- Missing component: `CaseReview` has no explicit field linking the outcome back to a specific supporting photo/analysis beyond the case's own single `ai_analysis_id` — no "evidence" concept distinct from that FK
- Required implementation: Add an optional `evidence_photo_ids: list[uuid]`/`evidence_analysis_ids: list[uuid]` field to `CaseReview`, letting a professional cite specific photos/analyses (useful once a case can accumulate multiple photos over time)
- Dependencies: Loosely related to D36-07 (Recommendation version) — both touch how multiple reviews/evidence accumulate per case
- Backend work: `backend/app/models/case_review.py`, `backend/app/schemas/case.py`, `case_service.submit_review`
- Database/migration work: new join table `case_review_evidence(review_id, crop_photo_id)` or a JSONB array column on `case_reviews`
- Mobile work: professional-side review form (see D34-04) would need a photo-picker if built
- Automation work: none
- Notification work: none
- Offline/sync impact: none — additive to online-only review submission
- Security/RBAC impact: none — must still respect the existing `PhotoAccessGrant` scoping (a professional can only cite a photo they were granted access to)
- Tests required: a test asserting evidence references are scoped to grants the professional actually holds
- Verification method: automated test

### D38-01 — Follow-up date
- Domain: 38 (Follow-up)
- Scenario ID: D38-01
- Exact scenario name: Follow-up date
- Current implementation status: Partial
- Existing relevant files/classes/functions: `schemas/treatment.py:30-33` (`FollowUpCreateRequest.observation_date`, past/present-only)
- Missing component: No forward-looking "please check back on day N" scheduled follow-up date — only a record of an observation that already happened
- Required implementation: Add an optional `next_check_due_date` to `TreatmentRecord` (set at treatment-creation time, e.g. "check back in 7 days"), read by a new reminder sweep (see D38-02)
- Dependencies: D38-02 (Reminder) directly depends on this field existing first
- Backend work: `backend/app/models/treatment_record.py` (new column), `backend/app/schemas/treatment.py`, `treatment_service.py` (accept the field at creation)
- Database/migration work: new nullable `treatment_records.next_check_due_date` column
- Mobile work: `mobile/lib/features/treatment` (or crop_photo) — optional date picker at treatment-creation time
- Automation work: enables the future scheduler sweep in D38-02
- Notification work: enables the future reminder notification in D38-02
- Offline/sync impact: none — additive to existing online-only treatment creation
- Security/RBAC impact: none
- Tests required: a test asserting the field round-trips and defaults to null when not provided
- Verification method: automated test

### D39-03 — Disease status
- Domain: 39 (Reinspection)
- Scenario ID: D39-03
- Exact scenario name: Disease status
- Current implementation status: Partial
- Existing relevant files/classes/functions: `treatment_service.py:10-16` (coarse HEALTHY/DISEASE_DETECTED comparison only, disclosed limitation)
- Missing component: No real severity/disease-progression measurement — `AIAnalysis` has no severity score, so "no_significant_change" only means "same category," never a measured delta
- Required implementation: Would require the AI model layer itself to output a severity/extent score (e.g. percent-of-leaf-area-affected) — a model capability, not just a service-layer change; blocked on having any real trained model at all (see D27-04)
- Dependencies: Hard-blocked on real model capability (`NotConfiguredModelProvider` has none); same root cause as D27-04/D29-04's ENVIRONMENT_DEPENDENT/FUTURE status
- Backend work: `backend/app/services/ai/model_provider.py` (new severity field in the prediction contract), `treatment_service.py` (use it instead of the coarse comparison)
- Database/migration work: new `ai_analyses.severity_score` column
- Mobile work: surface severity trend once available
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new fake-provider tests with a severity value once the model contract supports it
- Verification method: automated test for the mechanism; real-world accuracy would be ENVIRONMENT_DEPENDENT/FUTURE, same caveat as disease diagnosis generally

### D40-05 — "What should I do today?"
- Domain: 40 (Voice)
- Scenario ID: D40-05
- Exact scenario name: "What should I do today?"
- Current implementation status: Partial
- Existing relevant files/classes/functions: `backend/app/services/assistant/intent_router.py:46-63` (no keyword match, falls to `GENERAL_AGRICULTURE`); `assistant_extras_service.get_daily_summary()` (`GET /assistant/daily-summary`) — the dedicated Daily Briefing feature that DOES answer this correctly
- Missing component: The chatbot's own intent router has no pattern for this exact phrasing — asking it in the chat produces an honest "I don't have enough information" non-answer instead of routing to the Daily Briefing content
- Required implementation: Add a new `Intent.DAILY_BRIEFING` keyword pattern (e.g. "what should i do today", "what's next", "today's plan") to `intent_router.py`, whose handler calls the existing `assistant_extras_service.get_daily_summary()` and returns its composed text through the normal chat response path — no new data source, just routing the existing chat interface to the existing Daily Briefing logic
- Dependencies: Purely additive to D40-06 (Voice help)'s existing intent-router pattern; no other scenario depends on it
- Backend work: `backend/app/services/assistant/intent_router.py` (new intent + keyword list), `backend/app/services/assistant/` handler wiring to call `get_daily_summary`
- Database/migration work: none — reuses all existing reads
- Mobile work: none — same chat UI, same Listen mechanism
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same online-only chat request as today
- Security/RBAC impact: none — purely additive routing
- Tests required: a new `test_assistant_chat.py` test asserting the exact phrasing routes to daily-summary content instead of the generic fallback
- Verification method: automated test (backend pytest)

### D41-02 — Auto-detect location option
- Domain: 41 (Local Language)
- Scenario ID: D41-02
- Exact scenario name: Auto-detect location option
- Current implementation status: Partial
- Existing relevant files/classes/functions: `location_language_resolver.dart:37-55,74-87` (GPS→state→language map, audio-only); `language_selection_screen.dart` (manual-pick-only, no detect option)
- Missing component: Auto-detect-from-location exists only for spoken AUDIO language (`VoiceLanguageMode.location`), not for the UI display language
- Required implementation: Add a "detect from my location" option to `LanguageSelectionScreen`, reusing the existing `LocationLanguageResolver.resolveLanguageCode()` to set `LocaleController`'s display language, not just the voice mode
- Dependencies: Directly reuses D41-08's existing resolver; no scenario depends on this
- Backend work: none — this is a client-only change (same as `LocaleController.setLocale()` today)
- Database/migration work: none
- Mobile work: `mobile/lib/features/auth/language_selection_screen.dart` (add detect-from-location option), reuse `location_language_resolver.dart`
- Automation work: none
- Notification work: none
- Offline/sync impact: none — GPS resolution already falls back gracefully offline (existing `location_language_resolver.dart:74-87` behavior)
- Security/RBAC impact: none — same consent-gated GPS access already used for audio mode
- Tests required: a Flutter widget test mirroring `voice_language_controller_test.dart`'s location-mode tests, applied to the display-language controller
- Verification method: automated test (Flutter widget test)

### D41-03 — Local-language UI
- Domain: 41 (Local Language)
- Scenario ID: D41-03
- Exact scenario name: Local-language UI
- Current implementation status: Partial
- Existing relevant files/classes/functions: all 7 `.arb` files (651/651 keys matched, 0 missing/extra); `PROJECT_STATUS.md:963` (dealer-marketplace screens use hardcoded English)
- Missing component: `.arb`-covered surface (voice/weather/task/assistant/daily-briefing/auth) is fully and correctly localized, but the dealer-marketplace screens and "most farm/crop screens" are not — the app is not uniformly localized
- Required implementation: Extract hardcoded strings from the dealer-marketplace screens (and any other non-`.arb`-covered screen) into new `.arb` keys across all 7 language files, following the exact pattern already used elsewhere
- Dependencies: None — purely additive localization work, screen by screen
- Backend work: none
- Database/migration work: none
- Mobile work: `mobile/lib/features/dealer_market/*` and other non-localized screens — replace hardcoded strings with `AppLocalizations.of(context)!.xxx`
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: extend the existing key-set diff check (651/651 parity) to cover the new keys once added
- Verification method: automated check (the same `.arb` key-set diff already used this session) + manual visual verification per screen

### D41-04 — Local-language advisory
- Domain: 41 (Local Language)
- Scenario ID: D41-04
- Exact scenario name: Local-language advisory
- Current implementation status: Partial
- Existing relevant files/classes/functions: `farmer_messages.py:89-160` (8 `daily_summary_*` keys translated for all 6 non-English languages, DRAFT/unreviewed); `farmer_messages.py:164-179` (`get_message()` fallback chain); `docs/LOCALIZATION.md:46-50` (deliberate scope trade-off)
- Missing component: Of 53 template keys, 45 (`ai_result_*`, `rain_alert`, `CASE_*`, most `assistant_*`) have only an `en` entry — a non-English farmer receives these in English by explicit, disclosed design pending native-speaker review
- Required implementation: Commission/perform native-speaker review and translation for the remaining 45 keys across all 6 non-English languages, following the same DRAFT-flagged process already used for the 8 `daily_summary_*` keys
- Dependencies: None technical — this is a content/translation-review task, not an engineering blocker; the fallback mechanism (`get_message()`) already supports adding translations incrementally with zero code change
- Backend work: `backend/app/services/farmer_messages.py` — add translated strings only (no logic change)
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none — same notification templates, just more languages populated
- Offline/sync impact: none
- Security/RBAC impact: none — this is precisely the kind of agricultural/safety text the project deliberately does NOT auto-translate without review, so any change here must go through the same manual-review discipline, not be automated
- Tests required: extend `test_ai_localization.py` to assert non-English text once added for a given key (currently these tests only assert the honest English-fallback behavior)
- Verification method: live manual verification (native-speaker review is inherently non-automatable) followed by automated regression tests once translations land

### D42-03 — Disease education
- Domain: 42 (Education)
- Scenario ID: D42-03
- Exact scenario name: Disease education
- Current implementation status: Partial
- Existing relevant files/classes/functions: `farmer_messages.py:52` (`ai_result_disease_detected`/`assistant_disease_detected`, 1-sentence classification label); `GET /ai/analysis/{id}/localized`; `KnowledgeEntry` model (`knowledge_entry.py`, empty)
- Missing component: The disease-result text is a bare classification label ("not a confirmed diagnosis"), not educational content — no cause/lifecycle/treatment explanation, no image/audio/video, no `KnowledgeEntry` backing
- Required implementation: Populate `KnowledgeEntry` with vetted, licensed content per disease class, then link `AIAnalysisResponse.predicted_class` to a `GET /knowledge/{disease_class}` lookup surfaced alongside the result
- Dependencies: Directly blocked on D42-01/06/10 (Crop education / Text format / Expert-verified content) — the entire `KnowledgeEntry` domain must be seeded first; this scenario cannot be built in isolation
- Backend work: `backend/app/services/knowledge_service.py` (new), `backend/app/api/v1/knowledge.py` (new), `ai_analysis_service.py` (link result to entry)
- Database/migration work: populate existing empty `knowledge_entries` table (schema already exists — no new migration, just data + a serving endpoint)
- Mobile work: crop-photo result screen — add an "Learn more" link/section
- Automation work: none
- Notification work: none
- Offline/sync impact: none — read-only content, could be cached client-side for offline reading (optional enhancement, not required)
- Security/RBAC impact: none — read-only public reference content
- Tests required: new tests for the knowledge-lookup endpoint once content exists
- Verification method: automated test once implemented; content quality itself requires live/manual review (licensed-content sourcing, same discipline as `LicenseStatus` implies)

### D44-02 — Dealer
- Domain: 44 (Nearby Services)
- Scenario ID: D44-02
- Exact scenario name: Dealer
- Current implementation status: Partial
- Existing relevant files/classes/functions: `features/dealer_market/*` (226/226 Flutter tests passing per `PROJECT_STATUS.md:967`); `DealerBusinessProfile`, `DealerProduct`; `PROJECT_STATUS.md:959` ("no location filter")
- Missing component: Dealer discovery is a real, well-tested catalog/price-comparison marketplace, but has no geo/"nearby" proximity search — unlike Expert matching (D44-01), which is district/state-scoped
- Required implementation: Add `state_id`/`district_id` (or lat/lon) to `DealerBusinessProfile` and a location filter to `GET /products`/dealer search, mirroring the state/district matching already used in `nearby_professional_service.py`/`_build_match_criteria` for experts
- Dependencies: None blocking; purely additive to the existing dealer marketplace
- Backend work: `backend/app/models/dealer_business_profile.py` (location columns), `backend/app/services/dealer_product_service.py` (location filter), `backend/app/api/v1/products.py`
- Database/migration work: new `dealer_business_profiles.state_id`/`district_id` columns + migration, reusing the existing `location_repository`/state-district tables
- Mobile work: `mobile/lib/features/dealer_market/` — add a location filter UI element
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same online catalog-browsing flow
- Security/RBAC impact: none — additive filter
- Tests required: new tests mirroring the existing dealer-market test suite, plus a location-filter-specific test
- Verification method: automated test (backend pytest + Flutter widget test)

### D44-03 — Seed supplier
- Domain: 44 (Nearby Services)
- Scenario ID: D44-03
- Exact scenario name: Seed supplier
- Current implementation status: Partial
- Existing relevant files/classes/functions: `get_seed_products` assistant tool / `FIND_SEED` intent; `GET /products` (client-side category filter only, `PROJECT_STATUS.md:959`)
- Missing component: Seeds are purchasable via the generic dealer marketplace, but there is no distinct "find a nearby seed supplier" service type — same underlying gap as D44-02 (no geo search), plus category filtering is client-side only
- Required implementation: Move category filtering server-side (`GET /products?category=seed`) and apply the same location-filter work as D44-02
- Dependencies: Directly depends on D44-02's location-filter work being built first (shared mechanism)
- Backend work: `backend/app/api/v1/products.py` (server-side category + location filter params)
- Database/migration work: none beyond D44-02's location columns
- Mobile work: `mobile/lib/features/dealer_market/` — move category filter to a server query param
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new backend test for server-side category+location filtering
- Verification method: automated test

### D44-04 — Fertilizer supplier
- Domain: 44 (Nearby Services)
- Scenario ID: D44-04
- Exact scenario name: Fertilizer supplier
- Current implementation status: Partial
- Existing relevant files/classes/functions: same dealer-catalog mechanism as D44-02/03; `LedgerEntryCategory.FERTILIZER` (`models/ledger_entry.py:59`, cost-tracking only, unrelated)
- Missing component: identical gap to D44-03, for the fertilizer category — no distinct "nearby fertilizer supplier" search
- Required implementation: same fix as D44-03, applied to the fertilizer category
- Dependencies: same as D44-03 — shares the D44-02 location-filter mechanism
- Backend work: same as D44-03
- Database/migration work: none beyond D44-02
- Mobile work: same as D44-03
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same test plan as D44-03, fertilizer-category variant
- Verification method: automated test

### D46-03 — Cost (Labour)
- Domain: 46 (Labour)
- Scenario ID: D46-03
- Exact scenario name: Cost
- Current implementation status: Partial
- Existing relevant files/classes/functions: `LedgerEntryCategory.LABOR` (`models/ledger_entry.py:61`); `POST /cost-estimates` (real, existing, reused by `CropCostEstimatesScreen`)
- Missing component: A farmer can record labour *spend* after the fact via the generic cost-ledger feature, but there is no labour marketplace rate/quote feature — this only satisfies "cost" in the bookkeeping sense, not "what does hiring labour cost nearby"
- Required implementation: Blocked on the entire Labour domain (D46-01/02/04/05/06, all MISSING) being built first — a rate/quote feature presupposes a labour-marketplace listing to quote against
- Dependencies: Depends on D46-01 (Labour requirement posting) and D46-02 (Availability) existing first
- Backend work: see D46-01's proposal below — a new `labour_listing`/`labour_rate` concept
- Database/migration work: see D46-01
- Mobile work: see D46-01
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none beyond what a new labour marketplace would need (see D46-01)
- Tests required: none until the underlying domain exists
- Verification method: automated test, once the underlying Labour domain is built

## 3. Missing — full itemized (EVERY row, no aggregation)

### D28-01 — Pest risk
- Domain: 28 (Pest)
- Scenario ID: D28-01
- Exact scenario name: Pest risk
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_risk_service.py:38-48` (factor list has disease/expert-case/task/financial/weather only, confirmed by reading the full file)
- Missing component: No pest-risk factor of any kind — pest is not modeled as a concept anywhere, so there is nothing to derive a risk factor from
- Required implementation: Build the foundational pest domain first (D28-02/03/04), then add a `_pest_factor` contributor to `crop_risk_service._aggregate`, following the exact pattern of `_recent_disease_factor`/`_disease_recurrence_factor`
- Dependencies: Hard-blocked on D28-02/03/04 (Pest observation/photo/diagnosis) existing first; would extend D27-01 (Disease risk)
- Backend work: `backend/app/services/crop_risk_service.py` (new factor function)
- Database/migration work: none beyond what D28-02/04 introduce
- Mobile work: crop-risk screen — surface the new factor once it exists
- Automation work: none — matches D27-01's on-demand GET computation
- Notification work: none — read-only, matches existing pattern
- Offline/sync impact: none
- Security/RBAC impact: none — additive, same ownership scoping as D27-01
- Tests required: unit tests mirroring `test_crop_risk.py`'s disease-factor tests
- Verification method: automated test (backend pytest)

### D28-02 — Pest observation
- Domain: 28 (Pest)
- Scenario ID: D28-02
- Exact scenario name: Pest observation
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_health_case.py:41-45` (`CaseReason` enum, no pest-related value)
- Missing component: No pest-specific case reason, model, or field anywhere
- Required implementation: A new `PestObservation` concept — either a new `CaseReason.PEST_SUSPECTED` value reusing `CropHealthCase`, or a distinct `PestObservation` model if pest needs its own lifecycle separate from disease cases
- Dependencies: Foundational — D28-01/03/04/05/06/07 all depend on this existing first
- Backend work: `backend/app/models/crop_health_case.py` (new enum value) or a new `backend/app/models/pest_observation.py`; corresponding service/schema/API
- Database/migration work: new enum value migration, or a new `pest_observations` table + migration
- Mobile work: case-creation screen — add a pest-related reason option
- Automation work: none
- Notification work: reuses existing `CASE_CREATED`/`CASE_ASSIGNED` pattern if built on `CropHealthCase`
- Offline/sync impact: none — same online-only case creation as today
- Security/RBAC impact: none — same consent/ownership scoping as existing cases
- Tests required: new tests mirroring `test_cases.py`'s case-creation tests, pest-reason variant
- Verification method: automated test

### D28-03 — Pest photo
- Domain: 28 (Pest)
- Scenario ID: D28-03
- Exact scenario name: Pest photo
- Current implementation status: Missing
- Existing relevant files/classes/functions: `backend/app/models/crop_photo.py` (no "purpose"/category field); `CropPhotoSession` docstring (disease-check photo types only)
- Missing component: No field distinguishing a pest photo from a disease photo
- Required implementation: Add a `photo_purpose` enum (`disease`/`pest`) to `CropPhoto`, defaulting to `disease` for backward compatibility
- Dependencies: Depends on D28-02 existing (a pest photo needs a pest observation/case to attach to)
- Backend work: `backend/app/models/crop_photo.py`, `backend/app/schemas/crop_photo.py`, `crop_photo_service.py`
- Database/migration work: new `crop_photos.photo_purpose` column + migration + backfill default
- Mobile work: photo-capture flow — let the farmer indicate pest vs. disease purpose
- Automation work: none
- Notification work: none
- Offline/sync impact: additive field on the existing offline-capable upload queue — no new offline-handling logic needed
- Security/RBAC impact: none
- Tests required: new tests mirroring `test_crop_photos.py`'s upload tests, purpose-field variant
- Verification method: automated test

### D28-04 — Pest diagnosis
- Domain: 28 (Pest)
- Scenario ID: D28-04
- Exact scenario name: Pest diagnosis
- Current implementation status: Missing
- Existing relevant files/classes/functions: `model_provider.py:53-64` (`predict_disease`/`predict_stage` only, no pest method); `ai_analysis.py:48-56` (`ResultStatus` has no `PEST_DETECTED` value)
- Missing component: No pest-diagnosis model method or result status
- Required implementation: Add `predict_pest(image_bytes, crop_name)` to `ModelProvider` (and `NotConfiguredModelProvider`/any fake provider), a new `ResultStatus.PEST_DETECTED`, and a parallel branch in `PredictionValidator` mirroring the disease-diagnosis decision order exactly
- Dependencies: Depends on D28-02/03 existing; blocked on the same "no real trained model" constraint as disease diagnosis (D27-04) — would resolve to `AI_UNAVAILABLE` in this environment just like disease diagnosis does today
- Backend work: `backend/app/services/ai/model_provider.py`, `prediction_validator.py`, `ai_analysis_service.py`, `ai_analysis.py` (new enum value + column if pest confidence differs from disease confidence)
- Database/migration work: extend `ai_analyses` or add a sibling `pest_analyses` table, depending on whether pest and disease share one analysis record or need independent ones
- Mobile work: crop-photo analyze flow — support pest-purpose photos routing to this new pipeline
- Automation work: none
- Notification work: none new — reuses existing case-notification pattern once pest cases can be created
- Offline/sync impact: none — same synchronous analyze-request flow as disease diagnosis
- Security/RBAC impact: none — additive
- Tests required: new fake-provider tests mirroring the full `test_ai_analysis.py`/`test_ai_model_components.py` suite, pest variant
- Verification method: automated test for the pipeline; real diagnostic capability would be ENVIRONMENT_DEPENDENT/FUTURE, same caveat as disease diagnosis

### D28-05 — Pest history
- Domain: 28 (Pest)
- Scenario ID: D28-05
- Exact scenario name: Pest history
- Current implementation status: Missing
- Existing relevant files/classes/functions: `health_timeline_service.py` (aggregates only disease-related `ai_analysis`/`case`/`treatment` events)
- Missing component: No pest-diagnosis result exists to aggregate into a timeline
- Required implementation: Once D28-04 exists, add a pest-event branch to `health_timeline_service`'s aggregation, mirroring the disease-event branch exactly
- Dependencies: Hard-blocked on D28-04
- Backend work: `backend/app/services/health_timeline_service.py`
- Database/migration work: none beyond D28-04's
- Mobile work: health-timeline screen — render the new event type
- Automation work: none
- Notification work: none
- Offline/sync impact: none — read-only, same as D27-05
- Security/RBAC impact: none
- Tests required: mirrors `test_health_timeline.py`'s existing disease-event tests
- Verification method: automated test

### D28-06 — Pest recommendation
- Domain: 28 (Pest)
- Scenario ID: D28-06
- Exact scenario name: Pest recommendation
- Current implementation status: Missing
- Existing relevant files/classes/functions: same reasoning as D27-06 (deliberate treatment/recommendation exclusion), compounded by no pest concept existing at all
- Missing component: No pest concept to recommend against, and even if it existed, this project's `safety_validator.py:12-19` structurally blocks any prescription-style suggestion
- Required implementation: Not recommended to build as a "recommendation" — if D28-04 is ever built, this scenario should be resolved the same way as D27-06 (a deliberate FUTURE/safety-deferred exclusion), not implemented as an AI-suggested treatment
- Dependencies: Blocked on D28-04; would inherit D27-06's FUTURE justification once pest diagnosis exists, rather than becoming a real MISSING-to-build item
- Backend work: none recommended — `safety_validator.py`'s pattern list would need pest-specific chemical-name blocking added if D28-04 is built, mirroring its existing pesticide/fungicide patterns
- Database/migration work: none
- Mobile work: none
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — this is precisely the kind of prescription request the project's safety guardrails must continue to block
- Tests required: if D28-04 is built, a test mirroring `safety_validator.py`'s existing prescription-blocking tests, pest variant
- Verification method: not applicable until D28-04 exists; if built, should land as FUTURE (safety-deferred) not VERIFIED, matching D27-06's precedent

### D28-07 — Follow-up (Pest)
- Domain: 28 (Pest)
- Scenario ID: D28-07
- Exact scenario name: Follow-up
- Current implementation status: Missing
- Existing relevant files/classes/functions: `treatment_service.py:38` (`TreatmentFollowUp` only links to `AIAnalysis.result_status` healthy/disease_detected)
- Missing component: No pest-diagnosis result exists to follow up on
- Required implementation: Once D28-04 exists, extend `TreatmentFollowUp`'s effectiveness comparison to accept a pest-result pair, mirroring `treatment_service.get_effectiveness`'s disease logic exactly
- Dependencies: Hard-blocked on D28-04
- Backend work: `backend/app/services/treatment_service.py`
- Database/migration work: none beyond D28-04's
- Mobile work: none beyond what D28-04 introduces
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: mirrors `test_treatments.py`'s effectiveness tests, pest variant
- Verification method: automated test

### D29-03 — Plant-part identification
- Domain: 29 (AI Diagnosis)
- Scenario ID: D29-03
- Exact scenario name: Plant-part identification
- Current implementation status: Missing
- Existing relevant files/classes/functions: `photo_guidance_screen.dart:21` (pre-capture tip only); repo-wide search for `plant_part`/"plant part" returns zero matches
- Missing component: No `plant_part` field/logic anywhere
- Required implementation: same underlying fix as D30-04 (Wrong plant part) — a plant-part classifier would serve both scenarios; see D30-04's full proposal
- Dependencies: Shares implementation with D30-04
- Backend work: see D30-04
- Database/migration work: see D30-04
- Mobile work: see D30-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D30-04
- Verification method: automated test once built; real accuracy would be ENVIRONMENT_DEPENDENT/FUTURE if model-based

### D29-05 — Pest detection
- Domain: 29 (AI Diagnosis)
- Scenario ID: D29-05
- Exact scenario name: Pest detection
- Current implementation status: Missing
- Existing relevant files/classes/functions: same evidence as D28-04 — no `predict_pest` method, no `PEST_DETECTED` result status
- Missing component: identical to D28-04
- Required implementation: same as D28-04 (this is the same underlying gap described from the "AI Diagnosis" domain's perspective rather than the "Pest" domain's)
- Dependencies: same as D28-04
- Backend work: same as D28-04
- Database/migration work: same as D28-04
- Mobile work: same as D28-04
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D28-04
- Verification method: same as D28-04

### D29-06 — Nutrient deficiency
- Domain: 29 (AI Diagnosis)
- Scenario ID: D29-06
- Exact scenario name: Nutrient deficiency
- Current implementation status: Missing
- Existing relevant files/classes/functions: repo-wide search for "nutrient" outside `crop_variety.py` (unrelated) returns nothing; no `ResultStatus` value, no `ModelProvider` method
- Missing component: No nutrient-deficiency concept anywhere in the AI pipeline
- Required implementation: Add `predict_nutrient_deficiency(image_bytes, crop_name)` to `ModelProvider`, a new `ResultStatus.NUTRIENT_DEFICIENCY_DETECTED`, and a parallel `PredictionValidator` branch, mirroring the disease-diagnosis decision order
- Dependencies: Blocked on the same "no real trained model" constraint as disease/pest diagnosis
- Backend work: `backend/app/services/ai/model_provider.py`, `prediction_validator.py`, `ai_analysis_service.py`, `ai_analysis.py`
- Database/migration work: extend `ai_analyses` or add a sibling table
- Mobile work: crop-photo analyze flow — new result type rendering
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new fake-provider tests mirroring the disease-diagnosis test suite
- Verification method: automated test for the pipeline; real accuracy ENVIRONMENT_DEPENDENT/FUTURE

### D30-05 — Duplicate photo
- Domain: 30 (Image Quality)
- Scenario ID: D30-05
- Exact scenario name: Duplicate photo
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_photo.py:67,97` (`client_upload_id` uniqueness — dedupes retries of the same upload attempt only); repo-wide search for `phash`/`perceptual`/`image_hash` returns nothing
- Missing component: No perceptual-hashing or similar mechanism to detect a farmer photographing the same subject twice as two distinct captures
- Required implementation: Add a perceptual hash (e.g. average-hash or dHash) computed at upload time, stored on `CropPhoto`, with a similarity check against recent photos for the same crop cycle flagged as `quality_reasons: possible_duplicate` (a warning, not a hard block)
- Dependencies: None — purely additive to the existing upload pipeline
- Backend work: `backend/app/services/image_quality.py` (new hash function + comparison), `crop_photo_service.py`
- Database/migration work: new `crop_photos.perceptual_hash` column + index
- Mobile work: surface the new `quality_reasons` value via the existing friendly-message mapping
- Automation work: none — runs synchronously at upload like existing checks
- Notification work: none
- Offline/sync impact: none — same synchronous upload-time check
- Security/RBAC impact: none
- Tests required: unit tests mirroring `test_image_pipeline.py`'s existing quality-flag tests
- Verification method: automated test

### D30-06 — Old photo
- Domain: 30 (Image Quality)
- Scenario ID: D30-06
- Exact scenario name: Old photo
- Current implementation status: Missing
- Existing relevant files/classes/functions: `crop_photo.py:109` (EXIF stripped before capture-time metadata is read); `CROP_PHOTO_MODULE.md` "Known limitations"
- Missing component: `capture_timestamp` is never populated, so no staleness/age check is possible even in principle
- Required implementation: Populate `capture_timestamp` from the device clock at the moment of capture (before EXIF stripping, client-side), store it on `CropPhoto`, then add a staleness check (e.g. flag if capture_timestamp is more than N days before upload) to `image_quality.py`
- Dependencies: None — but must be careful not to reintroduce an EXIF/GPS leak while capturing this one timestamp field (the project deliberately strips EXIF for privacy)
- Backend work: `backend/app/models/crop_photo.py` (already has the column per the doc, just unpopulated), `image_quality.py` (new staleness check)
- Database/migration work: none if `capture_timestamp` column already exists (per docs) — otherwise add it
- Mobile work: `mobile/lib/features/crop_photo` capture flow — read and send device capture time explicitly (not via EXIF) at the moment of photo capture
- Automation work: none
- Notification work: none
- Offline/sync impact: capture_timestamp must be set at capture time, before any queued/delayed upload, so staleness reflects when the photo was actually taken, not when it was uploaded
- Security/RBAC impact: none — must continue to avoid leaking any other EXIF/GPS metadata
- Tests required: unit test asserting a photo captured N+1 days ago is flagged, and one captured today is not
- Verification method: automated test

### D32-04 — Ask additional question
- Domain: 32 (Unknown Diagnosis)
- Scenario ID: D32-04
- Exact scenario name: Ask additional question
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — the flow is strictly one-shot photo-in/result-out; the separate assistant chatbot is a deterministic intent router for unrelated Q&A, not a diagnosis-clarification dialogue
- Missing component: No mechanism exists for the AI/system to ask the farmer a clarifying follow-up question (e.g. "which part of the plant?", "how long has this been visible?")
- Required implementation: A structured clarification-question flow: when `result_status` is UNKNOWN/LOW_CONFIDENCE/CROP_MISMATCH, present the farmer with a small fixed set of clarifying questions (from a predefined, non-fabricated question bank, not free-form AI-generated text) whose answers are stored alongside the analysis and could feed a second analysis pass
- Dependencies: Would need to avoid the project's existing "never a free-form AI sentence" discipline (`ai_result_localization_service.py`) — questions must be from a fixed, reviewed bank, same discipline as `confidence_wording` templates
- Backend work: new `backend/app/models/analysis_clarification.py`, `ai_analysis_service.py` (present questions on UNKNOWN/LOW_CONFIDENCE), new schema/API
- Database/migration work: new `analysis_clarifications` table
- Mobile work: crop-photo result screen — a clarification-question form
- Automation work: none
- Notification work: none
- Offline/sync impact: none — same online-only analyze flow
- Security/RBAC impact: none
- Tests required: new tests asserting the clarification flow never fabricates a diagnosis from the answers alone
- Verification method: automated test

### D36-04 — Farmer acknowledgement
- Domain: 36 (Expert Recommendation)
- Scenario ID: D36-04
- Exact scenario name: Farmer acknowledgement
- Current implementation status: Missing
- Existing relevant files/classes/functions: `POST /cases/{id}/feedback` (`professional_feedback` table — a rating/helpfulness survey, semantically distinct from acknowledgement); `case_review.py:7` docstring comment only
- Missing component: No endpoint exists for a farmer to acknowledge/read-receipt a recommendation
- Required implementation: Add a `read_at`/`acknowledged_at` timestamp to `CaseReview` (or a lightweight `POST /cases/{id}/reviews/{review_id}/acknowledge` endpoint), distinct from the existing feedback-survey mechanism
- Dependencies: None — additive to the existing review flow
- Backend work: `backend/app/models/case_review.py` (new column), `backend/app/api/v1/cases.py` (new endpoint), `case_service.py`
- Database/migration work: new nullable `case_reviews.acknowledged_at` column
- Mobile work: case-detail screen — a "Mark as read"/acknowledge action
- Automation work: none
- Notification work: none new
- Offline/sync impact: none — same online-only case interaction pattern
- Security/RBAC impact: none — farmer can only acknowledge their own case's review, same ownership scoping as everything else
- Tests required: new test asserting acknowledgement is farmer-owner-scoped and idempotent
- Verification method: automated test

### D36-06 — Expert identity
- Domain: 36 (Expert Recommendation)
- Scenario ID: D36-06
- Exact scenario name: Expert identity
- Current implementation status: Missing
- Existing relevant files/classes/functions: `schemas/case.py:49-58` (`CaseReviewResponse` — only `reviewer_role`, never `professional_id`/name); `api/v1/cases.py:142-144` (`AuditLog` rows return only `action`/`actor_role`)
- Missing component: Farmer never learns which named individual reviewed their case — this is confirmed as a deliberate architectural characteristic ("the farmer-facing CaseResponse has no field for expert identity"), not an oversight
- Required implementation: This is a genuine product/privacy decision, not a pure engineering gap — if the project decides to expose expert identity, add `professional_display_name` to `CaseReviewResponse`, sourced from `ProfessionalProfile`, with the professional's own consent to be named
- Dependencies: Would need a new professional-side consent flag ("show my name to farmers") before implementation, since the current design deliberately withholds identity
- Backend work: `backend/app/models/professional_profile.py` (consent flag), `backend/app/schemas/case.py`, `case_service.py`
- Database/migration work: new `professional_profiles.show_name_to_farmers` boolean
- Mobile work: case-detail screen — display name when consented
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: this is the one Missing item in this domain where the "impact" is real: exposing identity changes the professional's privacy posture and must be opt-in, not a default
- Tests required: new test asserting identity is only exposed when the professional has consented
- Verification method: automated test + a product decision on whether this should be built at all

### D36-07 — Recommendation version
- Domain: 36 (Expert Recommendation)
- Scenario ID: D36-07
- Exact scenario name: Recommendation version
- Current implementation status: Missing
- Existing relevant files/classes/functions: `case_reviews` table (multiple rows per `case_id` for second opinions, no versioning concept)
- Missing component: No "version" field, no supersession logic — each review is an independent row, not a version chain
- Required implementation: Add a `supersedes_review_id` FK on `CaseReview`, set when a second-opinion review is explicitly meant to revise a prior one (vs. simply being an additional independent opinion)
- Dependencies: Overlaps with D36-03 (Evidence) — both touch how multiple reviews per case should relate to each other; consider designing together
- Backend work: `backend/app/models/case_review.py` (new FK), `case_service.py` (second-opinion flow)
- Database/migration work: new nullable `case_reviews.supersedes_review_id` self-referential FK
- Mobile work: case-detail screen — render a version chain if present
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test asserting the FK only ever references a review for the same case
- Verification method: automated test

### D37-01 — Recommendation creates task
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-01
- Exact scenario name: Recommendation creates task
- Current implementation status: Missing
- Existing relevant files/classes/functions: `case_service.py`/`treatment_service.py` (zero `Task` import/creation, confirmed by grep); `task.py:1-18` docstring; `task.py:57-59` (`tasks` has no FK to `crop_health_cases`/`case_reviews`)
- Missing component: No code path exists connecting a `CaseReview` outcome to task creation — this is an explicit, deliberate deferral ("no crop-calendar, no validated agronomic rule dataset"), not an oversight
- Required implementation: If ever built, must avoid inventing an agronomic rule dataset — the safest version is a farmer-confirmed suggestion: when a review outcome implies action (e.g. `field_visit_required`), prompt the farmer with an optional "Create a task for this?" action that pre-fills a generic task, never an auto-generated one with fabricated agronomic content
- Dependencies: D37-02 through D37-06 all depend on this existing first
- Backend work: `backend/app/models/task.py` (new nullable `source_case_review_id` FK), `case_service.py` (surface a "suggested task" hint in the review response, not auto-create), `backend/app/api/v1/tasks.py` (accept the optional FK at creation)
- Database/migration work: new nullable `tasks.source_case_review_id` FK + migration
- Mobile work: case-detail screen — "Create a task for this recommendation" button that pre-fills the existing task-creation form
- Automation work: none — farmer-confirmed, not auto-created, consistent with the project's no-fabricated-agronomic-task discipline
- Notification work: none new
- Offline/sync impact: none — same online-only task creation as today
- Security/RBAC impact: none
- Tests required: new test asserting a task created this way carries the FK, and that no task is ever auto-created without farmer confirmation
- Verification method: automated test

### D37-02 — Due date
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-02
- Exact scenario name: Due date
- Current implementation status: Missing
- Existing relevant files/classes/functions: `task.py:68` (`due_date` stored as-is, never auto-derived)
- Missing component: As a "recommendation → due date" concept, this doesn't exist since no recommendation ever creates a task (D37-01)
- Required implementation: Once D37-01's farmer-confirmed task-creation flow exists, allow (but never require) the review to suggest a due date offset (e.g. "field visit recommended within 3 days") which pre-fills, not auto-sets, the `due_date` field on the farmer-confirmed task
- Dependencies: Hard-blocked on D37-01
- Backend work: `backend/app/schemas/case.py` (optional suggested-due-date hint on the review response)
- Database/migration work: none beyond D37-01's
- Mobile work: pre-fill the due-date field on the task-creation form from the hint
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: mirrors D37-01's test plan
- Verification method: automated test

### D37-03 — Priority
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-03
- Exact scenario name: Priority
- Current implementation status: **PARTIAL (this session, was Missing — the independent
  half is now VERIFIED, the recommendation-derived half remains blocked)**
- Fix applied this session: `Task.priority` (`TaskPriority` enum: low/medium/high, default
  medium), migration `a1b2c3d4e5f6`, farmer-settable at creation
  (`TaskCreateRequest.priority`), returned in `TaskResponse`. Tested:
  `test_tasks.py::test_task_priority_defaults_to_medium_and_is_settable`. This closes the
  "independent of whether it's ever populated from a recommendation" half this row's own
  citation called out as buildable now.
- Still genuinely missing: the "derived from a recommendation's urgency" half — correctly
  blocked on D37-01 (Recommendation creates task), which remains unbuilt (P2). Not
  reclassified VERIFIED because that half of the scenario's own wording is not yet
  satisfiable.
- Mobile work: not yet done — task list/detail screens should render priority; tracked as a
  follow-up.
- Verification method: automated test (the independent half only), confirmed passing

### D37-04 — Farmer notification
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-04
- Exact scenario name: Farmer notification
- Current implementation status: **VERIFIED (fixed this session via the same sweep as
  D9-16/D9-03, was Missing)**
- Same fix as D9-16/D9-03 (`task_service.run_overdue_task_alert_sweep`, `scheduler.py`'s
  `task_overdue_alert_sweep` job, `NotificationCategory.TASK_ALERT`) — this row's own
  citation named the exact same buildable-independently sweep, now built. No dependency on
  D37-01/02/03 as this row itself anticipated. See `docs/audit/FINAL_CANONICAL_group_A.md`'s
  D9-16 entry for the full evidence.
- Tests: same as D9-16 (`test_tasks.py::test_overdue_sweep_sends_one_alert_and_never_duplicates`,
  `::test_overdue_sweep_ignores_tasks_without_a_due_date`)
- Verification method: automated test, confirmed passing

### D37-05 — Completion
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-05
- Exact scenario name: Completion
- Current implementation status: Missing
- Existing relevant files/classes/functions: `task.py:50-55` (`CheckConstraint` enforcing `completed_at` on completion — generic task completion, 14 passing tests per `PROJECT_STATUS.md` Step 16)
- Missing component: Generic task completion works and is fully tested, but as a "recommendation task" completion specifically it does not exist, since no task is ever created from a recommendation (D37-01)
- Required implementation: No new completion logic needed — once D37-01 exists (tasks carry `source_case_review_id`), the existing `POST /tasks/{id}/complete` endpoint already handles completion correctly; this scenario resolves automatically once D37-01 is built
- Dependencies: Hard-blocked on D37-01 only — no independent engineering work
- Backend work: none beyond D37-01
- Database/migration work: none beyond D37-01
- Mobile work: none beyond D37-01
- Automation work: none
- Notification work: none new
- Offline/sync impact: none — reuses existing task-completion flow
- Security/RBAC impact: none
- Tests required: one new test asserting a recommendation-sourced task completes through the existing endpoint just like any other task
- Verification method: automated test

### D37-06 — Follow-up (Recommendation → Task)
- Domain: 37 (Recommendation → Task)
- Scenario ID: D37-06
- Exact scenario name: Follow-up
- Current implementation status: Missing
- Existing relevant files/classes/functions: none directly — the unrelated Treatment/Follow-up system (`treatment_service.py`) is the closest analog but has no FK back to `case_reviews`
- Missing component: Since no task is ever created from a recommendation (D37-01), there is necessarily no mechanism to follow up on one
- Required implementation: Once D37-01 exists, add an optional link from a completed recommendation-task back to a new `TreatmentFollowUp`/`TreatmentRecord`, letting the farmer report the outcome of acting on the recommendation, reusing `treatment_service.py`'s existing effectiveness-comparison logic rather than inventing a new one
- Dependencies: Hard-blocked on D37-01; would also connect to D38 (Follow-up)/D39 (Reinspection)'s existing machinery
- Backend work: `backend/app/models/treatment_record.py` (optional `source_task_id` FK), `treatment_service.py`
- Database/migration work: new nullable FK column
- Mobile work: task-completion screen — offer to start a follow-up
- Automation work: none
- Notification work: none new
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new test connecting a completed recommendation-task to a follow-up record
- Verification method: automated test

### D38-02 — Reminder (Follow-up)
- Domain: 38 (Follow-up)
- Scenario ID: D38-02
- Exact scenario name: Reminder
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — depends on D38-01's `next_check_due_date` (Partial, not yet built)
- Missing component: No reminder mechanism of any kind for a pending/overdue follow-up
- Required implementation: A new scheduler sweep (`treatment_followup_reminder_service.py`, following the exact `case_sla_service.py` pattern) that finds `TreatmentRecord`s whose `next_check_due_date` (once D38-01 adds it) is approaching/passed, and sends a `TREATMENT_FOLLOWUP_REMINDER` notification
- Dependencies: Hard-blocked on D38-01
- Backend work: new `backend/app/services/treatment_followup_reminder_service.py`, register in `scheduler.py`
- Database/migration work: none beyond D38-01's
- Mobile work: none required — reuses notification display
- Automation work: this IS the automation work — new scheduler job
- Notification work: new message key `TREATMENT_FOLLOWUP_REMINDER` in `farmer_messages.py`
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new sweep tests mirroring `case_sla_service`'s reminder-dedup tests
- Verification method: automated test

### D38-05 — Reschedule
- Domain: 38 (Follow-up)
- Scenario ID: D38-05
- Exact scenario name: Reschedule
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — depends on D38-01's `next_check_due_date` existing
- Missing component: There is nothing to reschedule since no scheduled follow-up date is ever stored
- Required implementation: Once D38-01 exists, add a `PATCH /treatments/{id}` (or a dedicated `POST /treatments/{id}/reschedule`) endpoint allowing the farmer to update `next_check_due_date`
- Dependencies: Hard-blocked on D38-01
- Backend work: `backend/app/api/v1/treatments.py` (new endpoint), `treatment_service.py`
- Database/migration work: none beyond D38-01's
- Mobile work: treatment-detail screen — a reschedule action
- Automation work: none — reuses D38-02's sweep once built
- Notification work: none new
- Offline/sync impact: none
- Security/RBAC impact: none — same ownership scoping as existing treatment endpoints
- Tests required: new test asserting reschedule updates the date and is owner-scoped
- Verification method: automated test

### D40-01 — Voice input
- Domain: 40 (Voice)
- Scenario ID: D40-01
- Exact scenario name: Voice input
- Current implementation status: Missing
- Existing relevant files/classes/functions: `mobile/pubspec.yaml` (only `flutter_tts ^4.2.0`, `geolocator ^13.0.2` — no STT package); `docs/VOICE_ASSISTANT.md:5-20,44` (documents intended architecture, explicitly discloses no Flutter work happened)
- Missing component: No `speech_to_text`/STT package, no recorder UI — the mic icon in `main_navigation_shell.dart:51` is only the Assistant tab's nav icon
- Required implementation: Add a device-native STT package (e.g. `speech_to_text` from pub.dev) mirroring the existing `VoiceService`/`FlutterTtsVoiceService` abstraction pattern — a new `SpeechToTextService` interface with a device-native implementation, catching all exceptions and returning an honest "unavailable" state rather than throwing (same discipline as `flutter_tts_voice_service.dart:42-44,87-89`)
- Dependencies: D40-02 (provider abstraction) and D40-03 (voice question reaching the assistant) both depend on this
- Backend work: none — `POST /assistant/chat` already accepts text and would treat recognized speech identically, per `docs/VOICE_ASSISTANT.md:11-15`'s own design intent
- Database/migration work: none
- Mobile work: new `mobile/lib/core/speech_to_text_service.dart` (interface) + device-native implementation; mic-tap-to-record UI in the assistant screen
- Automation work: none
- Notification work: none
- Offline/sync impact: STT itself would need to work offline where the OS supports it (device-native), mirroring the offline-capable TTS today
- Security/RBAC impact: requires mic permission — must follow the same honest-failure discipline as GPS permission handling elsewhere (`location_language_resolver.dart:74-87`)
- Tests required: new Flutter tests mirroring `voice_service_test.dart`'s 5 contract tests, against a fake STT implementation
- Verification method: automated test (Flutter widget/unit test) + live manual verification (device mic behavior varies by OS/device)

### D40-02 — Speech-to-text
- Domain: 40 (Voice)
- Scenario ID: D40-02
- Exact scenario name: Speech-to-text
- Current implementation status: Missing
- Existing relevant files/classes/functions: same evidence as D40-01; contrast with the real `VoiceService` TTS abstraction
- Missing component: No STT provider interface exists
- Required implementation: same as D40-01's proposed `SpeechToTextService` interface — this scenario IS that interface specifically (D40-01 is the recording UI, D40-02 is the abstraction layer)
- Dependencies: Built together with D40-01 in practice
- Backend work: none
- Database/migration work: none
- Mobile work: `mobile/lib/core/speech_to_text_service.dart` interface, mirroring `voice_service.dart`'s shape
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond D40-01's
- Security/RBAC impact: none beyond D40-01's mic-permission handling
- Tests required: contract tests against a fake implementation, mirroring `voice_service_test.dart`
- Verification method: automated test

### D40-03 — Voice question
- Domain: 40 (Voice)
- Scenario ID: D40-03
- Exact scenario name: Voice question
- Current implementation status: Missing
- Existing relevant files/classes/functions: `backend/app/schemas/assistant.py:12` (`ChatRequest`, real and already used by typed chat)
- Missing component: Blocked entirely on D40-01/02 — nothing produces text from audio yet, though the backend chat endpoint is ready to receive it once it exists
- Required implementation: Once D40-01/02 land, wire the recognized STT text directly into the existing `POST /assistant/chat` call — no new backend endpoint needed, per `docs/VOICE_ASSISTANT.md:11-15`'s own deliberate "no separate /assistant/voice endpoint" design
- Dependencies: Hard-blocked on D40-01/02
- Backend work: none — `ChatRequest`/`POST /assistant/chat` already handle this
- Database/migration work: none
- Mobile work: assistant screen — send STT output through the existing chat-send code path
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond D40-01/02's
- Security/RBAC impact: none
- Tests required: an integration test asserting STT output reaches chat identically to typed input (mobile-side, since backend already has full coverage for typed chat)
- Verification method: automated test once D40-01/02 exist; until then, not testable

### D42-01 — Crop education
- Domain: 42 (Education)
- Scenario ID: D42-01
- Exact scenario name: Crop education
- Current implementation status: Missing
- Existing relevant files/classes/functions: `backend/app/models/knowledge_entry.py:1-6` (`KnowledgeEntry` — RAG foundation, deliberately empty, "no vetted, licensed agricultural content source was available")
- Missing component: Zero rows in `knowledge_entries`, zero content-serving endpoint
- Required implementation: Source/license vetted agricultural content (this is fundamentally a content-acquisition task, not an engineering one), populate `KnowledgeEntry`, and build a `GET /knowledge`/`GET /knowledge/{id}` serving endpoint plus a `KnowledgeService`
- Dependencies: Foundational for D42-02 through D42-10 (all education scenarios depend on this)
- Backend work: `backend/app/services/knowledge_service.py` (new), `backend/app/api/v1/knowledge.py` (new)
- Database/migration work: none — schema already exists, this is a data-population task
- Mobile work: new education/library screen(s)
- Automation work: none
- Notification work: none
- Offline/sync impact: could be cached client-side for offline reading (optional)
- Security/RBAC impact: none — read-only public reference content, though `LicenseStatus`/`is_approved` gating (D42-10) must be enforced before serving anything
- Tests required: new tests for the knowledge-serving endpoint, once content exists
- Verification method: automated test once implemented; content sourcing itself requires live/manual licensing review

### D42-02 — Stage-specific education
- Domain: 42 (Education)
- Scenario ID: D42-02
- Exact scenario name: Stage-specific education
- Current implementation status: Missing
- Existing relevant files/classes/functions: `CropCycle.cultivation_status`/stage tracking (real, per `PROJECT_STATUS.md:384`); `KnowledgeEntry` (empty)
- Missing component: No educational content is tied to crop-cycle stages anywhere
- Required implementation: Once D42-01 exists, add a `crop_stage` tag/FK to `KnowledgeEntry` and filter served content by the farmer's current `CropCycle.cultivation_status`
- Dependencies: Hard-blocked on D42-01
- Backend work: `backend/app/models/knowledge_entry.py` (new tag field), `knowledge_service.py` (stage filter)
- Database/migration work: new `knowledge_entries.crop_stage` column
- Mobile work: education screen — filter/highlight by current stage
- Automation work: none
- Notification work: none
- Offline/sync impact: none beyond D42-01's
- Security/RBAC impact: none
- Tests required: new test asserting stage-filtered content matches the farmer's actual cycle stage
- Verification method: automated test

### D42-04 — Pest education
- Domain: 42 (Education)
- Scenario ID: D42-04
- Exact scenario name: Pest education
- Current implementation status: Missing
- Existing relevant files/classes/functions: `DiseaseClass` (AI-detection classification only); `KnowledgeEntry` (empty)
- Missing component: No educational content, same empty `KnowledgeEntry` table
- Required implementation: same as D42-01, pest-content variant, additionally blocked on D28 (Pest domain) existing at all if content is meant to link to a `PestClass` taxonomy
- Dependencies: D42-01 (content foundation) and, for linkage, D28-02/04 (pest domain existing)
- Backend work: same as D42-01
- Database/migration work: same as D42-01
- Mobile work: same as D42-01
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D42-01
- Verification method: same as D42-01

### D42-05 — Weather education
- Domain: 42 (Education)
- Scenario ID: D42-05
- Exact scenario name: Weather education
- Current implementation status: Missing
- Existing relevant files/classes/functions: `weather_alert_rules.py` (real, deterministic actionable warnings — not explainer content)
- Missing component: Practical weather alerts exist and are well-built, but no educational material about weather concepts themselves
- Required implementation: same as D42-01, weather-education-content variant — no engineering dependency on the alert system itself, purely a `KnowledgeEntry` content category
- Dependencies: D42-01
- Backend work: same as D42-01
- Database/migration work: same as D42-01
- Mobile work: same as D42-01
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D42-01
- Verification method: same as D42-01

### D42-06 — Text (education format)
- Domain: 42 (Education)
- Scenario ID: D42-06
- Exact scenario name: Text (education format)
- Current implementation status: Missing
- Existing relevant files/classes/functions: `knowledge_entry.py:39` (`content_summary` field exists, zero populated rows)
- Missing component: Field exists in schema, no data
- Required implementation: same as D42-01 — this scenario IS the base content-population task itself, viewed from the "format" angle
- Dependencies: same as D42-01 (this is essentially the same work)
- Backend work: same as D42-01
- Database/migration work: none — field already exists
- Mobile work: same as D42-01
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D42-01
- Verification method: same as D42-01

### D42-07 — Image (education format)
- Domain: 42 (Education)
- Scenario ID: D42-07
- Exact scenario name: Image (education format)
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — crop photos in this app are diagnostic uploads (AI analysis input), never educational reference images
- Missing component: No education-image model/screen found
- Required implementation: Add an `image_url`/asset reference field to `KnowledgeEntry`, populated alongside D42-01's content sourcing (licensed reference images, not farmer-uploaded diagnostic photos)
- Dependencies: D42-01
- Backend work: `backend/app/models/knowledge_entry.py` (new field), asset storage reuse (existing photo-storage abstraction, `storage.open_read` pattern from `crop_photo_service.py`)
- Database/migration work: new `knowledge_entries.image_url` column
- Mobile work: education screen — render reference images
- Automation work: none
- Notification work: none
- Offline/sync impact: could be cached (optional)
- Security/RBAC impact: none — must ensure licensed images only, respecting `LicenseStatus`
- Tests required: same as D42-01
- Verification method: same as D42-01

### D42-08 — Audio (education format)
- Domain: 42 (Education)
- Scenario ID: D42-08
- Exact scenario name: Audio (education format)
- Current implementation status: Missing
- Existing relevant files/classes/functions: `VoiceService` (TTS only ever reads back diagnostic/status/briefing text verbatim, never a separate educational audio track)
- Missing component: No education-specific audio content
- Required implementation: Once D42-01/06 populate `content_summary`, the existing `VoiceService.speak()` can already read it back verbatim — no new audio-infrastructure work needed, just wiring the education screen's "Listen" button to the existing TTS mechanism (same pattern as every other Listen call site)
- Dependencies: D42-01/06 (needs text content to read)
- Backend work: none
- Database/migration work: none beyond D42-01's
- Mobile work: education screen — add a Listen button reusing `VoiceLanguageController.resolveLanguageCode()`, same as the 5 existing call sites
- Automation work: none
- Notification work: none
- Offline/sync impact: none — works fully offline once content is cached and a voice pack is installed, same as every other Listen call site
- Security/RBAC impact: none
- Tests required: a widget test mirroring the existing Listen-button tests, education-screen variant
- Verification method: automated test

### D42-09 — Video where supported
- Domain: 42 (Education)
- Scenario ID: D42-09
- Exact scenario name: Video where supported
- Current implementation status: Missing
- Existing relevant files/classes/functions: `mobile/pubspec.yaml` (no `video_player`/any video package; grep confirms zero hits)
- Missing component: No video capability anywhere in the app
- Required implementation: Add the `video_player` package (from the CDN-equivalent for Flutter — pub.dev), a new `KnowledgeEntry.video_url` field, and an education-screen video player widget
- Dependencies: D42-01 (content), plus a real decision on hosting/licensing video content (heavier lift than text/image)
- Backend work: `backend/app/models/knowledge_entry.py` (new field)
- Database/migration work: new `knowledge_entries.video_url` column
- Mobile work: add `video_player` dependency, new video-playback widget
- Automation work: none
- Notification work: none
- Offline/sync impact: video would likely need explicit download-for-offline handling given file size — a bigger lift than the other formats
- Security/RBAC impact: none — same licensing discipline as images
- Tests required: new widget tests for the video player
- Verification method: live manual verification (video playback is hard to meaningfully unit-test) + basic automated smoke test

### D42-10 — Expert-verified content
- Domain: 42 (Education)
- Scenario ID: D42-10
- Exact scenario name: Expert-verified content
- Current implementation status: Missing
- Existing relevant files/classes/functions: `knowledge_entry.py:24-28,41-48` (`LicenseStatus` enum: open license/public domain/official government source/internal approved summary — schema fully designed)
- Missing component: Governance/approval schema exists and is ready, but has zero rows to approve
- Required implementation: This is the gating mechanism for D42-01 — as content is sourced, each `KnowledgeEntry.is_approved`/`license_status` must be set correctly before the serving endpoint (D42-01) returns it; no new schema needed, just enforcement in `knowledge_service.py`'s query (`WHERE is_approved = true`)
- Dependencies: D42-01 (this is the gate on that content, not a separate deliverable)
- Backend work: `backend/app/services/knowledge_service.py` — enforce the `is_approved` filter
- Database/migration work: none — schema exists
- Mobile work: none beyond D42-01's
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none — this IS the content-safety gate; must never be bypassed
- Tests required: a test asserting unapproved entries are never served
- Verification method: automated test

### D43-01 — Farmer question (Community)
- Domain: 43 (Community)
- Scenario ID: D43-01
- Exact scenario name: Farmer question
- Current implementation status: Missing
- Existing relevant files/classes/functions: grep for `community`/`forum`/`discussion`/`moderation`/`abuse.report` across `backend/app` and `mobile/lib` returns zero files; `AssistantConversation`/`AssistantMessage` is private farmer↔AI only; `CropHealthCase` is private 1:1 farmer↔expert only
- Missing component: No farmer-visible community feature of any kind exists
- Required implementation: A new `CommunityPost` model (farmer-authored, publicly visible to other farmers), a `POST /community/posts` endpoint, and a feed screen — this is a genuinely new domain, not an extension of an existing one, and should reuse existing conventions: `AuditLogger` for moderation-relevant actions, the existing `Role`/ownership-scoping pattern for who can post
- Dependencies: Foundational for D43-02 through D43-07 (all depend on this existing first)
- Backend work: new `backend/app/models/community_post.py`, `backend/app/services/community_service.py`, `backend/app/api/v1/community.py`
- Database/migration work: new `community_posts` table (author_id, crop_id?, title, body, created_at, is_visible)
- Mobile work: new `mobile/lib/features/community/` feed + post-creation screens
- Automation work: none initially
- Notification work: none initially (could later notify on replies, once D43-02 exists)
- Offline/sync impact: reads could be cached; posting should be online-only, consistent with case creation's existing online-only convention
- Security/RBAC impact: this is a genuinely new surface for abuse/privacy exposure — every farmer-scoped query elsewhere in this codebase is explicitly single-owner-scoped (`farm_repository.get_owned` pattern); a public post breaks that pattern deliberately and needs its own review (PII scrubbing, no crop-cycle/farm data leakage)
- Tests required: full new test suite mirroring `test_cases.py`'s structure (creation, ownership, visibility)
- Verification method: automated test + a product/legal review given the new abuse-surface (see D43-05/06)

### D43-02 — Farmer discussion
- Domain: 43 (Community)
- Scenario ID: D43-02
- Exact scenario name: Farmer discussion
- Current implementation status: Missing
- Existing relevant files/classes/functions: same as D43-01 — no farmer-to-farmer visibility exists anywhere
- Missing component: threaded replies to a community post
- Required implementation: A `CommunityReply` model FK'd to `CommunityPost`, threaded (optional `parent_reply_id` for nesting)
- Dependencies: Hard-blocked on D43-01
- Backend work: new `backend/app/models/community_reply.py`, service/API additions
- Database/migration work: new `community_replies` table
- Mobile work: thread view + reply composer
- Automation work: none
- Notification work: notify the original poster on a new reply (reuses `notification_service.create_alert_notification` pattern)
- Offline/sync impact: same as D43-01
- Security/RBAC impact: same as D43-01
- Tests required: mirrors D43-01's plan, reply-specific
- Verification method: automated test

### D43-03 — Expert answer (public)
- Domain: 43 (Community)
- Scenario ID: D43-03
- Exact scenario name: Expert answer
- Current implementation status: Missing
- Existing relevant files/classes/functions: `CaseReview`/`CaseAssignment` (real, but private 1:1 only — cited for context, does not satisfy this scenario per the cluster file's own note)
- Missing component: No public expert-answer-to-community-post mechanism
- Required implementation: Once D43-01/02 exist, allow a `VerificationStatus.VERIFIED` professional to reply to a community post/thread, with their reply flagged distinctly (e.g. `is_expert_reply: true`) reusing the existing verification gate from `professional_repository.candidates_for_matching`
- Dependencies: Hard-blocked on D43-01/02
- Backend work: `backend/app/models/community_reply.py` (verified-reply flag), `community_service.py` (verification check reusing existing `VerificationStatus.VERIFIED` gate)
- Database/migration work: new `community_replies.is_expert_reply` boolean
- Mobile work: visually distinguish expert replies in the thread view
- Automation work: none
- Notification work: none new beyond D43-02's
- Offline/sync impact: same as D43-01
- Security/RBAC impact: reuses the existing verification gate — no new RBAC concept
- Tests required: mirrors D43-02's plan, expert-flag variant
- Verification method: automated test

### D43-04 — Verification (community content)
- Domain: 43 (Community)
- Scenario ID: D43-04
- Exact scenario name: Verification
- Current implementation status: Missing
- Existing relevant files/classes/functions: `docs/EXPERT_VERIFICATION.md`, `VerificationStatus.VERIFIED` gate (real, but for professional identity, not community content)
- Missing component: No community content exists to verify since no community exists
- Required implementation: Reuses D43-03's `is_expert_reply` flag as the primary "verification" signal for community content — no separate content-verification workflow is proposed beyond that, to avoid inventing a second parallel verification system
- Dependencies: Hard-blocked on D43-01/02/03
- Backend work: none beyond D43-03's
- Database/migration work: none beyond D43-03's
- Mobile work: none beyond D43-03's
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none beyond D43-03's
- Tests required: none beyond D43-03's
- Verification method: automated test, folded into D43-03's

### D43-05 — Moderation
- Domain: 43 (Community)
- Scenario ID: D43-05
- Exact scenario name: Moderation
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no moderation queue/flag model found by grep; no explicit "deferred" note found for community moderation specifically
- Missing component: Would require human moderators or an AI triage pipeline, neither built; correctly classified MISSING rather than FUTURE since there is no natural in-progress increment to extend
- Required implementation: A `CommunityFlag`/moderation-queue model (post/reply id, reason, status), a moderator-only review endpoint gated by a new `Role.MODERATOR` (or reuse an existing admin role if one exists), and a soft-hide mechanism on flagged content (mirroring the existing soft-delete pattern used for `CropPhoto`)
- Dependencies: Hard-blocked on D43-01/02 existing (nothing to moderate otherwise); should be built before or alongside D43-01/02's public launch, not after, given abuse risk
- Backend work: new `backend/app/models/community_flag.py`, `community_moderation_service.py`, admin-role-gated API
- Database/migration work: new `community_flags` table; `is_visible`/`hidden_reason` columns on `community_posts`/`community_replies`
- Mobile work: a "report" action on posts/replies (feeds D43-06), and an admin moderation queue screen (could be web-only/admin-tool, not necessarily in the farmer app)
- Automation work: optional future AI-triage pass (explicitly out of scope for a first pass, per the cluster file's own reasoning about D43-07)
- Notification work: notify the reporting farmer when their flag is actioned (optional)
- Offline/sync impact: none — moderation actions are online-only
- Security/RBAC impact: real — introduces a new privileged role and a content-hiding capability; must be carefully scoped so only moderators can hide content
- Tests required: new test suite for flagging, hiding, and moderator-only access
- Verification method: automated test + a product decision on who moderates (staff? community-elected? AI-assisted?) before building

### D43-06 — Abuse/reporting
- Domain: 43 (Community)
- Scenario ID: D43-06
- Exact scenario name: Abuse/reporting
- Current implementation status: Missing
- Existing relevant files/classes/functions: `dispute_service.py` (a commercial order/product complaint flow — explicitly distinct from a content-abuse report, per the cluster file's own note)
- Missing component: No report-abuse endpoint for community content
- Required implementation: A `POST /community/posts/{id}/report` (and reply equivalent) endpoint creating a `CommunityFlag` row (see D43-05) — this scenario IS the farmer-facing half of D43-05's moderation-queue proposal
- Dependencies: Hard-blocked on D43-01/02 and designed together with D43-05
- Backend work: `backend/app/api/v1/community.py` (report endpoint), `community_moderation_service.py`
- Database/migration work: shared with D43-05 (`community_flags` table)
- Mobile work: a "report" button/menu action on posts/replies
- Automation work: none
- Notification work: none new beyond D43-05's
- Offline/sync impact: none — online-only, same as other community actions
- Security/RBAC impact: any farmer can report; only moderators can act on reports — same RBAC boundary as D43-05
- Tests required: new test asserting a report creates a flag and is itself rate-limited/idempotent per reporter+post
- Verification method: automated test

### D43-07 — AI triage (community posts)
- Domain: 43 (Community)
- Scenario ID: D43-07
- Exact scenario name: AI triage
- Current implementation status: Missing
- Existing relevant files/classes/functions: `nearby_professional_service.find_ranked_candidates`/`case_service._try_auto_assign` (real, but triages private expert cases, not community posts, per the cluster file's own note — cited for context only)
- Missing component: No AI triage of community posts exists since community posts don't exist
- Required implementation: Deliberately NOT recommended as a first-pass deliverable — auto-triaging public community content by AI carries real moderation-quality and fabrication risk beyond this project's established "never fabricate, always disclose" discipline; if pursued, should reuse the existing deterministic-ranking pattern (`find_ranked_candidates`'s weighted, explainable scoring) rather than an opaque model, and should follow, not precede, D43-05's human moderation queue
- Dependencies: Hard-blocked on D43-01/02/05 (moderation queue should exist first, so AI triage has a human fallback from day one)
- Backend work: (if pursued) a new deterministic scoring function analogous to `find_ranked_candidates`, e.g. surfacing likely-duplicate or likely-spam posts for human review, never auto-hiding content without a human step
- Database/migration work: (if pursued) a `community_posts.triage_score` column
- Mobile work: none required for a backend-only triage aid
- Automation work: (if pursued) a scheduled sweep scoring new posts, following the `scheduler.py` pattern
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: same as D43-05 — any auto-action must remain human-gated
- Tests required: (if pursued) tests asserting triage never auto-hides without human confirmation
- Verification method: not recommended for this pass; would need automated test + human-in-the-loop review if built

### D44-05 — Machinery (Nearby Services)
- Domain: 44 (Nearby Services)
- Scenario ID: D44-05
- Exact scenario name: Machinery
- Current implementation status: Missing
- Existing relevant files/classes/functions: grep for `machinery`/`Machinery` across `backend/app` returns zero files
- Missing component: entire Machinery domain absent
- Required implementation: see the full D45 domain proposal below (D45-01 through D45-08) — this scenario is the "nearby services" umbrella entry for the same gap
- Dependencies: same as D45 domain
- Backend work: see D45-01
- Database/migration work: see D45-01
- Mobile work: see D45-01
- Automation work: see D45-01
- Notification work: see D45-01
- Offline/sync impact: see D45-01
- Security/RBAC impact: see D45-01
- Tests required: see D45-01
- Verification method: see D45-01

### D44-06 — Labour (Nearby Services)
- Domain: 44 (Nearby Services)
- Scenario ID: D44-06
- Exact scenario name: Labour
- Current implementation status: Missing
- Existing relevant files/classes/functions: `LedgerEntryCategory.LABOR` (`models/ledger_entry.py:61`, cost-tracking category only)
- Missing component: entire Labour marketplace domain absent
- Required implementation: see the full D46 domain proposal below (D46-01 through D46-06) — this scenario is the "nearby services" umbrella entry for the same gap
- Dependencies: same as D46 domain
- Backend work: see D46-01
- Database/migration work: see D46-01
- Mobile work: see D46-01
- Automation work: see D46-01
- Notification work: see D46-01
- Offline/sync impact: see D46-01
- Security/RBAC impact: see D46-01
- Tests required: see D46-01
- Verification method: see D46-01

### D44-07 — Mandi
- Domain: 44 (Nearby Services)
- Scenario ID: D44-07
- Exact scenario name: Mandi
- Current implementation status: Missing
- Existing relevant files/classes/functions: grep for `mandi` returns zero files; `SaleOrder` is buyer-to-farmer direct, not a mandi/market-yard locator
- Missing component: No mandi/market-yard locator of any kind
- Required implementation: A `MandiLocation` reference-data model (name, state, district, lat/lon — likely sourced from a government open dataset, not fabricated) plus a `GET /mandis?state=&district=` lookup endpoint; this is a "nearby services directory" pattern, distinct from the transactional `SaleOrder` marketplace
- Dependencies: none technical; depends on sourcing a real, licensed mandi dataset (same anti-fabrication discipline as `KnowledgeEntry`)
- Backend work: new `backend/app/models/mandi_location.py`, `mandi_service.py`, `backend/app/api/v1/mandis.py`
- Database/migration work: new `mandi_locations` table, seeded from a real government dataset (mirrors the existing Mandal/Village master-data seeding pattern already used elsewhere in this project)
- Mobile work: new "Nearby Mandis" screen with state/district filter (reusing existing `location_repository` state/district data)
- Automation work: none
- Notification work: none
- Offline/sync impact: reference data — could be bundled/cached like other location master data
- Security/RBAC impact: none — public reference data
- Tests required: new tests for the lookup endpoint
- Verification method: automated test; data accuracy requires live/manual sourcing verification, same discipline as the project's existing location master-data seeding

### D44-08 — Storage
- Domain: 44 (Nearby Services)
- Scenario ID: D44-08
- Exact scenario name: Storage
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no storage-facility model/endpoint found
- Missing component: no storage-facility directory
- Required implementation: A `StorageFacility` reference-data model (name, type, state/district, capacity if available) + lookup endpoint, same directory pattern as D44-07 (Mandi)
- Dependencies: none technical; depends on sourcing a real dataset
- Backend work: new `backend/app/models/storage_facility.py`, service, API
- Database/migration work: new `storage_facilities` table
- Mobile work: new "Nearby Storage" screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none — reference data, cacheable
- Security/RBAC impact: none — public reference data
- Tests required: new tests for the lookup endpoint
- Verification method: automated test; data sourcing requires manual verification

### D44-09 — Cold storage
- Domain: 44 (Nearby Services)
- Scenario ID: D44-09
- Exact scenario name: Cold storage
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no cold-storage model/endpoint found
- Missing component: no cold-storage directory
- Required implementation: same pattern as D44-08, with a `is_cold_storage`/`temperature_range` distinguishing field — likely the same `StorageFacility` model with a type flag rather than a separate model
- Dependencies: same as D44-08 — build together
- Backend work: same model as D44-08, extended with a type field
- Database/migration work: `storage_facilities.facility_type` column
- Mobile work: filter option on the D44-08 screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: same as D44-08, type-filter variant
- Verification method: same as D44-08

### D44-10 — Soil lab
- Domain: 44 (Nearby Services)
- Scenario ID: D44-10
- Exact scenario name: Soil lab
- Current implementation status: Missing
- Existing relevant files/classes/functions: `backend/app/core/roles.py:23,37,39-47` (`Role.LAB` exists as vocabulary only, not in `SEEDED_ROLE_CODES`, so no DB row, no registerable soil-lab professional exists in practice)
- Missing component: Vocabulary exists, nothing else — zero further implementation
- Required implementation: Seed `Role.LAB` into `SEEDED_ROLE_CODES`, then build a `ProfessionalProfile`-style directory for soil labs, reusing the exact `nearby_professional_service`/`ProfessionalProfile` pattern already built for experts (verification gate, state/district matching) rather than inventing a new mechanism
- Dependencies: This is the most straightforward of the D44 gaps to build, since the professional-directory pattern (D44-01, VERIFIED) already exists and just needs a new role seeded and a lab-specific profile subtype
- Backend work: `backend/app/core/roles.py` (add `LAB` to `SEEDED_ROLE_CODES`), reuse `ProfessionalProfile`/`nearby_professional_service.py` with `role="lab"`
- Database/migration work: seed migration adding the `LAB` role row; possibly a `SoilLabProfile` extension table if labs need fields experts don't (e.g. test turnaround time, accepted sample types)
- Mobile work: reuse the existing expert-directory screen pattern, filtered to `role=lab`
- Automation work: none
- Notification work: reuses existing case/assignment notification pattern if soil-test requests are modeled as a case-like flow
- Offline/sync impact: none — same online-only directory lookup as experts
- Security/RBAC impact: none new — reuses the existing `VerificationStatus.VERIFIED` gate
- Tests required: new tests mirroring `nearby_professional_service`'s existing test suite, `role="lab"` variant
- Verification method: automated test

### D44-11 — Diagnostic centre
- Domain: 44 (Nearby Services)
- Scenario ID: D44-11
- Exact scenario name: Diagnostic centre
- Current implementation status: Missing
- Existing relevant files/classes/functions: none directly — the closest adjacent capability (AI crop-photo diagnosis + expert case review, D44-01) is a software/expert flow, not a physical facility locator
- Missing component: No physical "diagnostic centre" locator model
- Required implementation: same directory pattern as D44-07/08/09 — a `DiagnosticCentre` reference-data model + lookup endpoint, or extend `SoilLabProfile` (D44-10) if diagnostic centres and soil labs overlap in this market
- Dependencies: consider designing alongside D44-10 given likely overlap
- Backend work: new model/service/API, or extend D44-10's
- Database/migration work: new table or extension of D44-10's
- Mobile work: new or shared directory screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none — reference data
- Security/RBAC impact: none
- Tests required: same pattern as D44-08/10
- Verification method: automated test

### D44-12 — Veterinary centre
- Domain: 44 (Nearby Services)
- Scenario ID: D44-12
- Exact scenario name: Veterinary centre
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — this app has no livestock/animal domain at all (crop-farming only), confirmed by the complete absence of any animal/vet keyword anywhere in `backend/app`
- Missing component: Entire livestock/animal domain absent, not just a locator
- Required implementation: Building this properly would require an entirely new farmer-facing domain (livestock records, animal health) before a "nearby veterinary centre" locator would even be meaningful — not recommended as an isolated feature; if pursued, should be scoped as a new product area, not a small addition
- Dependencies: A product-scope decision on whether this app ever covers livestock at all
- Backend work: out of scope for a small increment — would need a livestock domain first
- Database/migration work: n/a until scope is decided
- Mobile work: n/a until scope is decided
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: none until scope is decided
- Verification method: not applicable — requires a product decision, not an engineering estimate

### D44-13 — Transporter
- Domain: 44 (Nearby Services)
- Scenario ID: D44-13
- Exact scenario name: Transporter
- Current implementation status: Missing (unchanged — `FINAL_GAP_REPORT.md` explicitly kept this as MISSING rather than FUTURE, since `delivery_service.py`'s comment is "a real but informal signal, not a committed roadmap item"; no status-change delta applies)
- Existing relevant files/classes/functions: `roles.py:22,37` (`Role.TRANSPORTER` vocabulary-only, not seeded); `delivery_service.py:1-6` ("Delivery may later be handed to a distinct transporter role — not built this phase")
- Missing component: No transporter role seeded, no transporter-specific profile/matching, no delivery-assignment flow beyond whatever `delivery_service.py` currently does generically
- Required implementation: Seed `Role.TRANSPORTER`, build a `TransporterProfile` (or extend `ProfessionalProfile`) and reuse `nearby_professional_service`'s matching pattern for delivery assignment, exactly like D44-10's soil-lab proposal
- Dependencies: Should be designed alongside whatever `delivery_service.py`'s existing generic delivery flow does, to avoid two parallel delivery-assignment mechanisms
- Backend work: `backend/app/core/roles.py` (seed `TRANSPORTER`), `delivery_service.py` (route to a transporter-role match when one is assigned), reuse `nearby_professional_service.py`
- Database/migration work: seed migration for the role; possible `TransporterProfile` extension table (vehicle type, capacity)
- Mobile work: transporter-facing assignment screen (would face the same "no professional-facing UI" gap noted in D34-04)
- Automation work: none
- Notification work: reuses existing case/assignment-style notification pattern
- Offline/sync impact: none — same online-only assignment flow as experts
- Security/RBAC impact: none new — reuses the existing verification-gate pattern
- Tests required: new tests mirroring `nearby_professional_service`'s suite, transporter-role variant
- Verification method: automated test; also requires a product decision on scope/priority given it's currently only an informal design note

### D45-01 — Machinery search
- Domain: 45 (Machinery)
- Scenario ID: D45-01
- Exact scenario name: Machinery search
- Current implementation status: Missing
- Existing relevant files/classes/functions: grep for `machinery`/`Machinery` across `backend/app` (models, services, api, schemas) and `mobile/lib` returns zero files
- Missing component: entire Machinery domain absent
- Required implementation: A new `Machinery` listing model (owner, machinery type, description, rate, location) + `GET /machinery?type=&state=&district=` search endpoint, reusing the existing `DealerProduct` catalog/search pattern (client-and-server filtering) and `location_repository` state/district data for the "nearby" dimension
- Dependencies: Foundational for D45-02 through D45-08
- Backend work: new `backend/app/models/machinery_listing.py`, `machinery_service.py`, `backend/app/api/v1/machinery.py`
- Database/migration work: new `machinery_listings` table
- Mobile work: new `mobile/lib/features/machinery/` search/list screen
- Automation work: none
- Notification work: none initially
- Offline/sync impact: browse-only reads could be cached; booking (D45-06) should be online-only, consistent with other transactional flows
- Security/RBAC impact: none initially — public catalog, same as dealer products
- Tests required: new test suite mirroring the dealer-product catalog tests
- Verification method: automated test

### D45-02 — Availability (Machinery)
- Domain: 45 (Machinery)
- Scenario ID: D45-02
- Exact scenario name: Availability
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no machinery model exists to have an availability field
- Missing component: availability field/logic
- Required implementation: Add an `availability_status`/calendar-slot concept to the `MachineryListing` (D45-01), reusing `AvailabilityStatus` (available/busy/offline) already defined for `ProfessionalProfile` if a simple status suffices, or a proper slot/calendar table if machinery needs date-range booking (more likely, given rentals are typically day-based)
- Dependencies: Hard-blocked on D45-01
- Backend work: `backend/app/models/machinery_listing.py` (status or slot table), `machinery_service.py`
- Database/migration work: new `machinery_availability_slots` table (listing_id, date_range, is_booked) if slot-based
- Mobile work: availability calendar UI on the listing detail screen
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new tests for availability-slot logic (overlap prevention, etc.)
- Verification method: automated test

### D45-03 — Rental
- Domain: 45 (Machinery)
- Scenario ID: D45-03
- Exact scenario name: Rental
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no rental/booking model for machinery anywhere
- Missing component: the transactional rental concept itself
- Required implementation: This is effectively D45-06 (Booking) — "rental" is the product concept, "booking" is its lifecycle; see D45-06's full state-machine proposal, reusing `Order`'s `ALLOWED_ORDER_TRANSITIONS` pattern
- Dependencies: Hard-blocked on D45-01/02; same underlying build as D45-06
- Backend work: see D45-06
- Database/migration work: see D45-06
- Mobile work: see D45-06
- Automation work: see D45-06
- Notification work: see D45-06
- Offline/sync impact: see D45-06
- Security/RBAC impact: see D45-06
- Tests required: see D45-06
- Verification method: see D45-06

### D45-04 — Rate
- Domain: 45 (Machinery)
- Scenario ID: D45-04
- Exact scenario name: Rate
- Current implementation status: Missing
- Existing relevant files/classes/functions: no machinery rate/pricing field exists (contrast with the real `dealer_price_history.py` for products)
- Missing component: pricing field/history
- Required implementation: Add a `rate_per_day`/`rate_per_hour` field to `MachineryListing` (D45-01), and a `MachineryRateHistory` table mirroring `dealer_price_history.py`'s existing pattern if rate-change tracking is wanted
- Dependencies: Hard-blocked on D45-01
- Backend work: `backend/app/models/machinery_listing.py` (rate fields), optional `machinery_rate_history.py` mirroring `dealer_price_history.py`
- Database/migration work: new `machinery_listings.rate_per_day` column, optional history table
- Mobile work: display rate on listing detail
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new tests mirroring `dealer_price_history`'s existing test pattern
- Verification method: automated test

### D45-05 — Schedule
- Domain: 45 (Machinery)
- Scenario ID: D45-05
- Exact scenario name: Schedule
- Current implementation status: Missing
- Existing relevant files/classes/functions: no scheduling concept for machinery (the unrelated `Task` model, per `PROJECT_STATUS.md:388`, is farmer-created generic tasks, not machinery scheduling)
- Missing component: scheduling/calendar concept
- Required implementation: same as D45-02's availability-slot proposal — scheduling and availability are the same underlying calendar mechanism from two angles (owner sets availability, farmer books a schedule slot)
- Dependencies: Hard-blocked on D45-01/02; same build as D45-02
- Backend work: see D45-02
- Database/migration work: see D45-02
- Mobile work: see D45-02
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: see D45-02
- Verification method: see D45-02

### D45-06 — Booking
- Domain: 45 (Machinery)
- Scenario ID: D45-06
- Exact scenario name: Booking
- Current implementation status: Missing
- Existing relevant files/classes/functions: no booking model/endpoint/state-machine exists for machinery (contrast with the real `Order`/`ALLOWED_ORDER_TRANSITIONS` pattern used for dealer products)
- Missing component: booking state machine
- Required implementation: A `MachineryBooking` model with a state machine mirroring `Order`'s `ALLOWED_ORDER_TRANSITIONS` exactly (e.g. `REQUESTED -> CONFIRMED -> IN_PROGRESS -> COMPLETED`, with `CANCELLED` reachable from the pre-`IN_PROGRESS` states), `POST /machinery/{id}/bookings`
- Dependencies: Hard-blocked on D45-01/02/04; directly enables D45-07/08
- Backend work: new `backend/app/models/machinery_booking.py` (state enum + transition table mirroring `order.py`'s), `machinery_booking_service.py`, API
- Database/migration work: new `machinery_bookings` table
- Mobile work: booking-request flow, booking-status screen
- Automation work: none initially — could later add a reminder sweep for upcoming bookings, mirroring the task-reminder proposal (D37-04)
- Notification work: new notification on booking confirm/cancel, reusing `notification_service.create_alert_notification`
- Offline/sync impact: booking actions should be online-only, consistent with `Order`/case-creation conventions
- Security/RBAC impact: ownership-scoped (farmer sees own bookings, machinery owner sees bookings against their listings) — same dual-ownership pattern as `Order` (buyer/seller)
- Tests required: new test suite mirroring `test_orders`-equivalent transition tests
- Verification method: automated test

### D45-07 — Cancellation
- Domain: 45 (Machinery)
- Scenario ID: D45-07
- Exact scenario name: Cancellation
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no booking exists to cancel
- Missing component: cancellation transition
- Required implementation: A `CANCELLED` transition on `MachineryBooking` (D45-06), reachable from `REQUESTED`/`CONFIRMED`, mirroring `Order`'s existing cancellation-eligibility rules
- Dependencies: Hard-blocked on D45-06
- Backend work: `machinery_booking_service.py` (cancel transition + guard)
- Database/migration work: none beyond D45-06's
- Mobile work: cancel action on booking-detail screen
- Automation work: none
- Notification work: notify the other party on cancellation
- Offline/sync impact: none — online-only, same as D45-06
- Security/RBAC impact: same ownership scoping as D45-06
- Tests required: new tests mirroring order-cancellation tests
- Verification method: automated test

### D45-08 — Completion
- Domain: 45 (Machinery)
- Scenario ID: D45-08
- Exact scenario name: Completion
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no booking exists to complete
- Missing component: completion transition
- Required implementation: A `COMPLETED` transition on `MachineryBooking` (D45-06), mirroring `Order`'s completion pattern; could optionally feed into per-acre cost tracking (`LedgerEntryCategory`) as a new category once complete
- Dependencies: Hard-blocked on D45-06
- Backend work: `machinery_booking_service.py` (complete transition)
- Database/migration work: none beyond D45-06's
- Mobile work: "mark complete" action, both parties
- Automation work: none
- Notification work: notify on completion
- Offline/sync impact: none
- Security/RBAC impact: same as D45-06
- Tests required: new tests mirroring order-completion tests
- Verification method: automated test

### D46-01 — Labour requirement
- Domain: 46 (Labour)
- Scenario ID: D46-01
- Exact scenario name: Labour requirement
- Current implementation status: Missing
- Existing relevant files/classes/functions: `LedgerEntryCategory.LABOR` (`models/ledger_entry.py:61` — a cost-tracking enum value only, unrelated to sourcing workers)
- Missing component: entire Labour marketplace domain absent — no job-posting model anywhere
- Required implementation: A `LabourRequirement` model (farmer-posted: crop task, dates needed, number of workers, optional rate) + `POST /labour-requirements` — a directory/matching pattern most similar to Machinery (D45) rather than Expert (workers aren't verified professionals), so a simpler open-listing model without a verification gate is appropriate, unless worker identity verification becomes a trust requirement later
- Dependencies: Foundational for D46-02 through D46-06
- Backend work: new `backend/app/models/labour_requirement.py`, `labour_service.py`, API
- Database/migration work: new `labour_requirements` table
- Mobile work: new `mobile/lib/features/labour/` posting + browsing screens
- Automation work: none initially
- Notification work: none initially
- Offline/sync impact: posting should be online-only, consistent with other listing-creation flows
- Security/RBAC impact: none initially — public listing, though worker-side identity/trust is an open design question if this becomes a two-sided marketplace
- Tests required: new test suite mirroring the machinery-listing test plan
- Verification method: automated test

### D46-02 — Availability (Labour)
- Domain: 46 (Labour)
- Scenario ID: D46-02
- Exact scenario name: Availability
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no worker-availability concept exists
- Missing component: worker-side availability
- Required implementation: If workers are modeled as registerable profiles (not just anonymous responders to a posting), add a `WorkerProfile` with an `availability_status`, reusing `AvailabilityStatus` from `ProfessionalProfile`; if the simpler open-posting model (D46-01) is chosen instead, "availability" is implicitly whoever responds to a posting, and this scenario may not need a separate field
- Dependencies: Depends on the design decision made in D46-01 (open-posting vs. worker-profile marketplace)
- Backend work: conditional on D46-01's design — `WorkerProfile` model + availability field, or none
- Database/migration work: conditional
- Mobile work: conditional
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none beyond D46-01's
- Tests required: conditional on design
- Verification method: automated test once design is decided

### D46-04 — Schedule (Labour)
- Domain: 46 (Labour)
- Scenario ID: D46-04
- Exact scenario name: Schedule
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no labour scheduling concept exists
- Missing component: scheduling
- Required implementation: `LabourRequirement.needed_start_date`/`needed_end_date` fields (D46-01), no separate calendar system needed given labour needs are typically short, date-range based rather than slot-booked like machinery
- Dependencies: Hard-blocked on D46-01
- Backend work: `backend/app/models/labour_requirement.py` (date-range fields)
- Database/migration work: new columns on `labour_requirements`
- Mobile work: date-range picker on the posting form
- Automation work: none
- Notification work: none
- Offline/sync impact: none
- Security/RBAC impact: none
- Tests required: new tests for date-range validation
- Verification method: automated test

### D46-05 — Assignment (Labour)
- Domain: 46 (Labour)
- Scenario ID: D46-05
- Exact scenario name: Assignment
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no worker-assignment model exists (not to be confused with the real `CaseAssignment` for expert cases, an unrelated domain)
- Missing component: assignment/acceptance flow between farmer and worker
- Required implementation: A `LabourAssignment` model FK'd to `LabourRequirement`, with a small state machine (`OFFERED -> ACCEPTED -> COMPLETED`/`DECLINED`), reusing the `CaseAssignment` pattern's shape (not its expert-specific semantics) as the closest structural analog in this codebase
- Dependencies: Hard-blocked on D46-01/04
- Backend work: new `backend/app/models/labour_assignment.py`, service, API
- Database/migration work: new `labour_assignments` table
- Mobile work: assignment/offer screens for both farmer and worker sides
- Automation work: none
- Notification work: notify on offer/accept/decline, reusing `notification_service.create_alert_notification`
- Offline/sync impact: online-only, same as case assignment
- Security/RBAC impact: none beyond ownership scoping
- Tests required: new tests mirroring `test_cases.py`'s assignment-lifecycle tests, labour variant
- Verification method: automated test

### D46-06 — Completion (Labour)
- Domain: 46 (Labour)
- Scenario ID: D46-06
- Exact scenario name: Completion
- Current implementation status: Missing
- Existing relevant files/classes/functions: none — no labour job exists to mark complete
- Missing component: completion transition
- Required implementation: `COMPLETED` transition on `LabourAssignment` (D46-05); could optionally prompt the farmer to log the resulting cost via the existing `LedgerEntryCategory.LABOR` cost-tracking flow (D46-03), closing the loop between "hired labour" and "recorded labour spend"
- Dependencies: Hard-blocked on D46-05
- Backend work: `labour_assignment_service.py` (complete transition)
- Database/migration work: none beyond D46-05's
- Mobile work: "mark complete" action, optional prompt to log cost via the existing cost-ledger screen
- Automation work: none
- Notification work: notify on completion
- Offline/sync impact: none
- Security/RBAC impact: none beyond D46-05's
- Tests required: new tests mirroring D46-05's plan, completion variant
- Verification method: automated test

## 4. Broken

None. Confirmed explicitly: none of the 149 scenario rows in domains 27-46 carry a BROKEN
status in any of the three source cluster files (`c05_disease_ai.md`, `c06_expert_network.md`,
`c07_voice_language_community.md`) — the 12 originally-disclosed project-wide BROKEN rows
(`D1-18`, `D49-05`, `D50-07`, `D57-07`, `D58-06`, `D59-06`, `D66-02`, `D84-02`, `D84-04`,
`D87-04`, `D87-05`, `D87-06`, all fixed per `FINAL_100_DOMAIN_SCENARIO_MATRIX.md` §A) all
belong to domains outside this group's 27-46 range. Zero-BROKEN for this group requires no
reconciliation action.

## 5. Future — with justification

| Scenario ID | Domain | Name | Justification |
|---|---|---|---|
| D27-06 | 27 (Disease) | Treatment recommendation | **Justified.** Explicit deliberate deferral cited in three independent places: `docs/DISEASE_MODEL.md` ("Deliberately excluded: treatment/medicine fields... a separate future module, never a column here"), `treatment_record.py` docstring ("Rather than fabricate a 'recommendation' concept, this reuses existing structures"), and `safety_validator.py:12-19`'s structural block of prescription requests (`docs/AI_GUARDRAILS.md`). A genuine, documented safety/anti-fabrication boundary, not an oversight. |

No other row in this group's 149 scenarios carries a FUTURE label after reconciliation
(D35-06, the only FUTURE row affected by a delta, moved to VERIFIED — see the deltas table
above). All FUTURE-adjacent findings for domains 27-46 (D42-09's video-hosting decision,
D44-12's livestock-domain-scope question, D43-05/07's moderation-before-triage sequencing)
are documented as recommendations inside their MISSING entries in Section 3, not as FUTURE
labels, since the source cluster files classified them MISSING, not FUTURE, and this
reconciliation does not relabel a bucket without an explicit sourced delta.

## 6. Out of Scope — with justification

None. No scenario row in domains 27-46 was classified OUT_OF_SCOPE by any of the three
source cluster files (confirmed by re-reading all 149 rows' Status cells). The only
OUT_OF_SCOPE-adjacent mention in this group is D44-12 (Veterinary centre), whose cluster-file
Status cell explicitly reads "OUT_OF_SCOPE/MISSING... Classified MISSING" — i.e. the cluster
file itself resolved the ambiguity to MISSING, not OUT_OF_SCOPE, so it is listed once, under
Section 3, and not counted here. This is consistent with the whole-project count: all 25
project-wide OUT_OF_SCOPE rows (per `FINAL_100_DOMAIN_SCENARIO_MATRIX.md`'s reconciled
totals, e.g. D60-01/D61-01 per `FINAL_GAP_REPORT.md`) belong to domains outside 27-46.

## 7. Environment Dependent — exact dependency

None classified as a standalone ENVIRONMENT_DEPENDENT bucket in this group. All 6
project-wide ENVIRONMENT_DEPENDENT rows belong to domain 14 (Weather: D14-01/03/04/05/06/08,
per `FINAL_GAP_REPORT.md`'s own table), outside this group's 27-46 range.

Two rows in this group carry an environment-dependency **caveat** inside an otherwise-VERIFIED
compound status, disclosed here for completeness rather than hidden inside Section 1's
one-liners:

| Scenario ID | Domain | Name | Exact external dependency |
|---|---|---|---|
| D27-04 / D29-04 | 27/29 (Disease / AI Diagnosis) | Photo diagnosis / Disease detection | Real diagnostic accuracy depends on a trained disease-recognition model being configured in `ModelProvider`; only `NotConfiguredModelProvider` (`available=False`) is wired into production today (`docs/AI_MODEL_PROVIDER.md`, "no key configured"). The pipeline itself is VERIFIED via a fake provider; the model dependency is what remains environment/config-dependent (documented as FUTURE in project docs, not purely environmental, hence bucketed VERIFIED here per the compound-status convention, not moved to this section as a primary bucket). |
| D31-04 | 31 (AI Confidence) | Confidence threshold | The 0.85/0.60 numeric thresholds are configurable via `Settings` but are explicitly disclosed as unvalidated placeholders pending a real evaluation dataset (`docs/AI_EVALUATION.md`, dataset NOT_CONFIGURED) — real-world calibration depends on that dataset existing, not on this session's environment specifically, so also kept as a VERIFIED-with-caveat rather than moved here as a primary ENVIRONMENT_DEPENDENT bucket. |
