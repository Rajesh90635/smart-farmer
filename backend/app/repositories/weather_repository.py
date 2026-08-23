import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.weather_snapshot import WeatherSnapshot, WeatherSnapshotType


def get_fresh_current(db: Session, farm_id: uuid.UUID) -> WeatherSnapshot | None:
    now = datetime.now(timezone.utc)
    return db.execute(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.farm_id == farm_id, WeatherSnapshot.snapshot_type == WeatherSnapshotType.CURRENT, WeatherSnapshot.expires_at > now)
        .order_by(WeatherSnapshot.fetched_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_latest_current(db: Session, farm_id: uuid.UUID) -> WeatherSnapshot | None:
    """Used for the 'show stale cached data with a timestamp' fallback
    (Requirement 23) - unlike get_fresh_current, this ignores expiry."""
    return db.execute(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.farm_id == farm_id, WeatherSnapshot.snapshot_type == WeatherSnapshotType.CURRENT)
        .order_by(WeatherSnapshot.fetched_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_fresh_forecast(db: Session, farm_id: uuid.UUID) -> list[WeatherSnapshot]:
    now = datetime.now(timezone.utc)
    latest_fetch = db.execute(
        select(WeatherSnapshot.fetched_at)
        .where(WeatherSnapshot.farm_id == farm_id, WeatherSnapshot.snapshot_type == WeatherSnapshotType.FORECAST, WeatherSnapshot.expires_at > now)
        .order_by(WeatherSnapshot.fetched_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest_fetch is None:
        return []
    return list(
        db.execute(
            select(WeatherSnapshot)
            .where(WeatherSnapshot.farm_id == farm_id, WeatherSnapshot.snapshot_type == WeatherSnapshotType.FORECAST, WeatherSnapshot.fetched_at == latest_fetch)
            .order_by(WeatherSnapshot.forecast_date.asc())
        ).scalars().all()
    )


def save_snapshot(db: Session, snapshot: WeatherSnapshot) -> WeatherSnapshot:
    db.add(snapshot)
    return snapshot
