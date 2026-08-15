# Weather Alert Rules

## All thresholds are configurable, none are agriculturally validated

Per the explicit instruction not to hard-code thresholds or claim
agricultural safety from arbitrary values, every threshold below lives in
`app/core/config.py` (`Settings`), not a literal buried in a conditional —
but the **values themselves are placeholders**, not the output of any
agronomic study. Treat them as reasonable defaults to build against, not
as validated safety limits.

| Setting | Default | Meaning |
|---|---|---|
| `weather_rain_probability_threshold` | 40% | Above this: a "rain is likely" alert |
| `weather_heavy_rain_probability_threshold` | 70% | Above this: a "heavier rain expected" alert |
| `weather_heavy_rain_mm_threshold` | 20 mm/day | Alternate trigger for heavy-rain alert, independent of probability |
| `weather_high_wind_kmh_threshold` | 40 km/h | Triggers a high-wind alert and a spray-condition warning |
| `weather_extreme_heat_celsius_threshold` | 40°C | Triggers an extreme-heat alert |
| `weather_extreme_cold_celsius_threshold` | 5°C | Triggers an extreme-cold alert |

## Rules implemented (`app/services/weather_alert_rules.py` — pure functions, no I/O)

| Rule | Behavior |
|---|---|
| Rain alert | Fires at `LOW` priority when today's rain probability ≥ threshold — wording is always "rain is likely," never "it will rain" |
| Heavy rain alert | Fires at `HIGH` priority when probability or forecast mm crosses the heavy threshold — supersedes the plain rain alert (only one of the two fires) |
| High wind alert | `HIGH` priority |
| Extreme heat/cold alert | `MEDIUM` priority |
| Crop + weather combined alert | Only fires for the heavy-rain scenario currently — the one case supportable without inventing unvalidated agricultural logic. Combines crop name + the farmer's own confirmed `CropCycle.cultivation_status` (never an AI-suggested stage — see docs/CROP_STAGE_MODEL.md) with the weather condition |
| Spray-condition warning | Weather-condition-only (`app/services/weather_alert_rules.py:evaluate_spray_condition_warning`) — fires on high wind or imminent rain. **Verified by test to never mention a pesticide, chemical, dosage, or brand** (`test_never_recommends_a_specific_pesticide_or_dosage`) |

## Absolute rules enforced (verified by test)

- **Never claims certainty** — every rain-related message uses probability
  wording ("likely," "expected"), never a definite claim. The rule
  functions pass the raw probability through as a message parameter
  rather than converting it to a yes/no claim.
- **Never recommends a pesticide, chemical, or dosage** — the spray
  warning is structurally limited to "conditions may not be suitable,"
  full stop. No code path in this module can produce a chemical name.
- **Never issues an irrigation instruction** — no irrigation-decision rule
  exists this phase (Requirement 21 explicitly scopes this out); only the
  general weather data itself is available to a farmer via the weather
  screen.

## Crop-stage input note

The "crop stage" used in the combined crop+weather alert is the
**farmer-confirmed** `CropCycle.cultivation_status` from Prompt 4 — never
an AI-suggested stage (the AI crop-stage feature, `AICropStageResult`, has
no working model behind it yet per docs/CROP_STAGE_MODEL.md, and even if
it did, using an unconfirmed AI suggestion to drive a farmer-facing alert
would violate the "AI must never silently override farmer data" rule from
the AI phase).
