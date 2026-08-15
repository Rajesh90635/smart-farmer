# Quality Dispute

## A structured extension of SaleDispute, not a duplicate dispute system

`QualityDispute` is a 1:1 extension of `SaleDispute` (only created when
`reason == quality_disagreement`), holding fields specific to a quality
claim: `agreed_grade` (auto-populated from the sale's own
`quality_grade_snapshot` - never re-typed, so it can't drift from what
was actually agreed), `buyer_claimed_grade`, `farmer_response`,
`evidence_note`, `final_resolution`.

## Never automatically penalizes the farmer (Requirement 36's absolute rule)

`add_quality_dispute_details()` only RECORDS the buyer's claim - it does
not change the sale's status, trigger a refund, or make any judgment.
Resolution requires a separate, explicit admin/human action (mirroring
Prompt 9's dispute-resolution pattern) - there is no code path that
reads `buyer_claimed_grade != agreed_grade` and automatically penalizes
anyone.

## Evidence - text only this phase (disclosed gap)

Same limitation as Prompt 9's `OrderDispute`: `evidence_note` is free
text, no photo upload capability exists for quality disputes yet. Reusing
the crop-photo upload infrastructure (Prompt 5) directly would conflate
two different domains (crop health photos vs. post-sale quality
evidence); a proper extension would use the same `FileStorage`
abstraction via a new, purpose-built upload path - not built yet.

## Farmer response

`farmer_response` exists as a free-text field for the farmer's side of
the disagreement - but **no endpoint currently lets a farmer set it**.
The field exists on the model, ready for that endpoint, but this phase's
`marketplace.py` router only exposes the buyer-side
`add-quality-dispute-details` action. A disclosed, real gap - not
silently treated as symmetric when it isn't yet.

## Expert review - NOT wired to Prompt 8 this phase

Requirement 36 mentions "expert review where required" for a quality
disagreement. No code path in this phase creates a `CropHealthCase` or
routes a `QualityDispute` to a verified agriculture expert - the two
systems (Prompt 8's case management and this phase's quality disputes)
remain structurally separate, with no automatic bridge between them. A
future integration would reuse Prompt 8's existing case-creation and
professional-matching machinery rather than building a parallel review
system - the natural next step, not built yet.
