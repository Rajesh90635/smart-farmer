# API Conventions

## Versioning
All routes are mounted under `/api/v1`. A breaking change gets a new
`/api/v2` prefix rather than mutating v1's contract — existing mobile app
versions in the field must keep working against the v1 surface they were
built against.

## Route organization
One router module per domain under `app/api/v1/` (`auth.py`, `farmers.py`,
`farms.py`, `crops.py`, `ai.py`, `weather.py`, `market.py`, `experts.py`),
aggregated in `app/api/v1/router.py`. A domain's business logic lives in a
matching `app/services/<domain>.py`; routes stay thin (validate input, call
a service, shape the response).

## Error shape
Every error response (see `app/middleware/error_handling.py`) is:
```json
{
  "error": {
    "code": "STABLE_MACHINE_READABLE_CODE",
    "message": "Human-readable summary, safe to show a farmer or log.",
    "correlation_id": "uuid-also-present-in-server-logs",
    "details": "optional, e.g. field-level validation errors"
  }
}
```
Internal exception messages/stack traces are never included — only the
`correlation_id`, which is also attached as the `X-Correlation-Id` response
header on every request (success or failure) and logged server-side.

Stable codes (see `app/core/error_codes.py`) currently in use:
`INVALID_CREDENTIALS`, `ACCOUNT_DISABLED`, `VALIDATION_ERROR`,
`UNAUTHORIZED`, `FORBIDDEN`, `SESSION_EXPIRED`, `INVALID_TOKEN`,
`DUPLICATE_ACCOUNT`, `NOT_FOUND`, `RATE_LIMITED`,
`INCORRECT_CURRENT_PASSWORD`, `INVALID_OTP`, `OTP_DELIVERY_FAILED`. The
Flutter client maps each to a farmer-friendly message
(`mobile/lib/core/friendly_error.dart`) — never shows the raw `message`
field directly.

## Authentication
`Authorization: Bearer <jwt>` on every route except `/api/v1/health` and
`/api/v1/ready`. A missing/invalid/expired token returns `401`. An
authenticated-but-wrong-role caller returns `403` (see `require_role` in
`app/core/current_user.py`).

## Idempotency (for money/state-changing endpoints, once they exist)
Any endpoint that moves an order or offer past a draft state must accept
an `Idempotency-Key` header and guarantee a retried call with the same key
produces no additional state change. Not yet applicable — no such
endpoints exist in the foundation phase — but this is the contract they
must follow when built (see the approved architecture's Order/Offer state
machines).

## Request validation
Pydantic models define every request/response body. FastAPI's automatic
`422` on validation failure is left as-is (not overridden to a different
status code) — it's caught by the same error-shape handler so the response
body stays consistent.

## OpenAPI docs
Auto-generated at `/docs` (Swagger UI) and `/redoc`. No manual doc
maintenance needed — keep endpoint docstrings and Pydantic field
descriptions accurate instead.

## Implemented endpoints (Auth + Farmer Profile phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | None | Register (phone + password), returns tokens |
| POST | `/api/v1/auth/login` | None | Log in, returns tokens |
| POST | `/api/v1/auth/refresh` | None (refresh_token in body) | Rotate to a new token pair |
| POST | `/api/v1/auth/logout` | Bearer | Revoke the given session |
| POST | `/api/v1/auth/reset-password/request-otp` | None | Send a one-time SMS code for password-reset identity verification |
| POST | `/api/v1/auth/reset-password` | None | Reset password (phone + new password + the OTP just sent), returns tokens |
| GET | `/api/v1/farmers/me` | Bearer (farmer role) | Get own profile |
| PUT | `/api/v1/farmers/me` | Bearer (farmer role) | Update own profile |
| GET | `/api/v1/farmers/me/consents` | Bearer (farmer role) | List own consent history |
| POST | `/api/v1/farmers/me/consents` | Bearer (farmer role) | Record a consent grant/revocation |

