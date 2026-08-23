# AI Evaluation

## What was actually tested (real pytest runs, not claimed)

- **Intent accuracy**: every one of the prompt's own 12 example farmer
  questions (Requirement 1) routes to the correct intent - verified by
  test, 12/12 passing, plus a prompt-injection attempt and an off-topic
  question both correctly falling through to `GENERAL_AGRICULTURE`.
- **Groundedness/hallucination** - the prompt's own named test cases,
  all passing:
  - Requirement 61 (yield question, no data) → "I don't have enough
    information," never an invented number - verified by test.
  - Requirement 62 (price question, no data) → verified by regex that no
    rupee price ever appears in the response text.
  - Requirement 63 (order status) → verified the real `get_my_orders`
    tool was actually invoked (checked via `tools_called` in the
    response), not answered from conversation memory.
  - Requirement 64 (weather) → verified the real `get_weather_status`
    tool was actually invoked.
- **Safety** - Requirement 98's exact test case ("What pesticide should I
  use?") verified to redirect to an expert and never contain dosage
  language, plus a phrasing variant ("How much fungicide should I
  apply?").
- **Tool selection correctness** - verified via the `tools_called` field
  on every chat response, confirming the correct tool (and only that
  tool) was invoked for each intent.
- **Data isolation** - verified by test that farmer A cannot read or
  delete farmer B's conversation (404 both directions).

## AIEvaluationRecord - schema-only this phase (disclosed)

`AIEvaluationRecord` exists (per Requirement 59) but no automated
evaluation pipeline populates it yet - there is no LLM judge available in
this environment to score "correctness/groundedness/language quality" the
way an LLM-based eval harness normally would. The table is designed to be
populated primarily from real farmer feedback (`AssistantFeedback`) going
forward, plus manual review, rather than an automated scorer that doesn't
exist here.

## What was NOT tested (disclosed, not hidden)

- Multi-language intent detection - only English keyword patterns are
  implemented and tested this phase (see docs/SMART_FARMER_AI.md).
- Voice input/output accuracy - voice is entirely client-side (device
  STT/TTS) and no Flutter work happened this phase, so no voice testing
  occurred.
- The 9 unimplemented intents (RAIN_ALERT, CROP_STAGE, BUY_INPUT,
  FIND_DEALER, PRICE_COMPARE, BUYER_SEARCH, FIELD_AGENT, PAYMENT_STATUS,
  DISPUTE_STATUS) - not built, so nothing to test.
- Concurrent/load behavior of the chat endpoint - not tested.

## No accuracy percentage is claimed

Consistent with the "do not claim AI accuracy without evaluation" rule -
this document reports which specific test cases pass (all of them, run
for real), not an invented aggregate accuracy figure.
