# AI Architecture (Smart Farmer Assistant)

> This supplements, rather than replaces, the AI_ARCHITECTURE.md content
> already established in Prompt 6 for disease-detection AI - that
> architecture (ModelProvider, NotConfiguredModelProvider, the safety
> layer) is REUSED unchanged by this assistant's `get_disease_status`
> tool, not duplicated.

## The pipeline (matches the required architecture exactly)

```
Flutter
   |
Assistant API (app/api/v1/assistant.py)
   |
Authentication (existing JWT, unchanged)
   |
Safety pre-check (app/services/assistant/safety_validator.py) - prescription
   |                requests never reach normal routing at all
Intent Router (app/services/assistant/intent_router.py) - deterministic
   |
AI Orchestrator (app/services/assistant_service.py)
   |
Authorized Tools (app/services/assistant/tools.py) - farmer-scoped, read-only
   |
Data/Services (EVERY existing repository/service from Prompts 4-10, reused)
   |
Response Generator (app/services/assistant/response_generator.py) - templated
   |
Safety Validator (post-check, defense in depth)
   |
Localization (app/core/farmer_messages.py, reused from Prompt 7)
   |
TTS - device-native, Flutter-side (see docs/VOICE_ASSISTANT.md)
   |
Flutter
```

## Every existing AI/data service reused, none duplicated

| Prior system | Reused by this phase as |
|---|---|
| `app/services/ai/` (Prompt 6 - ModelProvider, confidence, safety layer) | `get_disease_status` tool reads `AIAnalysis` rows this system already produces - never re-runs analysis, never re-implements confidence classification (calls `classify_confidence` directly) |
| `app/services/weather_service.py` (Prompt 7) | `get_weather_status` tool calls it directly, including its caching/staleness/honest-unavailable behavior |
| `app/core/farmer_messages.py` (Prompt 7) | Every assistant response template lives in this SAME file, using the SAME `get_message()` function |
| Case management (Prompt 8) | `get_expert_case_status` reads `CropHealthCase`/`CaseReview` directly |
| Order/product/dealer system (Prompt 9) | `get_my_orders`, `get_delivery_status`, `get_seed_products` read these tables directly |
| Harvest/marketplace (Prompt 10) | `get_harvest_status`, `get_buyer_offers`, `get_my_sales` read these tables directly |

## Response format (Requirement 44) - implemented as structured fields, not enforced prose

Rather than forcing every response into an "ANSWER/WHY/WHAT YOU CAN
DO/IMPORTANT" prose block (which would fight against the "2-5 short
sentences" simplicity requirement), the structured provenance IS this
breakdown, just as machine-readable fields rather than baked into text:
`content` (the answer), `sources` (the "why" - where the fact came from),
`confidence` (whether "important" caveats about certainty apply). A
future Flutter UI can render these as separate visual sections if
desired; the API already carries the separation.
