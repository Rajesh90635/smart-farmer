# Prompt 10 — Assumptions and Risks

Every item is classified **KNOWN** (verified true in this codebase),
**ASSUMED** (believed true but not verified from within this
environment), or **NEEDS VALIDATION** (a real unresolved question).

## Crop grading differences

- **KNOWN**: `quality_grade` is free text on both `HarvestListing` and
  the frozen `SaleOrder.quality_grade_snapshot` - no rigid Grade A/B/C
  enum is imposed.
- **ASSUMED**: That farmer/buyer agreement on grading terminology
  (without a formal shared vocabulary) is workable for an MVP.
- **NEEDS VALIDATION**: Whether crop-specific formal grading standards
  (which genuinely differ - e.g. tomato grading vs. rice grading use
  different criteria) need to be modeled as structured master data before
  this is trustworthy at scale.

## Local market pricing

- **KNOWN**: No reference-price data source exists for harvest crops in
  this phase (unlike Prompt 9's agricultural inputs, which have
  `ReferencePrice`) - a farmer/buyer negotiate with zero price-anomaly
  guidance.
- **NEEDS VALIDATION**: Whether extending `ReferencePrice` (or a similar
  mechanism) to cover crop selling prices by region/season is feasible
  with real, documented data sources - see docs/PRICE_DATA_SOURCES.md
  (Prompt 9) for the same open question already flagged for inputs.

## Buyer reliability / farmer-buyer disputes

- **KNOWN**: `SaleFeedback` and `SaleDispute` exist as raw signal tables;
  no aggregated trust score is computed (see docs/MARKETPLACE_TRUST.md).
- **NEEDS VALIDATION**: What dispute/cancellation rate should actually
  disqualify a buyer from "trusted" status, and whether that should be an
  automatic threshold or always an admin judgment call (Requirement 55
  explicitly says "do not automatically permanently ban based on a single
  anomaly" - a rate-based automatic threshold would need careful design).

## Transportation costs

- **KNOWN**: `SaleOrder.charges` is always `0` - no transportation-cost
  model exists.
- **NEEDS VALIDATION**: Whether transportation cost should be a flat fee,
  distance-based, or buyer/farmer-negotiated as part of `collection_terms`
  free text (current de facto behavior, since it's unstructured).

## Harvest quantity uncertainty

- **KNOWN**: `HarvestRecord` distinguishes `estimated_quantity` from
  `actual_quantity` - the farmer can list based on an estimate before
  actual harvest.
- **ASSUMED**: That farmers will reasonably estimate quantity and that
  minor discrepancies are handled via the existing quantity-disagreement
  dispute reason (`WRONG_QUANTITY`), not a formal tolerance-band system.

## Weather

- **KNOWN**: Not integrated into harvest timing or listing this phase
  (see docs/HARVEST_MANAGEMENT.md's disclosed gap).
- **NEEDS VALIDATION**: How much weather should influence harvest-timing
  *suggestions* (never automatic decisions, per Requirement 43) once
  built.

## Payment settlement

- **KNOWN**: Sandbox only, same as Prompt 9. No real payout/disbursement
  mechanism to farmer bank accounts/UPI exists (see
  docs/PAYMENT_AND_SETTLEMENT.md).
- **NEEDS VALIDATION**: Real gateway selection and farmer payout
  compliance requirements - identical open question to Prompt 9's, not
  re-litigated differently here.

## Buyer verification

- **KNOWN**: Identical process to dealer/expert verification (Prompt 8) -
  admin-only, manual.
- **NEEDS VALIDATION**: What documentation should actually be required to
  verify a business buyer (GST registration, trade license, etc.) - not
  modeled or checked by this codebase.

## Agricultural product regulations / seed regulations

- **KNOWN**: Seeds reuse the exact same `Product` approval gate as any
  other regulated input (Prompt 9's assumptions apply unchanged - see
  docs/PROMPT9_ASSUMPTIONS_RISKS.md for the full regulatory-assumption
  discussion, which is not repeated here since nothing about seed
  regulation differs from general product regulation in this codebase).

## Marketplace fraud

- **KNOWN**: The primary protection for harvest selling is the hard
  buyer-verification gate - no price-anomaly-style Scam Shield exists for
  crop offers (see docs/MARKETPLACE_SCAM_SHIELD.md).
- **NEEDS VALIDATION**: Whether verification alone is sufficient
  protection at real scale, or whether a documented reference-price
  system (like Prompt 9's) is needed for genuine anti-scam value on the
  selling side too.

## Internet connectivity / language support

- **ASSUMED**: Carried over from every prior phase's same assumptions.
  This phase adds the same offline-viewing-only-with-online-confirmation
  requirement (Requirement 75) as a design principle, but no explicit
  offline-caching code was written this phase to test against - this is
  primarily a Flutter-side concern, and no Flutter work happened this
  phase.

## Location privacy

- **KNOWN**: Approximate-only listing data verified by test; exact
  collection-location sharing is a disclosed, unbuilt gap (see
  docs/LOCATION_PRIVACY.md).
- **NEEDS VALIDATION**: The actual UX/timing for when "sufficiently
  confirmed" a sale needs to be before exact location is shared - a
  product/business decision, not a technical one.
