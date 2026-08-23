# Smart Farmer AI Platform

A farmer operating system that automatically observes, predicts, explains,
and coordinates the farm lifecycle — while keeping financial, safety, and
irreversible decisions under farmer control.

**Status:** Development foundation only. No business features (disease
diagnosis, weather, marketplace, payments, expert workflows) are
implemented yet. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for exactly
what exists and what's next.

## Stack (all free / open-source)

| Layer | Technology |
|---|---|
| Mobile | Flutter |
| Backend API | Python + FastAPI |
| AI service | Python + FastAPI (model-abstraction only for now) |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Local storage | Filesystem, behind a swappable interface |
| Containerization | Docker / Docker Compose |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full picture and
[docs/LICENSE_REGISTER.md](docs/LICENSE_REGISTER.md) for every dependency's
license.

## Repository layout

```
smart-farmer/
├── mobile/            Flutter app (navigation placeholders only so far)
├── backend/            FastAPI backend (auth + farmer profile + farm/plot/crop
│   │                   + crop photo + AI disease detection + weather/notifications
│   │                   architecture implemented)
│   ├── app/
│   │   ├── api/v1/     auth, farmers, farms, plots, crops, crop_photos, ai,
│   │   │               weather, notifications implemented; market/experts
│   │   │               still empty placeholders
│   │   ├── core/       Config, logging, JWT, roles, password hashing,
│   │   │               localization whitelist, error codes, area units,
│   │   │               image validation/quality/processing, photo storage keys,
│   │   │               AI + weather provider dependency injection,
│   │   │               farmer_messages (structured localized templates)
│   │   ├── db/         SQLAlchemy engine/session
│   │   ├── models/     User, FarmerProfile, Role, UserRole, RefreshToken,
│   │   │               ConsentRecord, AuditLog, Farm, Plot, CropMaster,
│   │   │               CropCycle, CropPhotoSession, CropPhoto, DiseaseClass,
│   │   │               CropStageDefinition, AIModelRegistry, AIAnalysisSession,
│   │   │               AIAnalysis, AICropStageResult, WeatherSnapshot,
│   │   │               Notification, NotificationPreference
│   │   ├── repositories/ Data-access layer, ownership-aware
│   │   ├── services/   auth, farmer, consent, farm, plot, crop_cycle,
│   │   │               dashboard, crop_photo, ai_analysis, ai_analysis_session,
│   │   │               ai_result_localization, weather_service, weather_alert_rules,
│   │   │               weather_alert_orchestration, notification_service,
│   │   │               notification_query, ai/ (model abstraction),
│   │   │               weather/ (provider abstraction), audit_logger
│   │   ├── schemas/    Pydantic request/response models with validation
│   │   ├── middleware/ Request logging, unified error handling, rate limiting
│   ├── alembic/        10 migrations
│   └── tests/          Pytest suite (315 tests, all passing)
├── ai/                 AI/ML service (health + model abstraction only)
│   ├── app/
│   └── tests/          Pytest suite (4 tests, all passing)
├── database/seed/      Reserved for seed data scripts (none yet)
├── admin/              Reserved — admin portal approach not yet decided
├── infrastructure/     Reserved for future infra config
├── docs/               Architecture, setup, security, and other docs
├── scripts/            Local dev helper scripts
├── docker-compose.yml  One-command local environment
└── .env.example        Documented environment variables (no real secrets)
```

## Quickstart

See [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) for full,
exact, Windows-first instructions. Short version:

```powershell
git clone <your-repo-url>
cd smart-farmer
copy .env.example .env      # then edit .env with real local values
docker compose up --build
```

Then:
- Backend: http://localhost:8000/api/v1/health and /docs
- AI service: http://localhost:8100/ai/health
- pgAdmin: http://localhost:5050

## Contributing rules (see docs/ for full detail)

- No secrets in code — ever.
- Every schema change is an Alembic migration.
- Every module needs tests before it's considered done.
- AI and Automation never get independent financial authority.
- No third-party code, UI, content, or datasets copied — see
  [docs/LICENSE_REGISTER.md](docs/LICENSE_REGISTER.md).

## Professional Network + Case Management (this update)

Field agents, agriculture experts, verified traders/dealers, case
routing, expert/field-agent review, AI-vs-human disagreement tracking,
and authorized photo sharing — see `docs/PROFESSIONAL_NETWORK.md`,
`docs/CASE_MANAGEMENT.md`, `docs/CASE_ROUTING.md`,
`docs/EXPERT_VERIFICATION.md`, `docs/FIELD_AGENT_WORKFLOW.md`,
`docs/DEALER_VERIFICATION.md`, `docs/PHOTO_SHARING_PRIVACY.md`,
`docs/CASE_AUDIT.md`. New endpoints: `/api/v1/professionals/*`,
`/api/v1/cases/*`. Reuses the existing generic `AuditLog` for case audit
(no new table) and Prompt 7's notification system (no new notification
infrastructure). No medicine, marketplace, or payment functionality —
still explicitly out of scope.

