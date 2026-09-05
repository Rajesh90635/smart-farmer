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

## Trigger model: weather is now ALSO push-based, alongside pull

D16-10 (docs/audit/README.md): weather alerts are generated two ways now,
both funneling through the same `generate_alerts_for_farm_weather`:

1. Pull-based, as before: whenever a farmer's weather is fetched
   (`GET /farms/{id}/weather`).
2. Proactive: `weather_alert_orchestration_service.run_proactive_weather_alert_sweep`,
   run by the background scheduler (`app/services/scheduler.py`, every
   `proactive_weather_alert_sweep_interval_seconds`, default 30 min) —
   checks every farm with a location, not just ones a farmer happens to
   open the weather screen for. The previously-disclosed "a farmer who
   never opens the app never gets warned of a heavy-rain event" gap is
   closed.

There is still no push notification DELIVERY — a notification exists in
the database and is visible in-app once created, but nothing proactively
wakes the farmer's device (this applies project-wide). What changed is
that the notification now gets CREATED proactively; actually alerting a
farmer who isn't looking at the app is still a future, separate step
(would need a push provider - FCM/APNs - a real infrastructure decision,
not attempted here).

The same scheduler also now drives Expert case reminders, timeout-
reassignment/breach-escalation (docs/CASE_MANAGEMENT.md), input-inventory
low-stock/expiry alerts (docs/INPUT_INVENTORY.md), and harvest status
alerts (see below) — none of these require the farmer or professional to
open any screen first.

## Notification categories (only currently supported types)

`WEATHER_ALERT`, `RAIN_ALERT`, `HEAVY_RAIN_ALERT`, `CROP_ALERT`,
`DISEASE_ALERT`, `HARVEST_ALERT`, `STOCK_ALERT`. `ORDER_ALERT`/`MARKET_ALERT`
are **not** in the enum — they belong to future marketplace phases and
were deliberately excluded rather than added as unused placeholders (this
exclusion was deliberately respected, not overridden, when a later audit
pass considered adding automatic buyer-listing-match notifications — see
docs/audit/README.md's "Third pass, Batch 6").

Note: `DISEASE_ALERT` exists in the category enum and preference model
for forward-compatibility, but **no code path creates one this phase** —
disease results are surfaced via the AI analysis endpoints directly
(`GET /crop-photos/{id}/analysis`, `GET /ai/analysis/{id}/localized`), not
as a notification. Wiring a disease result into a proactive notification
is straightforward future work using the same `NotificationService`.

`HARVEST_ALERT` was previously registered (title + preference mapping)
but never dispatched by any code path (D47-05) — `harvest_service.mark_approaching`
and `confirm_ready` now send one (`HARVEST_APPROACHING`/`HARVEST_READY`),
exactly once per real status transition (a later quantity correction
while already READY does not re-send it).

## Priority levels

`LOW` (routine rain reminder), `MEDIUM` (extreme temperature, crop+weather
combined alert, routine case-lifecycle updates), `HIGH` (heavy rain, high
wind, an Expert SLA reminder before an assignment expires), `CRITICAL`
(now used — real justification required since it bypasses quiet-hours
suppression: an Expert case escalated after repeated professional
timeouts, or a treatment follow-up showing the crop went healthy ->
disease, see `case_service.escalate_case_for_worsened_treatment` and
`case_sla_service._expire_reassign_or_escalate`. No weather scenario uses
CRITICAL yet — that judgment hasn't changed).

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
**Limitation** (weather only — see "Trigger model" above): a
weather-triggered alert suppressed during quiet hours is not
automatically retried once quiet hours end — it's simply not created for
that check cycle, since the weather trigger itself is still pull-based.
If the farmer checks weather again after quiet hours end, a fresh
evaluation happens normally. This limitation does not apply to the
scheduler-driven Expert SLA notifications, which are re-evaluated on
every sweep tick regardless of quiet hours (and CRITICAL escalations
bypass quiet hours entirely).

## Offline notifications (Requirement 30)

Not applicable to the backend (notifications are stored server-side and
fetched on demand) — this is a Flutter-side concern (showing
already-fetched notifications while offline, syncing read-state once
reconnected) that is **not built this phase** since no Flutter work was
done in this phase (see PROJECT_STATUS.md).
