# Localization

## Architecture

Flutter's standard `gen-l10n` tooling, configured via `mobile/l10n.yaml`:
- Source strings live in `.arb` files under `mobile/lib/l10n/`.
- `app_en.arb` is the template (and currently the only populated language).
- No farmer-facing text is hard-coded directly into widgets — every screen
  should reference generated `AppLocalizations` keys, not literal strings,
  from the first real (non-placeholder) screen onward. The current
  placeholder screens intentionally use literal text since they're
  temporary scaffolding, not farmer-facing UI.

## Adding a new language

1. Create `mobile/lib/l10n/app_<code>.arb` (e.g. `app_hi.arb` for Hindi,
   `app_ml.arb` for Malayalam, `app_kn.arb` for Kannada, `app_te.arb` for
   Telugu, `app_ta.arb` for Tamil, `app_mr.arb` for Marathi) with the same
   keys as `app_en.arb`, translated.
2. Add the corresponding `Locale('<code>')` to `supportedLocales` in
   `lib/app.dart`.
3. Run `flutter gen-l10n` (or just `flutter run` — it regenerates
   automatically).

No other code changes are needed — this is the entire point of setting the
abstraction up now rather than after screens with hard-coded English exist.

## Open decision

Which language(s) get priority for the first real pilot is listed as an
open question in the approved architecture document (target language(s)
for STT/TTS/localization) — not yet answered. The `.arb` structure above
supports any of them equally; the decision only affects which file gets
populated first.

## Backend-driven farmer-facing text (Weather + Voice + Alerts phase)

AI results and weather/notification alerts are rendered server-side using
`app/core/farmer_messages.py` — a structured `(message_key, language_code)`
template system, **not** Flutter's `AppLocalizations` (which is for
static UI chrome like button labels). Only English is fully populated;
other languages fall back to English with no empty/missing message ever
produced (verified by test). See docs/AI_ARCHITECTURE.md's localization
bridge and docs/WEATHER_ALERT_RULES.md for what uses this system.

**Why native-speaker translations weren't added this phase:**
auto-translating agricultural/safety-relevant text without review would be
worse than clearly falling back to English — a mistranslated disease or
weather warning is actively harmful in a way a farmer correctly
recognizing "this is in English, not my language" is not.

## Known gap (Auth + Farmer Profile phase)

The new auth screens (Register, Login, Language Selection, Consent,
Profile) use hard-coded English strings, **not** `AppLocalizations` keys —
contrary to the "no hard-coded farmer-facing text" principle stated above.
This was a deliberate scope trade-off to keep this phase moving given that
the target-language decision (which language ships first) is still an
open question in the approved architecture — worth fixing once that
decision is made, but not before, to avoid translating strings twice.
Tracked in PROJECT_STATUS.md as a known issue, not silently left
unmentioned.

## Backend-side localization

The backend and AI service do not localize UI text (they have none) — but
any farmer-facing string the *backend* generates (e.g. a future daily
briefing or diagnosis explanation) must be produced in the farmer's
`preferred_language` once that field exists on the Farmer model. That's a
Farmer-module concern, not part of this foundation.
