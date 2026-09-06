"""
SoilTestResult: D20-02 (docs/audit/FINAL_CANONICAL_group_A.md) - the
measured-values table FK'd to SoilSample. D20-03..09/11 are columns here,
not separate models, per this domain's own canonical resolution.

D20-12 (Stale test): is_stale() mirrors WeatherSnapshot.is_stale()'s exact
pattern - a computed property, never a stored/cached flag that could go
stale itself. The max-age threshold is a real agronomic convention
(soil nutrient levels are typically re-tested every 2-3 years), not
invented for this project - same disclosed-placeholder treatment as this
project's other threshold settings (see Settings.soil_test_max_age_days).
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SoilTestResult(Base):
    __tablename__ = "soil_test_results"
    __table_args__ = (
        CheckConstraint("ph_value IS NULL OR (ph_value >= 0 AND ph_value <= 14)", name="ck_soil_test_results_ph_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    soil_sample_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("soil_samples.id", ondelete="CASCADE"), nullable=False, index=True)

    test_date: Mapped[date] = mapped_column(Date, nullable=False)  # D20-11

    ph_value: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)  # D20-03
    nitrogen_kg_per_ha: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # D20-04
    phosphorus_kg_per_ha: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # D20-05
    potassium_kg_per_ha: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # D20-06
    organic_carbon_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # D20-07
    ec_ds_per_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)  # D20-08
    micronutrients: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # D20-09 - varies by lab, flexible key/value

    report_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)  # D20-10

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def is_stale(self, today: date, max_age_days: int) -> bool:
        return (today - self.test_date).days > max_age_days