**Note on auth method:** phone number + password was chosen for this phase
instead of OTP/SMS specifically because a real OTP flow needs a paid SMS
provider, which conflicts with the free-first constraint. This can be
swapped for OTP later without changing the token/session model (JWT access
token + hashed-refresh-token session) — only the credential-verification
step inside `auth_service.login()` would change.

All other domain routers (`weather`, `market`, `experts`) remain empty
placeholders — not yet implemented.

## Implemented endpoints (Farm + Plot + Crop phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/farms` | Bearer (farmer) | Create a farm |
| GET | `/api/v1/farms` | Bearer (farmer) | List my farms (paginated) |
| GET | `/api/v1/farms/{farm_id}` | Bearer (farmer) | Get my farm (404 if not mine) |
| PUT | `/api/v1/farms/{farm_id}` | Bearer (farmer) | Update my farm |
| DELETE | `/api/v1/farms/{farm_id}` | Bearer (farmer) | Soft-delete (deactivate) |
| POST | `/api/v1/farms/{farm_id}/plots` | Bearer (farmer) | Create a plot under my farm |
| GET | `/api/v1/farms/{farm_id}/plots` | Bearer (farmer) | List plots for my farm |
| GET | `/api/v1/plots/{plot_id}` | Bearer (farmer) | Get my plot |
| PUT | `/api/v1/plots/{plot_id}` | Bearer (farmer) | Update my plot |
| DELETE | `/api/v1/plots/{plot_id}` | Bearer (farmer) | Soft-delete (deactivate) |
| GET | `/api/v1/crops/master?query=` | Bearer (farmer) | Search the crop reference table |
| POST | `/api/v1/plots/{plot_id}/crops` | Bearer (farmer) | Create a crop cycle on my plot |
| GET | `/api/v1/plots/{plot_id}/crops` | Bearer (farmer) | List crop cycles for my plot |
| GET | `/api/v1/crops/{crop_cycle_id}` | Bearer (farmer) | Get my crop cycle |
| PUT | `/api/v1/crops/{crop_cycle_id}` | Bearer (farmer) | Update fields and/or advance status (validated) |
| POST | `/api/v1/crops/{crop_cycle_id}/close` | Bearer (farmer) | Harvest (only from `ready_for_harvest`) |
| GET | `/api/v1/farmers/me/dashboard` | Bearer (farmer) | Farm/plot/crop summary counts + crops nearing harvest |

Full data model, transition rules, and ownership details:
`docs/FARM_MODULE.md`, `docs/PLOT_MODULE.md`, `docs/CROP_MODULE.md`.

## Implemented endpoints (Crop Photo phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/crop-photo-sessions` | Bearer (farmer) | Create a photo session for one of my crop cycles |
| GET | `/api/v1/crop-photo-sessions/{id}` | Bearer (farmer) | Get my session |
| POST | `/api/v1/crop-photo-sessions/{id}/photos` | Bearer (farmer), multipart | Upload a photo (idempotent via `client_upload_id`) |
| GET | `/api/v1/crop-cycles/{crop_cycle_id}/photos` | Bearer (farmer) | List all photos for my crop cycle |
| GET | `/api/v1/crop-photos/{id}` | Bearer (farmer) | Photo metadata |
| GET | `/api/v1/crop-photos/{id}/file` | Bearer (farmer) | Stream the actual image bytes (`?thumbnail=true` for the thumbnail) |
| DELETE | `/api/v1/crop-photos/{id}` | Bearer (farmer) | Soft delete |

Full detail: `docs/CROP_PHOTO_MODULE.md`, `docs/IMAGE_STORAGE.md`,
`docs/IMAGE_VALIDATION.md`.

