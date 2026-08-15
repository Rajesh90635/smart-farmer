# Voice Assistant

## Device-native STT/TTS - the same architecture decision as Prompt 7

Per Requirement 4's "Voice -> Speech-to-Text -> AI -> Response ->
Text-to-Speech" flow and the free-first requirement: this backend never
receives or produces audio. Speech recognition happens on the farmer's
device (Android `SpeechRecognizer` / iOS `Speech` framework, or a Flutter
plugin wrapping them) and produces TEXT, which is sent to
`POST /assistant/chat` exactly like typed input - the backend has no way
to distinguish a voice-originated message from a typed one, by design
(this is also why no separate `/assistant/voice` endpoint was built - the
spec's suggested `/assistant/chat` and `/assistant/voice` would be
functionally identical once STT has already run client-side, so a single
endpoint is used, avoiding a duplicate code path).

Text-to-speech for the response uses the same `flutter_tts` device-native
approach Prompt 7 chose for weather/notification audio - not built this
phase since no Flutter work happened, but the architecture decision is
already made and consistent.

## Why this, not a cloud STT/TTS API

Identical reasoning to Prompt 7's `VOICE_AUDIO.md`: zero cost, works
fully offline once installed, no per-request billing, no API key to
protect. A cloud STT/TTS API was evaluated and rejected for the same
reasons documented there - not repeated in full here.

## Language detection (Requirement 5)

The assistant does NOT attempt to detect spoken language itself - it uses
the farmer's own `preferred_language_code` (from `FarmerProfile`, Prompt
3) unless the chat request explicitly overrides it via
`ChatRequest.language_code`. If device-native STT produces text in a
different language than the farmer's stored preference, this backend has
no way to detect that mismatch this phase (no language-detection library
is integrated) - a disclosed gap. The spec's suggested "please select
which language you'd like an answer in" fallback message exists in
`farmer_messages.py`'s pattern conceptually but is not wired to an actual
language-mismatch detector yet.

## Honest testing status

**No language's voice input/output was actually tested** - no Flutter
work happened this phase, so no `flutter_tts`/STT call was ever made
against a real device. Do not claim voice works in any language until
manually verified on a real device, consistent with the same honesty
requirement Prompt 7 already established for TTS.
