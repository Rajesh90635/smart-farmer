# Architecture

This file summarizes the architecture as actually built so far. The full
approved architecture (PRD, MVP scope, ERD, event workflow, API contracts,
UI navigation, security model, AI evaluation plan, backlog) was produced
and approved before any code was written — that document is the source of
truth for anything not yet implemented; this file tracks reality.

## Current shape (foundation phase)

```
Flutter app (placeholders) --> FastAPI backend --> PostgreSQL
                                      |
                                      +--> Local filesystem storage
                                      |
                             FastAPI AI service (no model wired in yet)
```

- **Backend** is a modular monolith (per the approved architecture's
  microservices-vs-monolith decision): `app/api`, `app/core`, `app/db`,
  `app/models`, `app/services`, `app/middleware`, `app/repositories`.
  Business modules will live under `app/api/v1/<domain>.py` plus matching
  `services/` and `repositories/` code, following the pattern already
  established by the health/readiness endpoints.
- **AI service** is intentionally separate from the backend process (per
  the approved architecture — different runtime needs: model loading,
  potential GPU use, independent restart/scaling later) but currently has
  no real model — only the `ModelProvider` / `InferenceService` abstraction
  and a health endpoint.
- **Storage** is behind `FileStorage` (backend) — `LocalFileStorage` is the
  only implementation today. Swapping to Azure Blob/S3-compatible storage
  later means writing one new class, not touching any caller.
- **Auth** is JWT-based. A dev-only token issuer exists so protected
  endpoints are testable before the real farmer OTP-login module exists —
  see `app/core/current_user.py` and `app/core/jwt.py`. This is NOT the
  Farmer auth business module.
- **Audit logging** exists from the very first table (`audit_logs`) rather
  than being added later, per the non-negotiable rule that every
  state-changing action is audit-logged from day one.

## Trust boundaries (unchanged from the approved architecture, not yet
exercised by real code since no business module exists yet)

- AI/Automation has read access to context, zero write access to financial
  or order state.
- Diagnosis and commerce recommendation are structurally separate code
  paths — enforced when the disease-diagnosis and marketplace modules are
  built, not yet applicable since neither exists.
- No service can move money past a draft/pending state without an explicit
  farmer-authenticated confirm action — not yet applicable, no money-moving
  code exists yet.

## What's deliberately NOT here yet

Disease detection, weather intelligence, marketplace, dealer/buyer
workflows, harvest prediction (as a market-facing feature), profit
calculation, expert workflow, payments, delivery, scam detection, crop
photo upload/camera. See PROJECT_STATUS.md.

## Farm + Plot + Crop (this update)

Farmer → Farm → Plot → CropCycle → CropMaster is now real, tested code —
see `docs/FARM_MODULE.md`, `docs/PLOT_MODULE.md`, `docs/CROP_MODULE.md`
for full detail. Key architectural points carried forward from the
approved design:
- Ownership is enforced at the repository layer via SQL joins back to
  `farmer_id`, never trusted from the client, and a cross-farmer access
  attempt returns 404 (indistinguishable from "doesn't exist") rather than
  403 — the actual mechanism that defeats ID enumeration.
- `CropCycle` carries unused `ai_suggested_*` columns as a forward-compatible
  hook; no code reads or writes them yet, and a future AI suggestion will
  never auto-write the farmer-official `cultivation_status` field.
- No weather, disease, or marketplace data lives on these tables — those
  remain separate future modules that will reference these ids, not add
  columns here.

## Crop Photo module (this update)

Farmer → Farm → Plot → CropCycle → CropPhotoSession → CropPhoto — see
`docs/CROP_PHOTO_MODULE.md`, `docs/IMAGE_STORAGE.md`,
`docs/IMAGE_VALIDATION.md` for full detail. Reuses the existing
`FileStorage` abstraction and `Settings` config unchanged. The future AI
contract (`app/services/ai_contract.py`) exists as an interface only,
never called from any endpoint this phase.

## AI Disease Detection + Crop Stage (this update)

Real architecture, no real model — see `docs/AI_ARCHITECTURE.md` for the
full explanation and candidate-model evaluation. Every real analysis
request honestly returns `AI_UNAVAILABLE` via `NotConfiguredModelProvider`,
never a fabricated result. The complete safety layer (confidence
thresholds, unsupported-crop/crop-mismatch/low-confidence handling) is
built and tested against a test-only fake provider — see
`docs/AI_SAFETY.md` for exactly where each rule is enforced in code.

## Local Language + Voice + Weather + Alerts (this update)

