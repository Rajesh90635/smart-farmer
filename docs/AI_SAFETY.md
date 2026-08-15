# AI Safety

## The absolute rule

**AI results are AI-assisted observations, never guaranteed diagnoses.**
Every design decision in this module traces back to that sentence.

## Where each safety rule is actually enforced (not just stated)

| Rule | Enforcement point | Verified by |
|---|---|---|
| Never invent a disease when the model is unavailable | `NotConfiguredModelProvider` always returns `available=False`; `PredictionValidator` maps this to `AI_UNAVAILABLE` before any class name is ever considered | `test_predict_disease_is_unavailable`, `test_unavailable_model_maps_to_ai_unavailable` |
| Never name a disease at low confidence | `prediction_validator.validate_disease_prediction`: the `LOW_CONFIDENCE` branch explicitly sets `predicted_class=None` — the raw prediction may have a class name, but it is discarded at this layer, not merely hidden by the UI | `test_low_confidence_never_names_a_class`, `test_low_confidence_result_never_names_a_disease` (integration) |
| Never diagnose a crop the model doesn't support | Checked against `model_provider.supported_crop_names()` **before** looking at any prediction confidence | `test_unsupported_crop_result`, `test_unsupported_crop_maps_to_unknown` |
| Never diagnose when the photo doesn't match the selected crop | `DiseasePrediction.crop_match` checked as a hard gate, `CROP_MISMATCH` result, no class name surfaced | `test_crop_mismatch_result`, `test_crop_mismatch_is_never_silently_diagnosed` |
| Never run inference on a clearly bad photo | `analyze_photo` checks `photo.image_quality_status == REJECTED` and refuses with a 422 **before** any model call | `test_analysis_requires_accepted_photo_quality` |
| Never let an inference crash produce a fabricated result | `_run_analysis` wraps the entire model-call/validation block in a broad `try/except`, degrading to `FAILED`/`requires_review=True` on any exception | `test_ai_failure_during_inference_is_handled_safely` |
| Never silently overwrite farmer-confirmed data | No code path in this phase writes to `CropCycle.cultivation_status` from any AI model/service — `AICropStageResult` is a fully separate table | Structural — verified by inspection of every write in `app/services/ai_analysis_service.py` and `app/services/ai_analysis_session_service.py` |
| Every result identifies its model | `AIAnalysis.model_name`/`model_version` populated on every row, including `AI_UNAVAILABLE` and `FAILED` results | `test_model_version_is_always_recorded` |
| Expert-review hook exists without a full expert workflow | `requires_review: bool` on every `AIAnalysis` row; no expert UI/routing built this phase | Schema-level, per Requirement 27 |

## Confidence bands and what happens at each (Requirement 11)

| Band | Threshold (placeholder, see docs/AI_EVALUATION.md) | Result |
|---|---|---|
| HIGH | ≥ 0.85 | Disease/healthy result shown, `requires_review=False` |
| MEDIUM | 0.60–0.85 | Disease/healthy result shown, but **`requires_review=True`** — never review-free on a guess this uncertain |
| LOW | < 0.60 | `LOW_CONFIDENCE` — no class name surfaced at all, `requires_review=True` |

## Farmer-facing wording rules (Requirement 24/26)

- Never show a raw confidence percentage as if it were a validated
  accuracy claim (e.g. never "99.8% accurate").
- Never use "diagnosis" — use "observation" or "what we found."
- `AI_UNAVAILABLE` shows: *"We couldn't check the photo right now. Please
  try again later."* — never a fake result, and the photo remains safely
  stored regardless (Requirement 36).
- `UNKNOWN`/`LOW_CONFIDENCE` shows: *"Unable to identify the problem
  confidently. Please take a clearer photo."*
- `CROP_MISMATCH` shows a message asking the farmer to confirm they
  selected the right crop — never a same-crop diagnosis anyway.

## Operational logging (Requirement 34)

`processing_time_ms`, `model_name`/`model_version`, `result_status`,
photo `width_px`/`height_px` (already on `CropPhoto` from Prompt 5) are the
only things ever recorded about an analysis. **Never logged:** raw image
bytes, farmer PII, auth tokens — consistent with the logging rules
established in the foundation phase (`docs/SECURITY.md`).
