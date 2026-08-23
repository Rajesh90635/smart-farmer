"""
GET /api/v1/health  — liveness only, no dependency checks.
GET /api/v1/ready   — readiness, checks the database connection.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "healthy", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - readiness probes intentionally catch broadly
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "database_unreachable", "detail": str(exc)},
        )
    return {"status": "ready", "timestamp_utc": datetime.now(timezone.utc).isoformat()}