## Marketplace: Product Catalog + Price Transparency + Scam Shield + Orders (this update)

Controlled admin-approved product catalog, verified-dealer-only listings
(reusing Prompt 8's professional verification, not a new system),
sourced/never-fabricated reference prices, cross-pack-size price
normalization, a price-anomaly-based Scam Shield (neutral language only,
verified by test), a cart-as-draft-order checkout with **server-side-only
price calculation** (verified by test that a stale client-side price is
never trusted), the full 16-status order state machine, sandbox-only
payment, simple delivery tracking, and dispute/refund foundations. See
`docs/PRODUCT_CATALOG.md`, `docs/DEALER_WORKFLOW.md`,
`docs/PRICE_TRANSPARENCY.md`, `docs/SCAM_SHIELD.md`,
`docs/ORDER_WORKFLOW.md`, `docs/PAYMENT_ARCHITECTURE.md`,
`docs/DELIVERY_WORKFLOW.md`, `docs/REFUND_DISPUTE.md`,
`docs/PRODUCT_SAFETY.md`, `docs/PRICE_DATA_SOURCES.md`, and
`docs/PROMPT9_ASSUMPTIONS_RISKS.md`. No medicine/pesticide dosage
prescription anywhere in this codebase — verified explicitly by test.

## Harvest Selling + Direct Buyers + Seeds Marketplace (this update)

Farmer harvest management (farmer-confirmed readiness only, never
AI-automatic), "Sell My Harvest" listings (location-approximate by
construction), verified direct buyers (fully reusing Prompt 8's
professional verification — no second system), append-only offer/
counter-offer negotiation, and sale orders that **genuinely reuse**
Prompt 9's Payment/Delivery tables rather than duplicating them. Seeds
are just `Product` rows with `category=SEED`, reusing the entire Prompt 9
catalog/pricing/Scam Shield/checkout system unchanged. See
`docs/HARVEST_MANAGEMENT.md`, `docs/FARMER_MARKETPLACE.md`,
`docs/BUYER_WORKFLOW.md`, `docs/OFFER_NEGOTIATION.md`,
`docs/SALE_WORKFLOW.md`, `docs/SEED_MARKETPLACE.md`,
`docs/MARKETPLACE_TRUST.md`, `docs/LOCATION_PRIVACY.md`,
`docs/MARKETPLACE_SCAM_SHIELD.md`, `docs/PAYMENT_AND_SETTLEMENT.md`,
`docs/QUALITY_DISPUTE.md`, and `docs/PROMPT10_ASSUMPTIONS_RISKS.md`.

**The mandatory concurrency requirement is verified for real**: two
simultaneous offer acceptances against the same harvest listing,
attempted from separate threads, are correctly serialized by a real
PostgreSQL row lock (`SELECT ... FOR UPDATE`) — exactly one succeeds,
the other correctly fails, never both. Verified 5 times consecutively
during development to rule out a lucky race rather than a real guarantee.

## Smart Farmer AI Assistant (this update)

A farm-specific intelligent assistant — NOT a generic chatbot. A
deterministic intent router (no LLM, cannot hallucinate or be
prompt-injected by construction) maps a farmer's question to one of 15
implemented intents, calls a real authorized read-only tool reusing every
existing service from Prompts 4–10, and composes a farmer-friendly
templated answer. Verified against every example question in the prompt
itself, plus the prompt's own named hallucination/safety test cases
(yield question with no data, price question with no data, order status
must come from the real service, pesticide questions always redirect to
an expert). No LLM API key is configured in this environment — verified
directly (not assumed) by a live request to `api.anthropic.com`
confirming no credential is available — so the one free-form-reasoning
slot (`GENERAL_AGRICULTURE`) honestly reports it can't answer rather than
fabricating a response. See `docs/SMART_FARMER_AI.md`,
`docs/AI_ARCHITECTURE.md`, `docs/AI_TOOL_SYSTEM.md`,
`docs/AI_GUARDRAILS.md`, `docs/AI_PRIVACY.md`, `docs/AI_EVALUATION.md`,
`docs/AI_KNOWLEDGE_BASE.md`, `docs/AI_MODEL_PROVIDER.md`,
`docs/VOICE_ASSISTANT.md`, `docs/FARMER_AI_UX.md`,
`docs/AI_COST_CONTROL.md`, and `docs/PROMPT11_ASSUMPTIONS_RISKS.md`.
