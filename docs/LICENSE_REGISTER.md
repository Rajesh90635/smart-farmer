# Third-Party License Register

Every dependency actually added to this repository so far. Nothing is
added to `requirements.txt` / `pubspec.yaml` without a row here first, per
the development rules.

## Backend (`backend/requirements.txt`)

| Package | Version | License | Source | Intended use | Commercial-use OK? |
|---|---|---|---|---|---|
| fastapi | 0.115.0 | MIT | PyPI | Web framework | Yes |
| uvicorn | 0.30.6 | BSD-3-Clause | PyPI | ASGI server | Yes |
| pydantic | 2.9.2 | MIT | PyPI | Data validation | Yes |
| pydantic-settings | 2.5.2 | MIT | PyPI | Env-based config | Yes |
| sqlalchemy | 2.0.35 | MIT | PyPI | ORM | Yes |
| alembic | 1.13.2 | MIT | PyPI | DB migrations | Yes |
| psycopg[binary] | 3.2.2 | LGPL-3.0 | PyPI | PostgreSQL driver | Yes (LGPL permits linking/use; verify if statically bundling for distribution) |
| pillow | 10.4.0 | HPND (permissive, MIT/BSD-style) | PyPI | Image validation, quality heuristics, processing | Yes |
| pytesseract | 0.3.13 | Apache 2.0 | PyPI | Python wrapper for Tesseract OCR - Phase 30 invoice text extraction | Yes |
| tesseract-ocr (system package, not a Python dependency) | 5.3.4 (as installed) | Apache 2.0 | Ubuntu/Debian apt repository | The actual OCR engine pytesseract wraps - free, fully local/offline, no cloud service, no API key | Yes |
| python-multipart | 0.0.9 | Apache-2.0 | PyPI | multipart/form-data parsing for photo upload | Yes |
| python-jose[cryptography] | 3.3.0 | MIT | PyPI | JWT encode/decode | Yes |
| passlib | 1.7.4 | BSD-3-Clause | PyPI | Password hashing framework | Yes |
| bcrypt | 4.0.1 | Apache-2.0 | PyPI | bcrypt hashing backend (pinned — see note below) | Yes |
| pytest | 8.3.3 | MIT | PyPI | Testing | Yes (dev-only) |
| pytest-asyncio | 0.24.0 | Apache-2.0 | PyPI | Async test support | Yes (dev-only) |
| httpx | 0.27.2 | BSD-3-Clause | PyPI | Test client transport | Yes (dev-only) |
| ruff | 0.6.9 | MIT | PyPI | Lint/format | Yes (dev-only) |
| mypy | 1.11.2 | MIT | PyPI | Type checking | Yes (dev-only) |

**Note on `bcrypt` pin:** `passlib[bcrypt]`'s default resolution pulled
`bcrypt>=4.1`, which removed an attribute passlib's backend-detection
probes for, breaking password hashing at runtime (caught by the test
suite — see PROJECT_STATUS.md). Pinned to `4.0.1` explicitly. Revisit this
pin if passlib releases a fix for newer bcrypt versions.

## AI service (`ai/requirements.txt`)

| Package | Version | License | Source | Intended use | Commercial-use OK? |
|---|---|---|---|---|---|
| fastapi | 0.115.0 | MIT | PyPI | Web framework | Yes |
| uvicorn | 0.30.6 | BSD-3-Clause | PyPI | ASGI server | Yes |
| pydantic | 2.9.2 | MIT | PyPI | Data validation | Yes |
| pydantic-settings | 2.5.2 | MIT | PyPI | Env-based config | Yes |
| pytest | 8.3.3 | MIT | PyPI | Testing | Yes (dev-only) |
| httpx | 0.27.2 | BSD-3-Clause | PyPI | Test client transport | Yes (dev-only) |

No ML/model libraries (PyTorch, OpenCV, Hugging Face, etc.) are added yet —
those come with the vision/speech/LLM epics, each with its own license
verification row added at that time.

