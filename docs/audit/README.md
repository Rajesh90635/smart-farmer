# Smart Farmer V3 — Real-World Scenario Audit (2026-09-04)

Full audit of the 100-domain, 300+-scenario checklist supplied by the user
against the actual repository, run as 13 parallel research passes (one per
cluster of related domains). Every finding below is grounded in file:line
citations and, where applicable, actual test runs — not inferred from
feature names or documentation alone.

## Methodology

Each of the 9 status values is mutually exclusive and was applied per
individual scenario, not per domain:

- **MISSING** — no code implements this at all.
- **PARTIAL** — some code exists but doesn't cover the full scenario.
- **BROKEN** — code exists but is demonstrably incorrect/non-functional.
- **IMPLEMENTED** — code fully covers the scenario, but no automated test
  specifically asserts it.
- **VERIFIED** — code fully covers the scenario AND a passing automated
  test (or a live session verification) specifically asserts it.
- **COMPLETE** — reserved but unused as a distinct bucket (auditors were
  instructed to use VERIFIED instead, to avoid double-counting); always 0.
- **FUTURE** — explicitly, deliberately deferred, with a citation to where
  the project already documented that decision.
- **OUT_OF_SCOPE** — requires a real external business/legal/regulated
  relationship this project structurally never fabricates (a real payment
  gateway, insurance underwriting, eNAM registration, a government scheme
  portal, satellite/IoT hardware). Only an interface/boundary may exist.
- **ENVIRONMENT_DEPENDENT** — code is correct/complete, but real-world
  behavior in this specific dev environment depends on something this
  session/machine lacks (e.g. no non-English TTS voice installed, no
  Android device/emulator).

Totals below were computed **mechanically** (a script parsing every table
row's Status cell across all 13 files), not hand-tallied from each
sub-agent's own prose summary, to avoid transcription drift at this scale.
`c01_foundation.md` was re-parsed a second time after its authoring agent
reported a late race condition (its own spawned helper had briefly
overwritten the file); the numbers below reflect that final, verified
version.

## Final reconciled totals

| Status | Count |
|---|---|
| VERIFIED | 223 |
| IMPLEMENTED | 63 |
| COMPLETE | 0 |
| PARTIAL | 119 |
| MISSING | 321 |
| BROKEN | 12 |
| FUTURE | 29 |
| OUT_OF_SCOPE | 25 |
| ENVIRONMENT_DEPENDENT | 6 |
| **TOTAL** | **798** |

(223+63+0+119+321+12+29+25+6 = 798, verified by script — reconciles exactly.)

**Why 798, not "300+":** the supplied checklist's 100 domains expand to
this many individual scenarios once every bullet is treated as its own
row, per the instructions. This is consistent with, not a deviation from,
"300+" as a floor.

## Automation coverage (BV-2) — honestly not computed this pass

The requested `Automatic / Manual / Hybrid / Safety-confirmation workflow`
breakdown and automation-coverage percentage could **not** be reliably
computed by mechanical parsing: the 13 sub-agents used slightly different
column layouts (embedded citations pushed some rows to 16–22 columns
instead of the specified 17), so positionally extracting the Trigger /
Automatic Action columns across all 798 rows was not trustworthy. Rather
than publish a fabricated percentage, this is flagged as a distinct
follow-up pass (a second mechanical script keyed to each file's own
header, or a targeted per-domain re-read) — not silently dropped.

## The 7 distinct real bugs found (BROKEN, not just missing)

These are genuine defects — existing, tested-looking code that is
demonstrably wrong — found across 5 separate areas. Full citations are in
the linked files; short list:

1. **Password reset has no identity verification** beyond a phone number
   (`c01_foundation.md` D1-18) — already self-documented in
   `docs/SECURITY.md:203-205` as a known account-takeover gap.
2. **`harvest_service.confirm_ready()` has no status guard** (`c08` D49-05/
   D50-07) — re-calling it to correct a quantity silently regresses an
   already-`LISTED`/`HARVESTED` record back to `READY`.
3. **"Net realization" is fake** (`c09` D57-07/D58-06) — `offer_service.py`
   hardcodes transport/commission/storage charges to `Decimal("0")`, so the
   figure presented as a real net-of-costs number can never differ from
   the gross sale value.
4. **Offer expiry is dead code** (`c09` D59-06) — `BuyerOffer.valid_until`
   and `OfferStatus.EXPIRED` exist but nothing ever checks them; a farmer
   can accept an offer after it's supposed to have expired.
5. **Payment retry is blocked** (`c10` D66-02) — the status transition map
   only allows `PAYMENT_PENDING → {PAID, CANCELLED}`, so a second `/pay`
   call after a failure gets rejected with a 409, with no path to retry.
6. **Inconsistent auth-expiry handling during photo upload** (`c12` D84-02)
   — the foreground upload path never checks for a 401, unlike the
   background sync path, so it misclassifies an expired session as a
   plain retryable network failure.
7. **Dead-letter sync items can never be revived** (`c12` D84-04/D87-04/
   D87-05/D87-06) — a code comment promises a "manual retry UI path" that
   doesn't exist anywhere; once an item hits `authenticationRequired` or
   `retriesExhausted`, it is permanently stuck with zero farmer or admin
   visibility.

**Post-audit status (2026-09-05):** all 7 are now fixed and tested; the
table rows above are left as originally written (this is a point-in-time
snapshot, not re-parsed) rather than hand-edited out of the mechanically-
verified totals. Bug 1 specifically required a real product decision this
audit deliberately did not make unilaterally (see "What happens next"
below) — it's closed via a real Twilio Verify OTP check gating
`/auth/reset-password` (see `docs/SECURITY.md`'s "Password reset" section
and `app/services/sms/`), on explicit instruction to wire up a real SMS
provider rather than a free/no-OTP alternative.

All 7 are safely fixable now — none require a new external
provider/business decision. **Next: implementing these fixes with tests.**

## Cross-cutting architectural findings (not single bugs, but systemic)

- **No scheduler/cron/background worker exists anywhere in this project**
  (confirmed independently by the weather and expert-network audits) —
  this is *why* weather alerts are pull-only and Expert SLA timeouts/
  reminders never fire, not two separate gaps.
- **`notification_service` is never invoked from marketplace, sale,
  order, or payment code** — confirmed by grep. Only expert-case and
  weather flows notify farmers today.
- **Offline/sync is 100% scoped to crop-photo uploads** — Farms, Plots,
  Crops, Tasks, Expenses, Harvest records, and Notes have zero offline
  queueing capability.
- **Everything financial is scoped to a single crop cycle** — no Plot/
  Farm/Season-level profit rollup or cost-per-acre exists, despite
  `Plot.area_value` being available to join against.
- The strongest, most rigorously tested areas in the whole app are:
  the crop-cycle/harvest/sale/order state machines, the Ledger + Invoice
  OCR + Cost Estimate + Profit Forecast system (Phases 29-32), the AI
  disease-detection pipeline's architecture (real provider abstraction,
  tested against a fake provider), and Security/RBAC/tenant isolation.
