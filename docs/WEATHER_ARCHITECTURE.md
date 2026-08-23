# Weather Architecture

## Pipeline

```
Farm Location (Farm.latitude/longitude, from Prompt 4)
   |
WeatherProvider interface (app/services/weather/weather_provider.py)
   |
OpenMeteoProvider (real, free) OR NotConfiguredWeatherProvider (honest fallback)
   |
WeatherService (cache-or-fetch, app/services/weather_service.py)
   |
WeatherSnapshot (DB cache)
   |
Farmer (GET /api/v1/farms/{farm_id}/weather)
```

Flutter **never** calls the weather provider directly — only this backend
path does, which is what protects any future API key and lets the
provider be swapped by changing one function
(`app/core/weather_provider_dependency.py:get_weather_provider`).

## Provider: Open-Meteo

| Property | Value |
|---|---|
| Provider | [Open-Meteo](https://open-meteo.com) |
| API key required | **No** |
| Cost | Free for non-commercial use; commercial use requires contacting them per their terms |
| License | CC-BY-4.0 — **attribution required** wherever weather data is displayed |
| Rate limits | Documented as "fair use," no hard published cap for the free tier at time of writing — must be monitored in a real deployment |
| Data | Current conditions + up to 16-day forecast, global coverage via multiple national weather models |

## Honest verification status

`OpenMeteoProvider` (`app/services/weather/open_meteo_provider.py`) was
written against Open-Meteo's real, publicly documented response schema —
the field names (`temperature_2m`, `precipitation_probability_max`, etc.)
match the actual API docs exactly. **It has not been exercised against the
live API from this build environment** — a direct `curl` to
`api.open-meteo.com` from this sandbox returned **HTTP 403 from the egress
proxy**, not from Open-Meteo itself (the sandbox's network allowlist
doesn't include weather API hosts). What **was** verified: the response
**parsing logic** (`_parse_response`) against a realistic static fixture
matching the real documented shape — confirmed it correctly extracts
current conditions and a multi-day forecast including sunrise/sunset
timestamps.

**Action required before relying on this in a real deployment:** run
`OpenMeteoProvider.get_weather()` against the live API from a machine with
normal internet access and confirm it returns real data.

## Location hierarchy (Requirement 13)

This phase uses **Farm location** (`Farm.latitude`/`longitude`, set at
farm creation in Prompt 4) as the weather query location. The
farmer-selected-location and device-location layers described in the
approved hierarchy are **not implemented this phase** — farm location is
already the correct granularity for farm-level weather, and adding two
more override layers without a clear immediate need would be
over-engineering. Revisit if a farmer ever needs weather for a location
other than one of their registered farms.

## Caching (Requirement 22)

| Data | Cache TTL (configurable) |
|---|---|
| Current conditions | `weather_current_cache_minutes` (default 30 min) |
| Forecast | `weather_forecast_cache_minutes` (default 180 min) |

A cache hit skips the provider call entirely — verified by
`test_weather_is_cached_on_second_request`, which confirms a second
request within the TTL window returns the *first* fetch's data even when
the underlying provider's data has since changed.

## Failure handling (Requirement 23/51)

1. **Provider unavailable + no cache exists** → `available: false` with
   an honest `unavailable_reason`, never fake data.
2. **Provider unavailable + stale cache exists** → returns the stale data
   with `is_stale: true` and the original `fetched_at` timestamp, so the
   farmer can see it's not current — never presented as live.
3. **No provider configured** (`weather_provider: "none"` in settings) →
   `NotConfiguredWeatherProvider` always reports unavailable — the
   `WEATHER_NOT_CONFIGURED`-equivalent state, applied literally.

Both fallback paths verified by test
(`test_weather_provider_failure_returns_honest_unavailable`,
`test_weather_falls_back_to_stale_cache_when_provider_fails`).

## What this phase does NOT include

Irrigation instructions, guaranteed spray-safety claims, pesticide
recommendations — see docs/WEATHER_ALERT_RULES.md for exactly where the
line is drawn.
