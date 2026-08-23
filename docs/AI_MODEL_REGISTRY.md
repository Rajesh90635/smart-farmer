# AI Model Registry

## Purpose

`ai_model_registry` (one row per model **version**, never edited in place)
is what makes "the application should know which model generated each
result" true. `AIAnalysis.model_registry_id` points here, and
`AIAnalysis.model_name`/`model_version` are also copied as immutable
strings — so a historical result identifies its model even after the
registry row is edited or a new version becomes active.

## Schema

| Field | Notes |
|---|---|
| name, version | Unique together |
| framework | Nullable — e.g. "tensorflow", "pytorch", "onnx" |
| license | Nullable — must be filled in before any model is marked active |
| input_size | Nullable — e.g. "224x224" |
| supported_crop_ids | JSONB array of `crop_master.id` values |
| is_active | Exactly one row should be active at a time (not DB-enforced this phase — a service-layer convention, revisit if this ever causes confusion) |

## Current state

| name | version | is_active | Meaning |
|---|---|---|---|
| crop_disease_baseline | unconfigured-0.0 | **false** | The honest "no real model is configured" placeholder. Every `AIAnalysis` this phase points here (via the fallback lookup in `ai_reference_repository.get_fallback_not_configured_model`), since no row has `is_active=true`. |

## Rule: never silently swap an active model

Activating a new model version is:
1. Insert a **new** row (new name/version).
2. Set `is_active=true` on the new row, `is_active=false` on the old one,
   in the same transaction.
3. The old row is never deleted — every `AIAnalysis` that referenced it
   (via the immutable `model_name`/`model_version` strings, not just the
   FK) still correctly identifies which model produced it.

No code path in this phase performs this activation — it's a manual
registry-management action for whoever integrates the first real model.

## License tracking

Every future real model added here must have `license` populated with a
value verified against the model's actual license terms *before*
`is_active` is ever set to true — see docs/AI_ARCHITECTURE.md's candidate
evaluation table for why none of the candidates considered this phase
could be verified yet.
