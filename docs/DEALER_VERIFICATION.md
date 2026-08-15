# Dealer/Trader Verification (Foundation Only)

## Scope this phase

Only the verification FOUNDATION for `trader` and `dealer` roles is built
- registration (`POST /professionals` with `role=trader` or `role=dealer`)
and the same admin verify/reject/suspend/reactivate actions used for
field agents/experts. **No product, inventory, order, or medicine
workflow exists** - that's explicitly Prompt 9's scope.

## Data captured

Same `ProfessionalProfile` table as field agents/experts (reused, not a
separate table) - `organization`, `service_area` (approximate, never an
exact private address), `verification_status`. No product-category or
inventory fields were added this phase, since "do not implement product
ordering yet" per the spec.

## Why this matters for Prompt 9

Prompt 9 (medicine/marketplace) can build directly on
`verification_status = VERIFIED` for traders/dealers rather than
re-inventing a verification concept - the exact intent of building this
foundation now.

## What a trader/dealer CANNOT do this phase

- Cannot receive a `CaseAssignment` (case_service.create_case only routes
  to `field_agent`/`expert`).
- Cannot receive a `PhotoAccessGrant` (no code path creates one for a
  trader/dealer).
- Cannot see any farmer's crop-disease case or photo.

This is enforced structurally (no code path exists), not by a
permission check that could have a bug - there is simply nothing in this
phase that would ever route a case or grant photo access to these roles.
