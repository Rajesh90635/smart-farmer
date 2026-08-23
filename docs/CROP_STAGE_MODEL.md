# Crop Stage Model

## Data model

`CropStageDefinition` (`app/models/crop_stage_definition.py`) — crop-aware,
per Requirement 17's explicit instruction NOT to assume every crop uses
the same stage set. Stages are rows scoped to `crop_id`, not a shared
Python enum.

| Field | Notes |
|---|---|
| crop_id | FK → crop_master; unique with stage_code |
| stage_code | e.g. "seedling" |
| display_name | e.g. "Seedling" |
| sequence_order | Int — defines the expected progression order for that crop |
| is_active | |

## Seed data — same generic set for every seeded crop (a disclosed limitation)

| Order | stage_code | display_name |
|---|---|---|
| 1 | seedling | Seedling |
| 2 | vegetative | Vegetative Growth |
| 3 | flowering | Flowering |
| 4 | fruiting | Fruiting |
| 5 | maturation | Maturation |
| 6 | ready_for_harvest | Ready for Harvest |

Applied identically to both seeded crops (Tomato, Rice). **This does not
yet demonstrate genuine per-crop divergence** — no crop-specific stage
research was available this phase. The schema fully supports a different
crop having a different stage set (e.g. a perennial crop with no discrete
"harvest-ready" stage, or a crop with a "tillering" stage rice actually
has agronomically but wasn't added here) — that's a data problem to solve
per-crop as each is added, not a schema limitation.

## AI crop-stage result: architecture only, not wired to an endpoint

`AICropStageResult` (`app/models/ai_crop_stage_result.py`) exists with the
fields Requirement 18 asks for (crop_cycle, predicted_stage, confidence,
model/version, timestamp, requires_review) — but **no endpoint calls it
this phase**. This is a disclosed scope decision, not an oversight:

- `ModelProvider.predict_stage()` exists in the interface and
  `NotConfiguredModelProvider.predict_stage()` correctly returns
  `available=False` — the same honest "no model" story as disease
  detection.
- Since disease detection and crop-stage estimation would use the exact
  same non-existent model infrastructure (no real model provides either
  capability yet), building a parallel `/analyze-stage` endpoint this
  phase would be plumbing for a capability with zero real backing —
  effort better spent once a real model that can also do stage estimation
  exists.
- The table, the model-provider method, and the strict separation from
  farmer-official data (see below) are all real and ready; only the
  endpoint wiring is deferred.

## AI observation vs. official data (Requirement 18/19) — enforced structurally

`CropCycle.cultivation_status` (the farmer-official field, from Prompt 4)
is **never written by any AI code path** in this phase — verified by
inspection: no file under `app/services/ai*` imports or modifies
`CropCycle`. `AICropStageResult` would be a fully separate, additive
observation table even once wired up — promoting a suggestion into the
official record would require a distinct, explicit farmer/expert
confirmation endpoint that doesn't exist yet, exactly as required:

```
AI observation (AICropStageResult, once built)
   -> Farmer confirmation OR Expert confirmation (future module)
   -> Official CropCycle.cultivation_status update (farmer-only endpoint, unchanged since Prompt 4)
```
