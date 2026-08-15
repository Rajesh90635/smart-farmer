# Field Agent Workflow

## Controlled outcomes, distinct from expert outcomes

A field agent's review outcome must be one of exactly 5 values
(`FIELD_AGENT_OUTCOMES` in `app/models/case_review.py`) - a DIFFERENT
vocabulary from the expert's, enforced at the service layer (an expert
cannot submit a field-agent outcome and vice versa):

| Outcome | Case status transition |
|---|---|
| healthy_looking | VERIFIED |
| possible_disease | VERIFIED |
| needs_expert | (no automatic escalation-to-expert case creation this phase - disclosed gap, see below) |
| needs_better_photo | NEEDS_MORE_INFORMATION |
| field_visit_required | ESCALATED |

## Field agents are not represented as licensed experts

Nothing in the API response, schema, or farmer-facing text conflates a
field agent's observation with an expert's verification -
`CaseReview.reviewer_role` is always recorded and returned, and
`final_verification_source` on the case explicitly says "field_agent" or
"expert", never blurring the two.

## Known gap: "needs_expert" doesn't auto-create an expert case

When a field agent submits `needs_expert`, the case status doesn't
currently transition to trigger a new expert-routed case automatically -
that would require case-to-case chaining logic not built this phase. For
now, the farmer would need to request a second opinion
(`POST /cases/{id}/second-opinion`) manually, which does route to a
different professional but doesn't specifically prefer an expert over
another field agent. Flagged as a real, disclosed gap - not silently
treated as "handled."

## Offline consideration (Requirement 52)

Field agents may work with poor connectivity. This phase does **not**
build a local-cache-and-sync engine for field-agent case data (explicitly
deferred, matching the spec's "do not build the complete offline sync
engine if a later phase will handle it"). The clean integration point for
a future sync engine is the same `POST /cases/{id}/review` and
`POST /cases/{id}/accept`/`decline` endpoints already built - a future
offline queue would call these exact endpoints once connectivity returns,
using the same idempotency patterns already established elsewhere in this
project (e.g. crop photo upload's `client_upload_id`).
