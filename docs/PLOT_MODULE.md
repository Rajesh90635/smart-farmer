# Plot Module

## Data model

`Plot` (`app/models/plot.py`) — belongs to exactly one `Farm`. A farm may
have multiple plots.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| farm_id | UUID | FK → farms.id, indexed, `ON DELETE CASCADE` |
| plot_name | string(200) | required |
| area_value, area_unit, area_sqm | same design as Farm | see FARM_MODULE.md |
| latitude, longitude | Numeric(9,6), nullable | optional plot-specific location, same privacy rule as Farm |
| soil_type | string(100), nullable | **free text, not a controlled vocabulary** — flagged assumption below |
| irrigation_type | string(100), nullable | same |
| status | enum: active/inactive | soft-delete flag, shared `farm_status` enum with Farm |
| created_at, updated_at | timestamptz | |

**Assumption flagged, not silent:** `soil_type` and `irrigation_type` are
plain strings because the approved architecture doesn't define an
authoritative taxonomy for either yet. Inventing one here would mean
guessing at a decision that belongs to the future soil-report-OCR /
irrigation-advisor modules. Revisit when those are designed.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/farms/{farm_id}/plots` | Create under a farm — farm ownership checked first |
| GET | `/api/v1/farms/{farm_id}/plots` | List for a farm (paginated) |
| GET | `/api/v1/plots/{plot_id}` | Get mine |
| PUT | `/api/v1/plots/{plot_id}` | Partial update |
| DELETE | `/api/v1/plots/{plot_id}` | Soft delete |

## Ownership enforcement

A plot has no `farmer_id` of its own — ownership is always resolved by
joining `Plot → Farm.farmer_id` (`plot_repository.get_owned`). This join is
never skipped, including on create (the farm is fetched and
ownership-checked *before* a plot is created under it) — verified by
`test_cannot_create_plot_under_another_farmers_farm`.

## Audit events

`PLOT_CREATED`, `PLOT_UPDATED`, `PLOT_DEACTIVATED`.

## Testing

See `backend/tests/test_plots.py` — full CRUD, deactivation, creation
under another farmer's farm (rejected), and direct cross-farmer plot
access (rejected, 404). All passing — see PROJECT_STATUS.md.
