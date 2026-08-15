"""
Deterministic intent router. NOT an LLM - a farmer's message is matched
against keyword patterns for each intent, in a fixed priority order. This
is a deliberate architectural choice, not a placeholder for a future LLM:
per "do not build a generic chatbot," a router that can only ever select
from a fixed, closed set of intents - each backed by a real tool call
against real data - cannot hallucinate a price, invent an order status,
or be "prompt injected" into ignoring authorization, because it never
interprets or follows instructions in the farmer's text at all. It only
ever pattern-matches to decide WHICH real tool to call.

Only English keyword patterns are implemented and tested this phase -
consistent with the same honesty already established for localization
(Prompt 7): only English farmer-facing text is fully validated.

Intents implemented this phase (15 of the 23 listed in the spec) are
below. Unimplemented intents fall through to GENERAL_AGRICULTURE.
"""
import enum


class Intent(str, enum.Enum):
    CROP_STATUS = "crop_status"
    DISEASE_STATUS = "disease_status"
    WEATHER = "weather"
    HARVEST_READINESS = "harvest_readiness"
    HARVEST_STATUS = "harvest_status"
    FIND_SEED = "find_seed"
    PRICE_CHECK = "price_check"
    SELL_CROP = "sell_crop"
    BUYER_OFFER = "buyer_offer"
    MY_SALES = "my_sales"
    MY_ORDERS = "my_orders"
    DELIVERY_STATUS = "delivery_status"
    EXPERT_CASE = "expert_case"
    GENERAL_AGRICULTURE = "general_agriculture"
    HELP = "help"


_INTENT_KEYWORDS: list[tuple[Intent, list[str]]] = [
    (Intent.DISEASE_STATUS, ["disease", "spots", "spot on", "sick crop", "what is wrong", "what's wrong", "infection", "fungal", "pest on my"]),
    (Intent.HARVEST_READINESS, ["ready to harvest", "when should i harvest", "harvest time", "harvest ready", "is my crop ready"]),
    (Intent.HARVEST_STATUS, ["harvest status", "my harvest", "how much have i harvested"]),
    (Intent.WEATHER, ["weather", "rain", "will it rain", "temperature", "forecast"]),
    (Intent.EXPERT_CASE, ["expert say", "expert said", "expert case", "what did the expert", "agriculture expert"]),
    (Intent.DELIVERY_STATUS, ["where is my delivery", "delivery status", "when will it arrive", "track my order", "tracking"]),
    (Intent.MY_ORDERS, ["my order", "order status", "where is my order"]),
    (Intent.MY_SALES, ["my sales", "how much have i sold", "sold so far", "quantity remaining", "quantity left", "crop have i sold", "have i sold"]),
    (Intent.BUYER_OFFER, ["buyer offer", "who wants to buy", "interested buyer", "which buyers", "offers on my"]),
    (Intent.SELL_CROP, ["sell my", "sell crop", "want to sell", "i want to sell"]),
    (Intent.PRICE_CHECK, ["current price", "today's price", "what is the price", "price of", "price information"]),
    (Intent.FIND_SEED, ["seed", "seeds", "where can i buy seed", "need seed"]),
    (Intent.CROP_STATUS, ["my crop", "crop status", "what is happening to my crop", "how is my crop", "crop stage"]),
    (Intent.HELP, ["help", "what can you do", "how does this work"]),
]


def detect_intent(message: str) -> Intent:
    text = message.lower().strip()
    for intent, keywords in _INTENT_KEYWORDS:
        if any(kw in text for kw in keywords):
            return intent
    return Intent.GENERAL_AGRICULTURE