## Implemented endpoints (AI Disease Detection phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/crop-photos/{id}/analyze` | Bearer (farmer) | Analyze one photo (idempotent-ish — returns the in-flight job if one exists) |
| GET | `/api/v1/crop-photos/{id}/analysis` | Bearer (farmer) | Latest analysis for a photo |
| GET | `/api/v1/crop-cycles/{crop_cycle_id}/analyses` | Bearer (farmer) | Full analysis history for a crop cycle |
| GET | `/api/v1/ai/analysis/{analysis_id}` | Bearer (farmer) | Get one analysis by id |
| POST | `/api/v1/ai/sessions` | Bearer (farmer) | Create an AI analysis session for a crop-photo session |
| GET | `/api/v1/ai/sessions/{id}` | Bearer (farmer) | Get a session and its analyses |
| POST | `/api/v1/ai/sessions/{id}/analyze` | Bearer (farmer) | Analyze every photo in a session independently (no combined diagnosis) |

**Every real analysis this phase returns `result_status: "ai_unavailable"`**
— this is correct, not a bug. See `docs/AI_ARCHITECTURE.md`.

Full detail: `docs/AI_ARCHITECTURE.md`, `docs/AI_SAFETY.md`,
`docs/DISEASE_MODEL.md`, `docs/CROP_STAGE_MODEL.md`,
`docs/AI_MODEL_REGISTRY.md`, `docs/AI_EVALUATION.md`.

