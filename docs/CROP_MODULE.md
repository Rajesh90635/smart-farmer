# Crop Module (Crop Master + Crop Cycle)

## Why two entities, not one

Per the explicit "do not simply attach a crop directly to a plot" rule,
this module has:
- **`CropMaster`** — a reusable reference table (Tomato, Rice, ...). Never
  duplicated per cycle.
- **`CropCycle`** — one cultivation instance on a `Plot`, over a defined
  period, pointing at a `CropMaster` row via `crop_id`.

A plot can have many crop cycles over time, all retained:
`Plot A → Tomato (harvested) → Onion (planted)` — both rows exist forever.
Verified by `test_plot_can_have_sequential_crop_cycles_preserving_history`.

## CropMaster

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | string(150), unique | canonical name |
| local_names | JSONB, nullable | `{language_code: name}` — adding a language never needs a migration |
| scientific_name | string(200), nullable | |
| category | string(100), nullable, indexed | e.g. cereal/vegetable/fruit/cash_crop |
| is_active | boolean | |
| crop_metadata | JSONB, nullable | extensibility hook for future disease/stage/weather/treatment rules — unused so far |

**Seed data:** 12 illustrative crops (Rice, Wheat, Maize, Tomato, Onion,
Chilli, Banana, Cotton, Sugarcane, Groundnut, Coconut, Black Pepper) with a
few example local names. **This is not an authoritative agricultural
dataset** — just enough to exercise crop selection end-to-end. Expand
deliberately, one verified entry at a time.

`GET /api/v1/crops/master?query=` — searchable lookup (name substring
match), backing the Flutter searchable crop-selection UI. There is no
free-text crop-name field anywhere in `CropCycle` — a cycle always
references a real `crop_id`.

## CropCycle

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| plot_id | UUID | FK → plots.id, `ON DELETE CASCADE` |
| crop_id | UUID | FK → crop_master.id, `ON DELETE RESTRICT` (a crop can't be deleted while cycles reference it) |
| season | enum: kharif/rabi/zaid/perennial/other, nullable | |
| sowing_date | date, required | |
| expected_harvest_date | date, nullable | DB CHECK: ≥ sowing_date |
| actual_harvest_date | date, nullable | DB CHECK: ≥ sowing_date; set only by the close/harvest action |
| cultivation_status | enum, see below | the single farmer-official status |
| seed_variety | string(150), nullable | |
| ai_suggested_stage, ai_confidence, ai_observation_at, ai_model_version | nullable | **future AI hook — see below** |

### Cultivation status & transitions

```
PLANNED → SOWN → GROWING → FLOWERING → FRUITING → READY_FOR_HARVEST → HARVESTED
   ↓        ↓        ↓          ↓           ↓              ↓
   └────────┴────────┴──────────┴───────────┴──────────────┴──→ CANCELLED
```
- Forward-only — no backward transitions, ever.
- `CANCELLED` reachable from any non-terminal state.
- `HARVESTED` and `CANCELLED` are terminal — nothing transitions out.
- Enforced in `app/models/crop_cycle.py:ALLOWED_TRANSITIONS` and checked in
  `crop_cycle_service._validate_transition` — an invalid transition returns
  `409 Conflict`. The Flutter UI only ever offers the single valid "next"
  status as a button (`nextStatusAfter` in `farm_models.dart`), but the
  backend is the actual enforcement point regardless of what the client
  sends.
- Closing (`POST /crops/{id}/close`) is only valid from `READY_FOR_HARVEST`
  and requires `actual_harvest_date >= sowing_date`.

### Future AI integration hook (not implemented)

`ai_suggested_stage`, `ai_confidence`, `ai_observation_at`,
`ai_model_version` exist on the model but are **never written or read by
any code in this phase** — confirmed by the fact that no service or
repository function references them. Future flow, once built:
```
AI observation → confidence → farmer confirmation OR expert confirmation → official cultivation_status
```
An AI suggestion must never silently overwrite `cultivation_status` — only
an explicit farmer/expert confirmation action (a future module) would ever
promote a suggestion into the official field.

### Future weather / disease / marketplace — deliberately NOT here

- Weather data is never stored on `Farm`/`Plot`/`CropCycle` directly — it
  will be its own future module, joined by `plot_id` when built.
- Disease/photo/AI-analysis data is never mixed into `CropCycle` — a
  future `CropImage`/`ImageAnalysis`/`DiseaseCase` chain will reference
  `crop_cycle_id`, not add columns here.
- Marketplace fields (harvest quantity, quality, buyer, offer) are **not**
  pre-added to `CropCycle` "just in case" — future `HarvestForecast`/
  `CropLot` entities will reference `crop_cycle_id` when that module is
  built.

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/crops/master?query=` | Searchable crop reference lookup |
| POST | `/api/v1/plots/{plot_id}/crops` | Create a crop cycle — plot ownership checked first |
| GET | `/api/v1/plots/{plot_id}/crops` | List cycles for a plot (paginated, newest sowing_date first) |
| GET | `/api/v1/crops/{crop_cycle_id}` | Get mine |
| PUT | `/api/v1/crops/{crop_cycle_id}` | Update dates/season/seed_variety and/or advance status (validated) |
| POST | `/api/v1/crops/{crop_cycle_id}/close` | Harvest — requires `ready_for_harvest`, sets `actual_harvest_date` + `HARVESTED` |

## Ownership enforcement

Two joins deep: `CropCycle → Plot → Farm.farmer_id`
(`crop_cycle_repository.get_owned`). Never skipped, including at creation
(plot ownership checked before a cycle is created under it).

## Audit events

`CROP_CYCLE_CREATED`, `CROP_CYCLE_UPDATED`, `CROP_CYCLE_STATUS_CHANGED`
(logged separately from `CROP_CYCLE_UPDATED` whenever a status change is
part of the update), `CROP_CYCLE_CLOSED`.

## Testing

See `backend/tests/test_crop_cycles.py` — crop search, create, list,
sequential-history preservation, full valid transition sequence, invalid
(skip-ahead) transition, backward transition, post-terminal transition,
cancellation-from-any-active-state, invalid dates, close requiring
`ready_for_harvest`, successful close, and cross-farmer access at both the
plot-creation and cycle-access levels. All passing — see PROJECT_STATUS.md.
