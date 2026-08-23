# Farm Module

## Data model

`Farm` (`app/models/farm.py`) — top of the Farmer → Farm → Plot → CropCycle
hierarchy. A farmer may own **multiple** farms; nothing in this schema
assumes 1:1.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| farmer_id | UUID | FK → users.id, indexed, `ON DELETE CASCADE` |
| farm_name | string(200) | required |
| description | string(500), nullable | |
| latitude, longitude | Numeric(9,6), nullable | precise location — see Privacy below |
| area_value | Numeric(12,4) | farmer's original entered value, > 0 (DB CHECK) |
| area_unit | enum: acre/hectare/gunta/cent/square_meter | |
| area_sqm | Numeric(14,4) | canonical value, always derived from (area_value, area_unit) — never entered directly |
| status | enum: active/inactive | soft-delete flag |
| created_at, updated_at | timestamptz | |

## Area units

Canonical internal unit is **square meters**. `app/core/area_units.py`
converts any supported unit to/from square meters — the only place this
math happens. The farmer's originally entered value/unit is always kept
alongside the canonical value for display; area_sqm is derived, not a
second source of truth.

## Privacy

Precise `latitude`/`longitude` are farmer-private data. No endpoint in this
module or any other exposes another role's view of a farm — there is no
"list all farms" or "get any farm by id" route, only `/farms` (mine) and
`/farms/{id}` (mine, 404 otherwise). A coarse/approximate location for
future limited sharing (e.g. with a buyer) is **not** stored as a second
field — it would be computed at the point of sharing, once that workflow
exists, to avoid two sources of truth for one location.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/farms` | Create |
| GET | `/api/v1/farms` | List mine (paginated, `limit`/`offset`) |
| GET | `/api/v1/farms/{farm_id}` | Get mine, 404 if not found or not mine |
| PUT | `/api/v1/farms/{farm_id}` | Partial update |
| DELETE | `/api/v1/farms/{farm_id}` | Soft delete (see below) |

## Soft delete, not hard delete

`DELETE` sets `status = inactive`. A real `DELETE FROM farms` would
cascade-destroy (or orphan) historical plot/crop-cycle data, which the
approved architecture explicitly requires to persist ("crop history
persists across seasons"). Deactivated farms are excluded from
`GET /farms` but remain fully retrievable by id for historical reference.

## Ownership enforcement

Every farm lookup goes through `farm_repository.get_owned(db, farm_id,
farmer_id)` — the single choke point for the `farm.farmer_id ==
current_user` check. A farm that exists but belongs to someone else
returns **404, not 403** — this is what actually prevents ID enumeration
(an attacker can't distinguish "not yours" from "doesn't exist"), not just
a documented policy. Verified by `tests/test_farms.py::test_unauthorized_farm_access_is_rejected`.

## Audit events

`FARM_CREATED`, `FARM_UPDATED`, `FARM_DEACTIVATED` — written via the
existing `AuditLogger`, in the same transaction as the change.

## Testing

See `backend/tests/test_farms.py` — create, list, get, update (including
area-unit-change consistency), deactivate, invalid area, invalid latitude,
and cross-farmer access rejection. All passing — see PROJECT_STATUS.md for
the actual run output.
