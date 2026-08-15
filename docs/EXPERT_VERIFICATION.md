# Expert Verification

## Controlled outcomes only - never free text alone

An expert's review outcome must be one of exactly 5 values
(`EXPERT_OUTCOMES` in `app/models/case_review.py`), validated at the
service layer:

| Outcome | Case status transition |
|---|---|
| confirmed | VERIFIED |
| different_diagnosis | VERIFIED (with `final_verified_class` set to the expert's alternative) |
| insufficient_image | (no automatic transition coded this phase - stays IN_REVIEW; disclosed gap) |
| needs_more_information | NEEDS_MORE_INFORMATION |
| no_disease_visible | VERIFIED |

`notes` is optional free text that supplements the structured outcome -
never a substitute for it. Verified by test: submitting an outcome not in
the allowed set (e.g. a field-agent-only value from an expert) returns
`422`.

## AI vs expert - always separate, never overwritten

`AIAnalysis.predicted_class`/`confidence` are never modified by any case
service code. `CropHealthCase.final_verified_class` and
`final_verification_source` are a SEPARATE, additive record. When the
expert disagrees with the AI (`different_diagnosis`), both the original AI
result and the expert's alternative remain independently queryable -
verified by `test_expert_disagreement_recorded_without_touching_ai_result`.

## What this enables for future model evaluation

Every disagreement (AI result vs `final_verified_class`) is a real,
timestamped, model-versioned data point for future evaluation - the exact
kind of labeled pair `app/services/ai/evaluation.py` (Prompt 6) is
designed to consume, once a real model exists to evaluate.

## What experts CANNOT do (by omission, not by an explicit block)

No endpoint or field anywhere in this phase lets an expert recommend a
medicine, pesticide, or dosage - `CaseReview` has no such field, and no
service function accepts one.