## Implemented endpoints (Local Language + Voice + Weather + Alerts phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/farms/{farm_id}/weather` | Bearer (farmer) | Current + forecast weather for a farm, cached; also triggers best-effort weather-alert generation as a side effect |
| GET | `/api/v1/notifications` | Bearer (farmer) | List own notifications (paginated, `?unread_only=`) |
| POST | `/api/v1/notifications/{id}/read` | Bearer (farmer) | Mark one notification read |
| POST | `/api/v1/notifications/read-all` | Bearer (farmer) | Mark all read |
| GET | `/api/v1/notification-preferences` | Bearer (farmer) | Get own preferences (auto-created with defaults) |
| PUT | `/api/v1/notification-preferences` | Bearer (farmer) | Partial update |
| GET | `/api/v1/ai/analysis/{id}/localized` | Bearer (farmer) | Farmer-friendly, localized rendering of an AI analysis (`?language=` optional, defaults to the farmer's own preference) |
| GET | `/api/v1/ai/languages` | Bearer (farmer) | Supported language codes (reuses the existing whitelist from Prompt 2 — not a duplicate list) |

**Naming deviation, documented:** `GET /api/v1/languages` from the
original spec is implemented as `GET /api/v1/ai/languages` instead —
grouped with the localized-analysis endpoint it exists to support, rather
than as a bare top-level route. `PUT /api/v1/farmer/language` was **not**
built as a separate endpoint — `PUT /api/v1/farmers/me` (existing since
Prompt 3) already updates `preferred_language_code`; adding a second route
for the same field would be a duplicate, not a new capability.

**`POST /api/v1/audio/speak` was deliberately not built** — see
docs/VOICE_AUDIO.md for why device-native TTS was chosen instead.

Full detail: `docs/WEATHER_ARCHITECTURE.md`, `docs/WEATHER_ALERT_RULES.md`,
`docs/NOTIFICATION_ARCHITECTURE.md`, `docs/VOICE_AUDIO.md`,
`docs/LOCATION_PRIVACY.md`.

## Implemented endpoints (Professional Network + Case Management phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/professionals | Bearer (field_agent/expert/trader/dealer) | Register a professional profile (always starts PENDING) |
| GET | /api/v1/professionals/me | Bearer (professional) | Get own profile |
| PUT | /api/v1/professionals/me/availability | Bearer (professional) | Update availability |
| GET | /api/v1/professionals?role= | Bearer (farmer/admin) | List VERIFIED professionals for a role |
| GET | /api/v1/professionals/{id} | Bearer (farmer/admin) | Get a professional's public profile |
| POST | /api/v1/professionals/{id}/verify | Bearer (admin only) | Verify a professional |
| POST | /api/v1/professionals/{id}/reject | Bearer (admin only) | Reject a professional |
| POST | /api/v1/professionals/{id}/suspend | Bearer (admin only) | Suspend a professional |
| POST | /api/v1/professionals/{id}/reactivate | Bearer (admin only) | Reactivate a professional |
| POST | /api/v1/cases | Bearer (farmer) | Create a case (with consent), triggers auto-assignment |
| GET | /api/v1/cases | Bearer (farmer) | List own cases |
| GET | /api/v1/cases/{id} | Bearer (farmer) | Get own case |
| POST | /api/v1/cases/{id}/accept | Bearer (field_agent/expert) | Accept an assignment |
| POST | /api/v1/cases/{id}/decline | Bearer (field_agent/expert) | Decline, triggers reassignment |
| POST | /api/v1/cases/{id}/review | Bearer (field_agent/expert) | Submit a structured review outcome |
| POST | /api/v1/cases/{id}/close | Bearer (farmer) | Close, revokes photo access |
| POST | /api/v1/cases/{id}/second-opinion | Bearer (farmer) | Request a second opinion (limited) |
| POST | /api/v1/cases/{id}/feedback | Bearer (farmer) | Submit feedback |
| GET | /api/v1/cases/{id}/audit | Bearer (farmer) | Case audit trail (reuses AuditLog) |

**Broadened, not new:** `GET /api/v1/crop-photos/{id}/file` now also
accepts FIELD_AGENT/EXPERT roles with a valid case-based
`PhotoAccessGrant`, in addition to the existing farmer-ownership path.

Full detail: `docs/PROFESSIONAL_NETWORK.md`, `docs/CASE_MANAGEMENT.md`,
`docs/CASE_ROUTING.md`, `docs/EXPERT_VERIFICATION.md`,
`docs/FIELD_AGENT_WORKFLOW.md`, `docs/DEALER_VERIFICATION.md`,
`docs/PHOTO_SHARING_PRIVACY.md`, `docs/CASE_AUDIT.md`.

## Implemented endpoints (Marketplace phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET/POST | /api/v1/products | Farmer (list, APPROVED only) / Admin (create) | Catalog |
| GET | /api/v1/products/{id} | Farmer/Admin/Dealer/Trader | Product detail |
| POST | /api/v1/products/{id}/approve, /reject, /suspend | Admin only | Product lifecycle |
| GET | /api/v1/products/{id}/prices, /price-history | Farmer | Reference price + history |
| POST | /api/v1/products/{id}/reference-prices | Admin only | Add a sourced reference price |
| GET | /api/v1/products/{id}/compare | Farmer | Cross-dealer price comparison |
| GET | /api/v1/dealer-products/{id}/scam-shield | Farmer | Neutral price-anomaly status |
| POST/PUT/GET | /api/v1/dealer-products* | Dealer/Trader | Listing management |
| POST/GET/PUT/DELETE | /api/v1/cart* | Farmer | Cart = DRAFT order operations |
| POST | /api/v1/orders/{id}/checkout | Farmer | Server-side price recalculation + confirmation |
| GET | /api/v1/orders, /orders/{id} | Farmer | Order history/detail |
| POST | /api/v1/orders/{id}/cancel | Farmer | Cancellation |
| POST | /api/v1/orders/{id}/pay, /pay/complete | Farmer | Sandbox payment (complete is TEST-ONLY) |
| GET | /api/v1/orders/{id}/delivery | Farmer | Delivery status |
| POST | /api/v1/orders/{id}/confirm-delivery | Farmer | Farmer's own receipt confirmation |
| POST/GET | /api/v1/orders/{id}/dispute | Farmer | File/view a dispute |
| POST | /api/v1/disputes/{id}/resolve | Admin only | Dispute resolution |
| POST | /api/v1/orders/{id}/refund/complete | Admin only | Mark refund complete (sandbox bookkeeping) |
| GET/POST | /api/v1/dealer/orders* | Dealer/Trader | Dealer order dashboard + fulfillment actions |
| PUT | /api/v1/dealer/orders/{id}/delivery | Dealer/Trader | Update delivery status |

Full detail: docs/PRODUCT_CATALOG.md, docs/DEALER_WORKFLOW.md,
docs/PRICE_TRANSPARENCY.md, docs/SCAM_SHIELD.md, docs/ORDER_WORKFLOW.md,
docs/PAYMENT_ARCHITECTURE.md, docs/DELIVERY_WORKFLOW.md,
docs/REFUND_DISPUTE.md.

## Implemented endpoints (Harvest Marketplace phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/harvests/from-crop-cycle/{id} | Farmer | Get-or-create harvest record (smart pre-fill) |
| GET | /api/v1/harvests | Farmer | List own harvests |
| POST | /api/v1/harvests/{id}/approaching, /confirm-ready | Farmer | Farmer-only readiness confirmations |
| POST | /api/v1/harvests/{id}/listing | Farmer | Create a sell listing (duplicate-warned) |
| GET | /api/v1/harvests/listings/me | Farmer | Own listings |
| POST/GET | /api/v1/marketplace/buyers* | Buyer | Buyer registration/profile (reuses ProfessionalProfile) |
| GET | /api/v1/marketplace/listings | Buyer | Browse active harvest listings |
| POST | /api/v1/marketplace/listings/{id}/offers | Buyer (verified) | Make an offer |
| GET | /api/v1/marketplace/listings/{id}/offers | Farmer | View offers on own listing |
| POST | /api/v1/marketplace/offers/{id}/counter, /counter-as-buyer | Farmer / Buyer | Append-only negotiation |
| POST | /api/v1/marketplace/offers/{id}/accept | Farmer | Concurrency-safe acceptance, creates SaleOrder |
| POST | /api/v1/marketplace/offers/{id}/reject | Farmer | Reject |
| GET/POST | /api/v1/marketplace/sales* | Farmer | Sale lifecycle (accept/advance/cancel/dispute/feedback) |
| GET/POST | /api/v1/marketplace/purchases* | Buyer | Buyer-side sale actions (confirm-delivery/pay/cancel/dispute/feedback) |
| GET | /api/v1/seeds, /seeds/{id} | Farmer | Thin reuse of the Prompt 9 product catalog, category=SEED |

Full detail: docs/HARVEST_MANAGEMENT.md, docs/FARMER_MARKETPLACE.md,
docs/BUYER_WORKFLOW.md, docs/OFFER_NEGOTIATION.md, docs/SALE_WORKFLOW.md,
docs/SEED_MARKETPLACE.md.

## Implemented endpoints (Smart Farmer AI Assistant phase)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/assistant/chat | Farmer | Send a message (voice or typed - both arrive as text, see docs/VOICE_ASSISTANT.md), get a real tool-backed answer |
| GET | /api/v1/assistant/history/{conversation_id} | Farmer | Full conversation history |
| DELETE | /api/v1/assistant/history/{conversation_id} | Farmer | Soft-archive a conversation |
| POST | /api/v1/assistant/feedback/{message_id} | Farmer | Rate one assistant answer |
| GET/PUT | /api/v1/assistant/preferences | Farmer | Response mode, voice, summary preferences |
| GET | /api/v1/assistant/daily-summary | Farmer | Real tool-composed summary, never invented |

Internal AI tools (`get_crop_status`, `get_weather_status`, etc.) are
**never exposed directly** as API endpoints - only the assistant
orchestrator calls them internally, per Requirement 78.

Full detail: docs/SMART_FARMER_AI.md, docs/AI_ARCHITECTURE.md,
docs/AI_TOOL_SYSTEM.md, docs/AI_GUARDRAILS.md.
