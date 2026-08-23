# Development Setup

Exact commands to get this running locally. Written for Windows +
PowerShell first (per request), with Docker Compose as the primary path
and a manual path for anyone who prefers running services outside Docker.

## Prerequisites (all free)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- [Git](https://git-scm.com/)
- [VS Code](https://code.visualstudio.com/)
- [Python 3.12](https://www.python.org/downloads/) (only needed if you want to run backend/AI outside Docker)
- [Flutter SDK](https://docs.flutter.dev/get-started/install) (for mobile development)

## Option A — Docker Compose (recommended, matches CI/pilot most closely)

```powershell
git clone <your-repo-url>
cd smart-farmer
Copy-Item .env.example .env
# Edit .env: at minimum, set JWT_SIGNING_KEY to a real random value:
python -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up --build
```

This starts:
- `postgres` on `localhost:5432`
- `pgadmin` on `http://localhost:5050`
- `backend` (FastAPI) on `http://localhost:8000` — try `http://localhost:8000/api/v1/health` and `/docs`
- `ai-service` (FastAPI) on `http://localhost:8100` — try `http://localhost:8100/ai/health`

Run migrations (first time, and after any future schema change):
```powershell
docker compose exec backend alembic upgrade head
```

Stop everything:
```powershell
docker compose down          # keeps data
docker compose down -v       # also wipes the Postgres volume
```

## Option B — Running services directly (no Docker)

Requires a local PostgreSQL install (or point `DATABASE_URL` at any
Postgres you already have running — e.g. one inside Docker Compose while
you run the backend natively for faster iteration).

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:DATABASE_URL = "postgresql+psycopg://postgres:<password>@localhost:5432/smart_farmer_dev"
$env:JWT_SIGNING_KEY = "<a real random value>"
$env:ENVIRONMENT = "development"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### AI service

```powershell
cd ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:ENVIRONMENT = "development"
uvicorn app.main:app --reload --port 8100
```

### Mobile (Flutter)

```powershell
cd mobile
flutter pub get
flutter gen-l10n
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```
(`10.0.2.2` is the Android emulator's alias for your host machine's
`localhost`; use `http://localhost:8000/api/v1` for iOS simulator or a
real device on the same LAN as your machine's actual IP.)

## Running tests

### Backend
```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql+psycopg://postgres:<password>@localhost:5432/smart_farmer_test"
$env:JWT_SIGNING_KEY = "test-only-signing-key"
$env:ENVIRONMENT = "testing"
pytest tests/ -v
```
Expected: **20 passed** (verified in the build environment against a real
Postgres instance — see PROJECT_STATUS.md for the exact run output).

### AI service
```powershell
cd ai
.venv\Scripts\Activate.ps1
pytest tests/ -v
```
Expected: **4 passed**.

### Mobile
```powershell
cd mobile
flutter test
```
Not yet run in the build environment (no Flutter SDK available there) —
run this yourself and report back if anything fails; the widget test
targets exact placeholder text that's easy to get out of sync.

## Database administration

Open pgAdmin at `http://localhost:5050` (Docker Compose) and register a
server pointing at host `postgres`, port `5432`, using the credentials from
your `.env`. See docs/DATABASE.md for the migration workflow.
