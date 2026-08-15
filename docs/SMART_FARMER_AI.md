# Smart Farmer AI Assistant

## What this actually is - and isn't

**This is NOT a generic chatbot.** It's a deterministic intent router
that maps a farmer's question to one of a fixed set of intents, calls a
real, authorized, read-only tool that queries the farmer's actual
application data, and composes a farmer-friendly answer from a template
- the exact same template system already used for weather/notification
messages (`app/core/farmer_messages.py`, Prompt 7). There is no
generative language model involved in producing any data-backed answer.

## Why this architecture, not an LLM wrapper

Per the explicit "do not build a generic chatbot" instruction and the
absolute rule that the assistant must never invent a price, weather
reading, order status, or diagnosis: a system that can only ever select
from a **closed, fixed set of intents**, each backed by a real database
query, **cannot hallucinate** a fact it wasn't given, because it never
generates free text to answer a data question - it only fills in real
values into a template. This is a stronger guarantee than "we prompted an
LLM not to hallucinate" - it's structurally impossible for this
architecture to invent an order status, because the only way `my_orders`
intent produces text is by first calling the real order-lookup function
and branching on whether it returned data.

## The one place a real LLM slot exists (and honestly isn't filled)

`GENERAL_AGRICULTURE` - open-ended questions that don't match any
specific data-backed intent - is the one place free-form reasoning would
help. `app/services/assistant/ai_provider.py` defines the abstraction for
this; `NotConfiguredAIProvider` is the only implementation actually wired
up, because **no LLM API key is configured in this environment** (see
docs/AI_MODEL_PROVIDER.md for how this was verified, not just assumed).
Every `GENERAL_AGRICULTURE` question today gets an honest
"I don't have enough information to answer that reliably" - never a
fabricated general-knowledge answer.

## Farmer-first design

Responses are 2-5 short sentences, plain language, no unexplained
agricultural jargon. Voice input/output is entirely device-native
(Flutter-side STT/TTS, the same architecture decision Prompt 7 made for
audio) - this backend only ever sees and returns text. See
docs/VOICE_ASSISTANT.md and docs/FARMER_AI_UX.md.

## What's implemented this phase vs. disclosed as future work

15 of the 23 intents listed in the spec are implemented and tested:
`CROP_STATUS`, `DISEASE_STATUS`, `WEATHER`, `HARVEST_READINESS`,
`HARVEST_STATUS`, `FIND_SEED`, `PRICE_CHECK`, `SELL_CROP`, `BUYER_OFFER`,
`MY_SALES`, `MY_ORDERS`, `DELIVERY_STATUS`, `EXPERT_CASE`,
`GENERAL_AGRICULTURE`, `HELP`. Not implemented this phase:
`RAIN_ALERT`, `CROP_STAGE`, `BUY_INPUT`, `FIND_DEALER`, `PRICE_COMPARE`,
`BUYER_SEARCH`, `FIELD_AGENT`, `PAYMENT_STATUS`, `DISPUTE_STATUS` - each
would follow the exact same tool-based pattern already established;
adding one means writing one new tool function + one new intent-keyword
entry + one new response-template branch, not a new architecture.