## Mobile (`mobile/pubspec.yaml`)

| Package | Version | License | Source | Intended use | Commercial-use OK? |
|---|---|---|---|---|---|
| flutter (SDK) | — | BSD-3-Clause | Google | App framework | Yes |
| flutter_localizations (SDK) | — | BSD-3-Clause | Google | Localization | Yes |
| intl | ^0.19.0 | BSD-3-Clause | pub.dev | Locale/date formatting support for gen-l10n | Yes |
| http | ^1.2.2 | BSD-3-Clause | pub.dev | HTTP client underlying ApiClient | Yes |
| flutter_lints | ^4.0.0 | BSD-3-Clause | pub.dev | Lint rules | Yes (dev-only) |
| image_picker | ^1.1.2 | BSD-3-Clause (Apache-2.0 for Android platform code) | pub.dev | Camera + gallery access | Yes |
| http_parser | ^4.0.2 | BSD-3-Clause | pub.dev | Content-Type handling for multipart upload | Yes |
| connectivity_plus | ^6.0.5 | BSD-3-Clause | pub.dev | Real network-status detection | Yes |
| path_provider | ^2.1.4 | BSD-3-Clause | pub.dev | App-local persistent storage directory for the offline photo-upload queue | Yes |
| flutter_tts | ^4.2.0 | Not independently re-verified live (pub.dev not reachable from this sandbox) - believed permissive per training-data knowledge, added Step 14 | pub.dev | Device-native text-to-speech for farmer-facing voice output | Assumed, not confirmed |
| geolocator | ^13.0.2 (resolved 13.0.4) | MIT - verified live by reading the actual fetched package's LICENSE file at `Pub/Cache/hosted/pub.dev/geolocator-13.0.4/LICENSE` (a Flutter SDK/pub.dev connection is available in this environment now, unlike every prior phase - not assumed from training data) | pub.dev | Device GPS position capture for Add Farm's "Use current location" | Confirmed |

## External services (non-dependency)

| Service | Cost | Provider | Purpose | Notes |
|---|---|---|---|---|
| OpenStreetMap Nominatim (reverse geocoding) | Free, public API | OpenStreetMap Foundation | Best-effort auto-fill of state/district/mandal/village text from a farmer's captured GPS coordinates on Add Farm | Called directly over `http` (no separate package) only when the farmer explicitly taps "Use current location" - sends that one coordinate pair to a third-party service, a real privacy trade-off disclosed to the user, not the default for lat/lng capture. Subject to Nominatim's usage policy (max ~1 request/second, requires an identifying User-Agent) - not suitable for high-volume use without self-hosting; acceptable here since it is one on-demand, farmer-initiated call. |

## Infrastructure

| Component | License | Notes |
|---|---|---|
| PostgreSQL 16 | PostgreSQL License | Free, permissive |
| Docker / Docker Compose | Apache-2.0 | Free |

## Flagged for verification before any real use (not yet used — placeholders only)

| Item | Status |
|---|---|
| Any open plant-disease dataset (e.g. PlantVillage) for the vision classifier | Not yet chosen or downloaded — license must be read and this row updated before training starts |
| Any open-weight LLM run via Ollama | Not yet chosen — license varies per model, must be verified per the approved architecture's AI Model Strategy section |
| Whisper / faster-whisper model weights | Not yet used — verify weight license separately from the code license |
| Piper / Coqui TTS voice packs | Not yet used — voice packs may carry per-language licenses |
| PlantVillage-trained MobileNet/EfficientNet-lite checkpoints | Evaluated on paper this phase (see docs/AI_ARCHITECTURE.md) — **not downloaded** (network restriction in build environment); license varies by specific checkpoint/repo and must be verified before any integration |
| Hugging Face plant-disease classification models (general) | Evaluated on paper this phase — **not downloaded**; license must be checked per specific model card before any integration |
