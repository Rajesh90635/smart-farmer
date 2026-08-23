# Prompt 11 — Assumptions and Risks

## AI accuracy

- **KNOWN**: For the 15 implemented intents, "accuracy" means intent-
  keyword-matching correctness (verified 12/12 against the prompt's own
  example questions) and tool-call correctness (verified via
  `tools_called`) - not generative-model accuracy, since no generative
  model is used for any data-backed answer.
- **NEEDS VALIDATION**: Real-world keyword coverage - only ~14 keyword
  patterns per intent were written and tested against a small example
  set; real farmer phrasing variety (typos, colloquialisms, code-mixed
  language) is untested.

## Crop disease uncertainty

- **KNOWN**: Fully inherited from Prompt 6 - `get_disease_status` never
  overrides or reinterprets the confidence/result_status the AI safety
  layer already computed.

## Language accuracy / speech recognition / TTS quality

- **KNOWN**: Only English keyword patterns are implemented and tested.
- **NEEDS VALIDATION**: Whether device-native STT/TTS quality is
  acceptable for the target regional languages (Kannada, Telugu, Hindi,
  Tamil, Malayalam, Marathi) - not tested at all this phase (no Flutter
  work happened).

## Internet availability

- **KNOWN**: The assistant requires connectivity (no local model, no
  offline mode) - `/assistant/chat` will simply fail without a network
  connection to the backend, same as every other endpoint in this app.
- **ASSUMED**: A clear "internet required" message would need to be shown
  client-side - not built (no Flutter work this phase).

## AI cost / model availability

- **KNOWN**: Zero cost currently (no LLM configured). See
  docs/AI_COST_CONTROL.md, docs/AI_MODEL_PROVIDER.md.

## Agricultural safety

- **KNOWN**: Verified by test that prescription-style requests are always
  redirected to an expert, never answered directly, and that the output
  validator would catch dosage-pattern language even if it slipped
  through.
- **NEEDS VALIDATION**: Whether the keyword-based prescription detector
  (~6 regex patterns) catches all the ways a farmer might phrase a
  chemical-dosage request in practice - untested beyond the prompt's own
  examples.

## Expert dependency

- **KNOWN**: The assistant never overrides an expert's decision -
  `get_expert_case_status` only reports what `CropHealthCase`/`CaseReview`
  already contain.

## Weather accuracy

- **KNOWN**: Fully inherited from Prompt 7 - the assistant's weather tool
  is a thin pass-through to `weather_service.get_farm_weather`, including
  its own honest unavailable/stale states.

## Market data freshness

- **KNOWN**: The assistant never fabricates a price - `get_seed_products`
  only lists approved products without inventing a price figure in the
  summary text (price detail would require a further tool call not built
  this phase - the current `PRICE_CHECK`/`FIND_SEED` response only
  reports product availability, not a specific number).
- **NEEDS VALIDATION**: Whether farmers would expect a specific price in
  the chat answer itself (requiring a `get_product_prices` tool, not
  built) versus being directed to the product/comparison screen.

## Privacy / data retention

- **KNOWN**: See docs/AI_PRIVACY.md - conversation deletion is a soft
  archive, not a hard delete, this phase.
- **NEEDS VALIDATION**: Legal/business requirements for how long
  assistant conversation history should be retained, and whether a hard
  delete is required for compliance.

## Copyright

- **KNOWN**: `KnowledgeEntry` is empty - no copyrighted content was
  ingested (see docs/AI_KNOWLEDGE_BASE.md).

## Regulatory requirements

- **KNOWN**: No new regulatory surface was introduced - the assistant
  only reads data already governed by each originating phase's own
  regulatory assumptions (Prompt 9's product/dealer regulations, Prompt
  10's buyer/seed regulations) - see those phases' assumptions/risks docs.

## Hallucination

- **KNOWN**: Verified by the prompt's own named test cases (Requirements
  61-64, 98) - see docs/AI_EVALUATION.md. The architecture makes
  hallucination for data-backed intents structurally very unlikely, not
  merely "tested for."

## Prompt injection

- **KNOWN**: Structurally defeated by the deterministic router's lack of
  instruction-following capability - verified by test.

## AI misuse

- **NEEDS VALIDATION**: Whether a farmer could use the assistant's
  question text field for abuse (e.g. extremely long repeated requests)
  beyond what the existing global rate limiter and 1000-character message
  cap already constrain - no assistant-specific abuse testing was done
  this phase.