- Entirely and honestly absent, confirmed by exhaustive grep, not
  assumption: Government Schemes, Crop Insurance, Satellite, IoT, real
  Machinery/Labour marketplaces, Community/discussion features, Storage/
  Cold-Storage logistics, and a real crop-selling market-price feed.

## Cluster files (full 798-row detail, evidence-cited)

| File | Domains |
|---|---|
| [c01_foundation.md](c01_foundation.md) | 1-8: Account, Farm, Plot, Crop, Variety, Cycle, Stages, Calendar |
| [c02_lifecycle_edgecases.md](c02_lifecycle_edgecases.md) | 9-13, 99: Task Automation, Crop Failure, Re-sowing, Intercropping, Perennial, Special Scenarios |
| [c03_weather_water_soil.md](c03_weather_water_soil.md) | 14-20: Weather, Weather Risk, Weather Automation, Water, Irrigation, Soil, Soil Testing |
| [c04_inputs.md](c04_inputs.md) | 21-26: Seeds, Fertilizer, Crop Protection, Input Inventory, Purchase, Verification |
| [c05_disease_ai.md](c05_disease_ai.md) | 27-32: Disease, Pest, AI Diagnosis, Image Quality, AI Confidence, Unknown Diagnosis |
| [c06_expert_network.md](c06_expert_network.md) | 33-39: Expert Escalation, Assignment, SLA, Recommendation, Recommendation→Task, Follow-up, Reinspection |
| [c07_voice_language_community.md](c07_voice_language_community.md) | 40-46: Voice, Local Language, Education, Community, Nearby Services, Machinery, Labour |
| [c08_harvest_postharvest.md](c08_harvest_postharvest.md) | 47-55: Harvest Readiness, Planning, Quantity, Yield, Quality, Post-Harvest, Storage, Cold Storage, Transport |
| [c09_market_sales.md](c09_market_sales.md) | 56-63: Market Prices, Comparison, Net Realization, Buyer Matching, eNAM, FPO, Sales, Orders |
| [c10_payments_finance.md](c10_payments_finance.md) | 64-72: Payments, Partial/Failed Payments, Disputes, Refund Boundary, Expenses, Revenue, Profit, ROI |
| [c11_schemes_insurance_disaster_satellite_iot.md](c11_schemes_insurance_disaster_satellite_iot.md) | 73-77: Gov Schemes, Crop Insurance, Disaster Management, Satellite, IoT |
| [c12_notifications_offline_sync.md](c12_notifications_offline_sync.md) | 78-87: Notifications, Dedup, Priority, Offline, Sync, Retry, Auth Expiry, Conflict Resolution, Idempotency, Dead-letter |
| [c13_governance_farmbrain_security.md](c13_governance_farmbrain_security.md) | 88-98, 100: Data Provenance, Rule Versioning, Provider Abstraction, AI Governance, Farm Brain, Daily Brief, What Changed, Risk Dashboard, Season Comparison/Closure, Historical Learning, Security/Privacy/Audit |

## What happens next

Per the requested process (AUDIT → GAP MATRIX → IMPLEMENT → TEST →
RE-AUDIT), the 7 bugs above are being fixed now — they're safe, scoped,
and need no new product/business decision. The 318 MISSING and 123
PARTIAL scenarios are not being bulk-implemented blindly: many require
real decisions only the product owner can make (which payment provider,
whether to pursue insurance/eNAM/satellite integration, whether to build
a Machinery/Labour marketplace, etc.) — those will be brought back as a
prioritized list for explicit sign-off rather than built speculatively.
