# AI Model Provider

## Honestly not configured - verified, not assumed

This environment has **no LLM API key configured**. This was verified
directly, not assumed by default: `api.anthropic.com` is reachable from
this sandbox's network (it's on the egress allowlist), but a real POST
request without an API key correctly returns
`{"type":"error","error":{"type":"authentication_error","message":"x-api-key header is required"}}`
- confirming the network path exists but no credential does. Since no
key can be supplied, `NotConfiguredAIProvider` (`app/services/assistant/not_configured_provider.py`)
is the only provider ever actually used in this build.

## The abstraction (`AIProvider`) is real and ready

`app/services/assistant/ai_provider.py` defines `answer_general_question()`
- a real interface a future implementation could satisfy by calling
Anthropic's (or any other) `/v1/messages` endpoint with a real key read
from `Settings` (never hard-coded, never committed - consistent with
Requirement 73). Swapping in a real provider means writing one new class
and changing `app/core/ai_provider_dependency.py:get_ai_provider()` -
no endpoint, schema, or orchestrator code changes.

## Scope of what this provider would ever be used for

**Only `GENERAL_AGRICULTURE`** - open-ended questions with no matching
data-backed intent. Every other intent (crop status, weather, orders,
disease, marketplace, etc.) is answered entirely by the deterministic
intent router + real tool calls (see docs/SMART_FARMER_AI.md,
docs/AI_TOOL_SYSTEM.md) - configuring a real LLM provider would NOT
change how any of those are answered, by design.

## Free vs. paid (Requirement 71/104)

| Service | Purpose | Free option | Limitations | Estimated cost | When required |
|---|---|---|---|---|---|
| Anthropic Claude API (or any comparable LLM API) | Free-form GENERAL_AGRICULTURE reasoning | None at meaningful quality for this use case - all capable LLM APIs are paid per-token | Requires an API key, ongoing per-request cost, requires prompt-injection/output-safety review before going live | Usage-based, varies by model/volume | Only if open-ended agricultural Q&A beyond the 15 implemented intents is genuinely needed - not required for the assistant to be useful today |

No paid dependency was added. The assistant works entirely without one
for every data-backed intent.
