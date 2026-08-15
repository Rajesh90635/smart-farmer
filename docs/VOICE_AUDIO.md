# Voice / Audio (Text-to-Speech)

## Decision: device-native TTS, not a backend-generated audio service

Per Requirement 41's explicit instruction to **evaluate** whether
device-native TTS is preferable before building a backend service, and
Requirement 6's "use free/local device capabilities where practical, do
not make a paid cloud TTS mandatory":

**Chosen approach: device-native TTS** (Android `TextToSpeech` /
iOS `AVSpeechSynthesizer`, via Flutter's `flutter_tts` package).

| Consideration | Device-native TTS | Backend-generated TTS (e.g. Piper/Coqui) |
|---|---|---|
| Cost | Free — built into the OS | Free (open-source engines), but requires hosting/running a real TTS engine somewhere |
| Offline capability | Works fully offline once the language voice pack is installed | Requires a network round-trip to the backend every time |
| Infrastructure needed | None | A running TTS engine process, audio file generation, storage, and the caching this phase's requirements ask for |
| Language coverage | Depends on what voice packs are installed on the farmer's device — varies by device/OS/manufacturer, cannot be guaranteed from the backend | Backend controls exactly which languages are supported |
| Latency | Instant (local synthesis) | Network round-trip + synthesis time |

**Verdict:** device-native TTS wins decisively for a free/local-first MVP
— zero infrastructure, zero cost, works offline, matches "the lowest-cost
reliable approach" instruction directly. The backend-generated approach's
one advantage (guaranteed language coverage) is undermined by the fact
that this project also can't verify TTS quality for
Kannada/Telugu/Tamil/Malayalam/Marathi voice packs from this environment
either way — see "Honest limitation" below.

**Consequence:** `POST /api/v1/audio/speak` (listed as a possible endpoint
in the spec) was **not built**. There is no server-side audio generation,
caching, or `AudioCacheMetadata` table this phase — there's no
server-generated audio file to cache. The backend's job stops at
providing **structured, farmer-friendly text**
(`GET /api/v1/ai/analysis/{id}/localized`, notification `body` fields) —
Flutter is responsible for feeding that text to the device's TTS engine.

## What the backend provides for TTS to consume

Every farmer-facing message (AI results via
`ai_result_localization_service.py`, weather/notification alerts via
`farmer_messages.py`) is **structured**, not a single free-form paragraph:
`title`, `confidence_wording`, `next_action` are separate fields, plus a
pre-composed `audio_text` that concatenates them in a sensible reading
order. Flutter can either read `audio_text` directly or compose its own
reading order from the structured fields — both are supported by the
schema (`FarmerFriendlyAnalysisResponse`).

## Audio experience requirements (for the Flutter implementation, not yet built)

Documented here so the requirements aren't lost even though no Flutter
code was written this phase:
- Play / Pause / Replay controls, large and simple.
- Audio does not auto-play by default anywhere —
  `NotificationPreference.audio_alerts_enabled` defaults to **false**
  (opt-in), matching Requirement 8's "should not unexpectedly play audio."
- If TTS fails on-device, the text must remain visible regardless — this
  falls out naturally from the architecture (text is always fetched and
  displayed independently of whether audio synthesis succeeds), but the
  actual Flutter error-handling for a `flutter_tts` failure is not yet
  implemented.
- Audio caching (Requirement 9): since there's no server-generated audio
  file, "caching" in this architecture means Flutter could cache the most
  recently synthesized common phrases in memory to avoid re-synthesizing
  identical text repeatedly within a session — a Flutter-side optimization
  detail, not built this phase.

## Honest limitation

**No language's TTS output was actually tested** — this phase built zero
Flutter code, so no `flutter_tts` call was ever made against a real device
or emulator. Do not claim any language "has audio support" until it's
been manually verified on a real device with the relevant voice pack
installed.
