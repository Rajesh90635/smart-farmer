# AI Tool System

## Tool security - the absolute rule, verified structurally

Per Requirement 19: "do not trust farmer_id/order_id/crop_id sent by the
model." This architecture makes that guarantee stronger than a
permission check - **no tool function accepts any entity id parsed from
the farmer's free-text message at all**. Every tool signature is
`tool(db, farmer_id)` where `farmer_id` comes ONLY from the authenticated
JWT session (`current_user.user_id`), never from the message body. There
is no code path anywhere in `app/services/assistant/tools.py` that reads
an id out of the farmer's question. "Which order/crop/case" is always
resolved as "the calling farmer's own most-relevant (most recent) record"
- this is what makes cross-farmer data access structurally impossible
rather than merely checked-for.

## Implemented tools (10)

| Tool | Reuses | Returns |
|---|---|---|
| `get_crop_status` | Farm/Plot/CropCycle/CropMaster (Prompt 4) | Crop name, farm name, stage, dates |
| `get_disease_status` | AIAnalysis + confidence classifier (Prompt 6) | Result status, predicted class (only if not low-confidence, matching the safety layer's own rule), confidence level, requires_review |
| `get_weather_status` | weather_service.get_farm_weather (Prompt 7) | Availability, staleness, temperature, rain probability |
| `get_harvest_status` | HarvestRecord (Prompt 10) | Status, expected date, estimated quantity |
| `get_buyer_offers` | HarvestListing + BuyerOffer (Prompt 10) | Active offer count and top offers on the farmer's own listing |
| `get_my_sales` | SaleOrder (Prompt 10) | Total sale count, most recent sale status/value |
| `get_my_orders` | Order (Prompt 9) | Most recent order status/amount |
| `get_delivery_status` | Delivery (Prompt 9) | Delivery status, estimated date |
| `get_expert_case_status` | CropHealthCase + CaseReview (Prompt 8) | Case status, final verified class, latest review outcome |
| `get_seed_products` | Product catalog, category=SEED (Prompt 9) | Up to 5 approved seed products |

Every tool returns a **small, structured dict** - never a raw ORM object,
never a full row, never any field not needed for the response (Requirement
20). Every tool includes a `source` string identifying exactly which
system produced the data - this is what populates `AssistantMessage.sources`.

## What's NOT built this phase (disclosed)

The 8 tools implied by unimplemented intents (`get_market_offers` beyond
the farmer's own listing, dealer search, payment-status-specific lookup,
dispute-status-specific lookup, field-agent-scoped tools, etc.) don't
exist yet - see docs/SMART_FARMER_AI.md for exactly which intents this
maps to.

## Admin/expert/field-agent AI access - NOT built this phase

Requirements 53-55 (separate admin AI analytics, field-agent-scoped AI
capabilities, expert AI case-summarization) are not implemented - the
entire assistant this phase is farmer-facing only
(`require_role(Role.FARMER.value)` on every endpoint). Building
role-specific assistant variants would follow the same tool-based
pattern, scoped to each role's own authorized data, but that work isn't
done yet.
