# Notification Architecture

## Pipeline

```
Event (e.g. a weather check, an AI analysis)
   |
Notification Rule (app/services/weather_alert_rules.py for weather;
                    the AI pipeline itself for AI-adjacent alerts - not
                    built this phase, see Limitations)
   |
NotificationService (app/services/notification_service.py) - decides:
   - Is this category enabled in the farmer's preferences?
   - Is it currently quiet hours (and is this non-critical)?
   - Has this exact alert already been sent (dedup)?
   |
Language (farmer's preferred_language_code, from FarmerProfile)
   |
Notification (rendered, stored, ready to read)
   |
Farmer
```

## Trigger model: pull-based, not push-based (a disclosed limitation)

Alerts are generated **when the farmer's weather is fetched**
(`GET /farms/{id}/weather` also runs alert evaluation as a best-effort side
effect — see `app/services/weather_alert_orchestration_service.py`), not
by a background scheduler proactively checking weather for every farmer
on a timer. This means:
- A farmer who never opens the weather screen for a farm won't get alerts
  for it, even if dangerous weather is happening.
- There is no push notification delivery — a notification exists in the
  database and is visible in-app once created, but nothing proactively
  wakes the farmer's device.

This is a **deliberate scope decision**, not an oversight: building a
background scheduler + push delivery is real infrastructure (a
queue/worker, a push provider) that the "do not introduce a complicated
distributed architecture unnecessarily" instruction argues against
building before it's clearly needed. The `NotificationService` and
`AlertCandidate` interfaces are designed so a future scheduler can call
the exact same functions this phase's weather endpoint calls — no
redesign needed, only a new caller.

## Notification categories (Requirement 24 — only currently supported types)

`WEATHER_ALERT`, `RAIN_ALERT`, `HEAVY_RAIN_ALERT`, `CROP_ALERT`,
`DISEASE_ALERT`, `HARVEST_ALERT`. `ORDER_ALERT`/`MARKET_ALERT` are **not**
in the enum — they belong to future marketplace phases and were
deliberately excluded rather than added as unused placeholders.

Note: `DISEASE_ALERT` exists in the category enum and preference model
for forward-compatibility, but **no code path creates one this phase** —
disease results are surfaced via the AI analysis endpoints directly
(`GET /crop-photos/{id}/analysis`, `GET /ai/analysis/{id}/localized`), not
as a notification. Wiring a disease result into a proactive notification
is straightforward future work using the same `NotificationService`.

## Priority levels

`LOW` (routine rain reminder), `MEDIUM` (extreme temperature, crop+weather
combined alert), `HIGH` (heavy rain, high wind), `CRITICAL` (reserved,
never used this phase — no weather scenario in this project's rule set
was judged to warrant it; CRITICAL alerts also bypass quiet-hours
suppression, so assigning it needs real justification, not routine use).

## Deduplication (Requirement 27)

Enforced by a **database unique constraint** on `(farmer_id, dedup_key)`,
not just an in-memory or application-level check — safe under concurrent
requests. `dedup_key` is built as
`{category}:{scope}:{suffix}`, e.g.
`heavy_rain_alert:farm:{farm_id}:2026-06-01:heavy_rain` — encoding the
category, the subject (farm or crop cycle), and a day-bucket, so the same
real event never produces two rows but a genuinely new day or a different
farm correctly gets its own notification. Verified by
`test_repeated_weather_checks_do_not_duplicate_the_same_alert` (three
consecutive weather checks in the same test produce exactly one
notification).

## Preferences (Requirement 28)

One `NotificationPreference` row per farmer, auto-created with defaults on
first access. All categories default **ON** except `audio_alerts_enabled`,
which defaults **OFF** (opt-in, not opt-out) per the "automatic playback
should be configurable and respectful" instruction.

## Quiet hours (Requirement 29)

`is_within_quiet_hours()` is a pure predicate supporting both same-day
ranges (e.g. 13:00–14:00) and overnight-wrapping ranges (e.g. 22:00–06:00),
verified by test for both cases. Applied only to non-`CRITICAL` alerts.
**Limitation** (see "Trigger model" above): since there's no background
scheduler, a suppressed alert during quiet hours is not automatically
retried once quiet hours end — it's simply not created for that check
cycle. If the farmer checks weather again after quiet hours end, a fresh
evaluation happens normally.

## Offline notifications (Requirement 30)

Not applicable to the backend (notifications are stored server-side and
fetched on demand) — this is a Flutter-side concern (showing
already-fetched notifications while offline, syncing read-state once
reconnected) that is **not built this phase** since no Flutter work was
done in this phase (see PROJECT_STATUS.md).
