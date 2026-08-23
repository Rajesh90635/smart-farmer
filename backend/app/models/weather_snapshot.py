"""
WeatherSnapshot: caches weather data per farm (Requirement 22). One table
covers both CURRENT and FORECAST rows (snapshot_type distinguishes them)
rather than two near-identical tables - "do not create unnecessary tables."

Never fabricated: every row's `provider` field records where the data
actually came from. A row with provider="none" cannot exist - if no
provider is configured, no snapshot is ever created (see WeatherService),
and the API returns WEATHER_NOT_CONFIGURED instead (Requirement 51).
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WeatherSnapshotType(str, enum.Enum):
    CURRENT = "current"
    FORECAST = "forecast"


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_type: Mapped[WeatherSnapshotType] = mapped_column(
        SAEnum(WeatherSnapshotType, name="weather_snapshot_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    forecast_date: Mapped[Date | None] = mapped_column(Date, nullable=True)  # only for FORECAST rows

    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "open_meteo" - never "none"

    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    feels_like_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain_probability_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    condition_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # provider-specific code, mapped to a friendly label at the API layer, not here
    sunrise: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sunset: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    def is_stale(self, now: datetime) -> bool:
        return now > self.expires_at
