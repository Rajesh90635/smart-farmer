# AI Cost Control

## Current cost: zero

Since `NotConfiguredAIProvider` is the only provider used, and every
data-backed intent is answered by deterministic routing + real database
queries (never an LLM call), **this assistant currently costs nothing
beyond normal database query load** - there is no per-message API cost to
control, because no paid API is ever called.

## What would matter once/if a real LLM provider is configured

| Control | Status |
|---|---|
| Token limits | Not applicable yet - no LLM calls happen. Would need to be added to any real `AIProvider` implementation before going live. |
| Response length limits | Already true by construction for all data-backed intents (template responses are always short); would need explicit enforcement for a real `GENERAL_AGRICULTURE` LLM response. |
| Request throttling | The existing global rate-limit middleware applies to `/assistant/chat` like every other endpoint - no assistant-specific stricter limit exists (disclosed gap, see docs/AI_GUARDRAILS.md). |
| Caching | Not implemented - every chat call re-queries the database fresh. For read-heavy tools (e.g. `get_seed_products`, which doesn't change per-farmer) a short cache could reduce load, but no caching layer exists this phase. |
| Duplicate question detection | Not implemented - two identical consecutive questions each trigger a fresh tool call and a new `AssistantMessage` row. |
| Model selection by task | Moot - only one (not-configured) provider exists; no routing between "cheap" and "strong" models happens because no model is called at all. |

## Database query cost - the only real cost this phase

Every tool call is a single, indexed, farmer-scoped query (e.g. `WHERE
farmer_id = ... ORDER BY updated_at DESC LIMIT 1`) - no N+1 patterns, no
unbounded scans. This was verified by code review of `tools.py`, not a
formal load test (none was run this phase).
