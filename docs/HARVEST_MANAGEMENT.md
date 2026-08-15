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
