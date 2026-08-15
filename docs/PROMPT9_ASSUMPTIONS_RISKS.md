# Prompt 9 — Assumptions and Risks

Every item below is classified as **KNOWN** (verified true in this
codebase), **ASSUMED** (believed true but not verified from within this
environment), or **NEEDS VALIDATION** (a real unresolved question that
must be answered before real farmers/dealers/money are involved).

## Agricultural product regulatory requirements

- **KNOWN**: This codebase enforces an admin-approval gate before any
  product can be sold (`ProductStatus.APPROVED` required), and product
  categories are distinguished (seed/fertilizer/pest-control/etc.) rather
  than everything being called "medicine."
- **ASSUMED**: That admin approval alone is a sufficient regulatory
  control. In reality, agricultural inputs (especially
  `PEST_CONTROL_PRODUCT`/`CROP_PROTECTION_PRODUCT`) are typically
  regulated under specific national/state legislation (e.g., in India,
  the Insecticides Act) requiring dealer licensing and product
  registration that this platform does not verify against any external
  registry.
- **NEEDS VALIDATION**: Whether operating this marketplace for regulated
  agricultural inputs requires the platform operator itself to hold a
  license, and whether `DealerBusinessProfile.license_number` needs to be
  cross-checked against a real regulatory database (not built - it's
  free text this phase).

## Dealer licensing assumptions

- **KNOWN**: `license_number` is captured as a free-text field and never
  publicly exposed (only visible to the dealer themselves and admin,
  since it's not included in any farmer-facing response schema).
- **ASSUMED**: That the specific documentation an admin should require
  before verifying a dealer (business registration, GST, pesticide
  dealer license, etc.) is a business/legal decision outside this
  codebase's scope - no such checklist exists in the code.
- **NEEDS VALIDATION**: What documents are legally required per state,
  and whether a manual admin review process (the only one built) is
  sufficient or whether integration with a government licensing database
  is required.

## Product approval assumptions

- **KNOWN**: A product cannot be sold until an admin explicitly approves
  it; approval status can be revoked (`SUSPENDED`/`RECALLED`) and this is
  enforced at checkout time (re-verified, not just at listing time).
- **ASSUMED**: That the admin performing approval has the domain
  expertise to correctly evaluate a product's safety/legality - the
  platform provides no decision-support tooling for this judgment.
- **NEEDS VALIDATION**: What qualifications an "admin" approving
  agricultural products should actually have.

## Market-price data availability / price-source reliability

- **KNOWN**: No live external price feed exists; all reference prices
  this phase are `ADMIN_ENTERED_REFERENCE` (see docs/PRICE_DATA_SOURCES.md).
- **ASSUMED**: That admin-entered reference prices, kept reasonably
  current by manual admin diligence, are an acceptable interim
  substitute for a live feed.
- **NEEDS VALIDATION**: How frequently reference prices would realistically
  be updated in practice, and whether that cadence is fast enough to be
  useful for genuine price-anomaly detection (a reference price that's
  months stale could produce misleading anomaly flags in either direction).

## Payment gateway requirements

- **KNOWN**: Only a sandbox payment flow exists; no real gateway is
  integrated (see docs/PAYMENT_ARCHITECTURE.md).
- **NEEDS VALIDATION**: Gateway selection, KYC/business registration
  requirements, and compliance (PCI-DSS scope, if any) - none evaluated
  in this codebase.

## Delivery partner requirements

- **KNOWN**: No delivery-partner entity exists; the dealer self-reports
  delivery status.
- **NEEDS VALIDATION**: Whether a real deployment needs a genuine
  logistics partner integration, and what that partner's
  verification/liability requirements would be.

## Product authenticity limitations

- **KNOWN**: `DealerProduct` captures `batch_number`/dates as
  dealer-entered fields, not independently verified. `Product` has no
  QR/barcode verification capability.
- **ASSUMED**: That batch/expiry data entered by a verified dealer is
  accurate - there is no cross-check against a manufacturer database.
- **NEEDS VALIDATION**: Whether manufacturer-side verification
  (Requirement 46) is available/necessary for the product categories this
  platform will actually carry.

## Weather impact on delivery

- **KNOWN**: `Delivery.weather_delay_note` exists as a column but nothing
  populates it yet (see docs/DELIVERY_WORKFLOW.md).
- **ASSUMED**: That when built, a simple informational note (not an
  automatic cancellation) is the right behavior - matches Requirement 51
  explicitly.

## Farmer digital literacy / connectivity / regional language

- **ASSUMED**: Carried over from every prior phase's same assumptions
  (Prompts 5-8) - this phase adds no new assumption here beyond what
  already exists for photo upload, AI results, and notifications.
- **NEEDS VALIDATION**: Whether the checkout flow specifically (multi-step:
  cart -> checkout -> pay -> confirm) is usable for a low-literacy farmer
  on a low-end device with intermittent connectivity - not tested with
  real users in this environment.

## Data privacy

- **KNOWN**: No payment secrets are ever stored (structurally impossible
  - no such columns exist). Dealer license numbers are never exposed to
  farmers.
- **NEEDS VALIDATION**: Full data-retention and deletion policy for order/
  payment/dispute records - not defined this phase (same gap as every
  prior phase's audit data).

## Fraud detection limitations

- **KNOWN**: Scam Shield this phase only checks price anomalies against a
  (possibly stale, possibly sparse) reference price. It does not detect
  duplicate listings, coordinated fake reviews, or sophisticated seller
  fraud patterns.
- **NEEDS VALIDATION**: Whether the current single-factor price check
  provides meaningful farmer protection at real-world scale, or whether
  more sophisticated fraud signals (documented as future work in
  docs/SCAM_SHIELD.md) are needed before this feature can be marketed as
  genuinely protective.
