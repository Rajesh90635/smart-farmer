# Professional Network

## Roles reused, not recreated

`FIELD_AGENT`, `EXPERT`, `DEALER`, `ADMIN` already existed (Prompt 3).
Only `TRADER` was added this phase. This phase's "AGRICULTURE_EXPERT" is
the same role as the existing `EXPERT` - no second role was created.

## Data model

`ProfessionalProfile` - one row per professional user, linked via
`user_id` to the existing `User`/auth system (not a second authentication
system). Deliberately consolidates languages, crop/disease specializations,
and service area into JSONB fields rather than three separate child
tables - the same pattern already used by `AIModelRegistry.supported_crop_ids`
(Prompt 6). Revisit with real child tables only if per-row metadata (e.g.
per-specialization years of experience) is ever needed.

| Field | Notes |
|---|---|
| role | One of field_agent, expert, trader, dealer - validated against the single-sourced app.core.roles.Role vocabulary, not a duplicate enum |
| language_codes | JSONB list, validated against the existing SUPPORTED_LANGUAGE_CODES whitelist |
| crop_specialization_ids | JSONB list of crop_master.id strings |
| disease_specialization_categories | JSONB list of free-text categories (fungal/bacterial/viral/pest/...) - configurable, not a hard-coded enum |
| service_area | JSONB object {state, district, taluk, village, approx_latitude, approx_longitude, radius_km} - exactly ONE area per professional this phase (disclosed limitation) |
| verification_status | pending / verified / rejected / suspended / expired - always starts pending, never settable to verified at registration |
| availability_status | available / busy / offline |
| max_active_cases | Workload cap, default 5 |
| completed_case_count | Raw counter - reputation foundation, never a pre-computed "star rating" that could be gamed |
| is_test_account | Flag for clearly-marked seed/demo accounts - not automatically set by any code path this phase; must be set explicitly when seeding test data |

## Verification - admin-only, never self-service

VerificationRecord is an append-only history of admin actions
(verify/reject/suspend/reactivate). ProfessionalProfile.verification_status
is the current state; the record is why/when/who changed it. Verified by
test: test_professional_cannot_self_verify confirms a professional calling
/verify on their own profile gets 403 - only ADMIN-role callers can invoke
any of the four verification endpoints at all.

## Matching algorithm - never solely by distance

app/services/nearby_professional_service.py:find_ranked_candidates scores
each VERIFIED candidate (unverified/rejected/suspended/expired
professionals are excluded at the repository query level, not filtered
out after the fact):

| Factor | Points |
|---|---|
| Availability = AVAILABLE | +30 |
| Availability = BUSY | +5 |
| Crop specialization match | +25 |
| Disease-category specialization match | +20 |
| Language match | +20 |
| Service-area district match | +15 |
| Service-area state match (no district match) | +5 |
| Reputation (completed cases, capped at 20) | up to +5 |
| Available workload headroom | up to +2.5 |

Hard exclusions (never just scored low): workload at/over max_active_cases,
and any professional who already has an assignment record
(pending/accepted/declined/expired) for this exact case - a declined
professional is never re-offered the same case.

Tiebreaker (a real bug found and fixed): when candidates score identically,
the most recently registered verified professional wins. Found via a
genuine test failure - with multiple equally-qualified experts in the
pool, matching was effectively database-order-dependent and
non-deterministic. This is also a defensible real-world tiebreak (gives
newer verified professionals a genuine chance at cases).

## Location privacy

Only service_area (an approximate, professional-declared area) is ever
used for matching or shown to a farmer - a professional's own exact home
location is never collected. A farmer's exact farm coordinates are never
sent to a professional automatically (see docs/PHOTO_SHARING_PRIVACY.md).