- **Weather:** real `OpenMeteoProvider` written against Open-Meteo's
  documented API (free, no key), but **not verified against the live API**
  — this sandbox's network allowlist blocks it (confirmed via direct
  `curl`, 403 from the egress proxy). Parsing logic verified against a
  realistic static fixture instead. See `docs/WEATHER_ARCHITECTURE.md`.
- **Weather alerts:** a configurable, tested rule engine (rain, heavy
  rain, high wind, extreme temperature, crop+stage+weather combined,
  spray-condition warnings) — verified to never claim certainty or
  recommend a chemical. See `docs/WEATHER_ALERT_RULES.md`.
- **Notifications:** a unified system with DB-enforced deduplication,
  per-category preferences, and quiet hours. See
  `docs/NOTIFICATION_ARCHITECTURE.md`.
- **Voice/TTS:** device-native (`flutter_tts`), not a backend service —
  evaluated and chosen for zero cost/infra and offline capability. See
  `docs/VOICE_AUDIO.md`.
- **AI-to-language bridge:** every AI result is rendered into structured,
  farmer-friendly, localized text via `ai_result_localization_service.py`
  — never raw AI output. See `docs/AI_ARCHITECTURE.md`. See PROJECT_STATUS.md.

## Professional Network + Case Management (this update)

New actors (FIELD_AGENT, EXPERT, TRADER, DEALER professional profiles)
and a new domain object (CropHealthCase) sit alongside the existing
Farmer/Farm/Crop/Photo/AI chain, connecting to it via foreign keys
(crop_cycle_id, crop_photo_id, ai_analysis_id) rather than duplicating any
of it. Key architectural points:
- Verification is admin-only and append-only (VerificationRecord) - no
  professional can self-verify, enforced by role-gating every
  verification endpoint to ADMIN.
- Matching (`nearby_professional_service.py`) only ever considers
  VERIFIED professionals - a hard filter at the query level.
- Photo sharing reuses the EXISTING crop-photo-serving endpoint, broadened
  to check a new PhotoAccessGrant authorization path alongside farmer
  ownership - not a new parallel endpoint.
- Case audit reuses the EXISTING generic AuditLog table - no new audit
  table.
- Case notifications reuse the EXISTING NotificationService from the
  Weather phase - no new notification infrastructure.
- AI results and human (expert/field-agent) results are structurally
  separate and both retained - CaseReview is additive, AIAnalysis is
  never modified by any case-service code.

## Marketplace: Product Catalog + Orders (this update)

Reuses Prompt 8's `ProfessionalProfile` verification entirely for
dealers/traders - no second verification system. Cart is modeled as a
`DRAFT`-status `Order` (no separate Cart/CartItem tables), and
`OrderItem`'s price fields double as the frozen price snapshot (no
separate PriceSnapshot table) - both deliberate consolidations disclosed
in docs/ORDER_WORKFLOW.md. A single shared `order_transitions.py` module
is the sole source of truth for order status transitions, used
identically by the farmer-facing, dealer-facing, and payment services -
found and fixed a real duplication risk before it could cause drift
between three near-identical copies of the same validation logic.

Server-side price authority is structural: `CheckoutRequest` has no price
field in its schema at all, so there is nothing for a malicious client to
even attempt to override.

## Harvest Marketplace (this update)

Buyer verification reuses `ProfessionalProfile` exactly like dealers
(Prompt 9) - no third verification system. `SaleOrder` genuinely reuses
Prompt 9's `Payment`/`Delivery` tables via a new `sale_order_id` column
(alongside the pre-existing `order_id`, both now nullable) rather than
creating parallel tables - "exactly one FK set" is maintained by
service-layer construction. Offer acceptance uses a real database row
lock (`SELECT ... FOR UPDATE`) to guarantee no harvest listing can be
oversold under concurrent acceptance - verified with an actual
multi-threaded test, not just reasoned about. Seeds are `Product` rows
with `category=SEED`, reusing 100% of Prompt 9's catalog/pricing/
checkout machinery.

## Smart Farmer AI Assistant (this update)

A deterministic, tool-based intent router - not a generic LLM chatbot.
Every data-backed answer is produced by calling a real, farmer-scoped,
read-only tool that reuses an existing repository/service from Prompts
4-10, then composing the answer from the same template system Prompt 7
built for weather/notification text. No entity id is ever parsed from a
farmer's free-text message - every tool resolves "the calling farmer's
own most-relevant record" purely from the authenticated session, which
is what makes cross-farmer data leakage and prompt injection structurally
defeated rather than merely filtered. The one slot reserved for a real
generative model (open-ended `GENERAL_AGRICULTURE` questions) honestly
reports unavailable in this environment, since no LLM API key is
configured - verified by a live request, not assumed.
