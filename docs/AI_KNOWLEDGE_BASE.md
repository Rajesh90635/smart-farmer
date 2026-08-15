# AI Knowledge Base (RAG Foundation)

## Honestly empty by default - the same pattern as ReferencePrice/DemandSignal

`KnowledgeEntry` has **zero seed rows**. No RAG retrieval is actually
performed by any intent this phase - `GENERAL_AGRICULTURE` questions
receive the honest "I don't have enough information" response (see
docs/SMART_FARMER_AI.md), never a knowledge-base lookup, because the
knowledge base has nothing in it to look up.

## Why nothing was seeded

Per the explicit "do not ingest copyrighted content without permission"
rule and no vetted, licensed agricultural content source being available
from within this build environment (the same network-access constraint
already documented for Prompt 6's disease-detection model evaluation and
Prompt 9's reference-price sourcing) - inventing plausible-sounding
"official" agricultural facts to fill this table would be exactly the
kind of unsupported claim this project's absolute rules forbid.

## Schema - ready for real content whenever a real source exists

Every `KnowledgeEntry` requires: `source_name` (non-nullable, no default
- there is no such thing as an unattributed entry), `license_status`
(one of `OPEN_LICENSE`/`PUBLIC_DOMAIN`/`OFFICIAL_GOVERNMENT_SOURCE`/
`INTERNAL_APPROVED_SUMMARY`), `version_date`, and `is_approved` (defaults
to `false` - admin approval required before any entry could ever be
surfaced, mirroring the Product/professional verification pattern used
everywhere else in this project). `content_summary` is documented as
"a SHORT factual summary only - never a large copied excerpt."

## What retrieval would look like once populated

No retrieval code exists yet either - there's nothing to retrieve. When
real, licensed content exists, the natural integration point is inside
`GENERAL_AGRICULTURE`'s branch in `response_generator.py`: check
`KnowledgeEntry` for a matching `topic`/`crop_id`/`language_code`
combination before falling back to the "I don't have enough information"
message, and always label the result as coming from that source (never
presented as if the assistant "knows" it independently).

## Expert-approved information — distinguishable, when it exists

`get_expert_case_status` already labels its answer with `source: "Expert
case record (Prompt 8)"`, and the response text explicitly reports the
reviewer's outcome rather than paraphrasing it into different words -
satisfying "do not rewrite expert guidance in a way that changes its
meaning" for the one real expert-information path that exists this phase.
