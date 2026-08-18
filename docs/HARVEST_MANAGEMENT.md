# Harvest Management

## Farmer confirmation is the only way past PLANNED - enforced in code

`HarvestRecord.status` starts `PLANNED`. AI (Prompt 6's crop-stage
intelligence) may in the future suggest a crop is approaching harvest,
but **no code path in this phase automatically advances status** -
`harvest_service.mark_approaching()` and `confirm_ready()` are the only
two functions that mutate status past `PLANNED`, and both require an
authenticated farmer's own request. There is no scheduled job, AI
callback, or admin action anywhere in this codebase that does this
automatically. Verified by test
(`test_harvest_never_reaches_ready_without_explicit_farmer_confirmation`).

## Status lifecycle (exactly 8 values, no extras)

`PLANNED` -> `APPROACHING` -> `READY` -> `HARVESTED` -> `LISTED` ->
`PARTIALLY_SOLD` / `SOLD` / `CANCELLED`.

**Disclosed gap:** `HARVESTED`, `PARTIALLY_SOLD`, and the reverse
transition to `SOLD` are not yet driven by any code path this phase -
`create_listing` jumps straight from any prior status to `LISTED`, and
nothing currently transitions a harvest to `PARTIALLY_SOLD`/`SOLD` based
on sale completion. The enum values exist and are ready for that wiring
(a natural next step once `sale_order_service.py`'s completion path is
connected back to the originating `HarvestRecord`).

## Smart pre-fill (Requirement 38)

`GET-or-create /harvests/from-crop-cycle/{id}` reuses the existing
`CropCycle`'s `crop_id`, `plot_id` (and via the plot, `farm_id`), and
`expected_harvest_date` - the farmer never re-enters data already on
file. Calling this twice for the same crop cycle returns the same
`HarvestRecord`, verified by test.

## Multiple harvests per crop cycle (Phase 0)

`CropCycle` has a **one-to-many** relationship with `HarvestRecord`, not
one-to-one. This is required for crops picked repeatedly over a season -
tomato, chilli, okra, brinjal, beans, cucumber - where each picking round
is its own independent harvest event with its own date and quantity, not
a single harvest for the whole cycle.

Two distinct write paths exist, deliberately kept separate:

- `POST /harvests/from-crop-cycle/{crop_cycle_id}` (`get_or_create_harvest_for_crop_cycle`) -
  **idempotent**. For a crop with only one harvest, calling this
  repeatedly always returns the same record - this is the pre-existing
  behavior from before Phase 0, unchanged and still tested
  (`test_calling_get_or_create_twice_returns_same_harvest`,
  `test_existing_single_harvest_get_or_create_behavior_is_unchanged`).
- `POST /harvests/from-crop-cycle/{crop_cycle_id}/new-harvest` (`create_new_harvest_for_crop_cycle`) -
  **never idempotent, always inserts**. Call this again after each
  picking round to record the next harvest. Confirming/updating one
  harvest never affects any other harvest on the same crop cycle - each
  row is fully independent.

`GET /harvests/from-crop-cycle/{crop_cycle_id}` lists every harvest for
that cycle, oldest first.

**What changed at the schema level:** `harvest_records.crop_cycle_id`'s
index went from `unique=True` to `unique=False` (migration
`da873270b431`) - no columns added or removed, no data migrated, table
not recreated.

**What changed at the code level:** the old
`harvest_repository.get_harvest_by_crop_cycle()` used
`scalar_one_or_none()`, which would raise `MultipleResultsFound` once a
crop cycle had more than one harvest. It was replaced by
`get_most_recent_harvest_by_crop_cycle()` (used only by the idempotent
get-or-create path) and `list_harvests_by_crop_cycle()` (the actual
multi-harvest read path) - no other one-to-one assumption was found
anywhere else in the backend (confirmed by a full-codebase search for
`HarvestRecord`/`harvest_record_id` references during this phase;
`assistant/tools.py`'s "most recent harvest" query was already safe,
using explicit ordering + `limit(1)`).

**Not built this phase:** a mobile harvest-list UI - no `mobile/lib`
harvest screens exist yet in this codebase, so there was nothing to
break and nothing new to build here; that remains a future phase.

## Quantity and units - configurable, not hard-coded to one unit

`unit` is a free string (`kg`, `quintal`, `ton`, or anything else) - no
enum forces one unit system. `quality_grade` is similarly free text, not
a rigid `Grade A/B/C` enum, since "allow crop-specific grading rules, do
not assume the same quality criteria apply to every crop" - a formal
crop-specific grading rules engine is not built this phase; grading is
whatever text the farmer/buyer agree on.

## Weather + harvest timing (Requirement 43)

Not wired this phase - `HarvestRecord` has no weather-derived field, and
no code path checks Prompt 7's weather service before suggesting harvest
timing. A future integration point, not built yet.
