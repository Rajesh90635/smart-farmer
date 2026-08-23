# Farmer AI UX

## Not built this phase - documented as the target for future Flutter work

No Flutter code was written this phase (consistent with every backend-
first phase before this one). This document records the UX requirements
the backend API is already designed to support, so the eventual Flutter
implementation has a clear target.

## Entry point

"Ask Smart Farmer" on the main dashboard, with sub-actions: Ask by Voice,
Type Question, Ask About Photo, Listen to Answer (Requirement 3). The
backend's single `/assistant/chat` endpoint supports both voice
(post-STT text) and typed input identically - see docs/VOICE_ASSISTANT.md.

## Contextual assistant (Requirement 83)

If a farmer is viewing a specific screen (crop, order, harvest), a
context-aware shortcut button ("Ask about this crop") would pre-fill the
question rather than requiring the farmer to re-type information already
on screen. The backend doesn't need any special support for this beyond
what already exists - the relevant tool (`get_crop_status`, etc.) already
resolves "the farmer's most relevant record" without needing an explicit
id, so a screen-contextual "ask" button can just submit a natural-language
question and get the same answer a typed one would.

## Response format for the UI

`ChatResponse` already separates `content` (the answer text),
`sources` (for an optional "source" chip/label), and `confidence` (for an
optional visual indicator) - a future UI can render these as distinct
elements without any backend change.

## Action cards (Requirement 32) - not built

The spec envisions structured UI cards ("View Details" / "Ask Expert" /
"Upload Another Photo" buttons) rather than plain text for certain
answers (e.g. a disease result). The backend currently returns plain text
only - no structured "suggested actions" field exists on `ChatResponse`
yet. This is a real, disclosed gap: adding it would mean extending
`MessageResponse` with an optional `suggested_actions: list[dict]` field,
populated by `response_generator.py` per intent (e.g. disease-detected
responses could suggest `{"action": "ask_expert"}`).

## Response length / simple vs. detailed mode

`AssistantPreference.response_mode` (`simple`/`detailed`) exists in the
schema, but **no code path currently branches behavior on it** - every
response is generated in the same (simple, template-based) way regardless
of the stored preference. A disclosed gap: `response_generator.py` would
need a `detailed` variant for each intent (e.g. including source metadata
and more context) to make this preference actually change anything.

## Safety messaging (Requirement 74)

Not yet surfaced as a standing UI element ("Use verified buyers," "Do not
share OTP/PIN") - this would be a static Flutter-side banner, not
something the backend needs to generate per-response.
