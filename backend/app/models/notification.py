"""
Notification: the unified notification record (Requirement 24). Text is
stored already-rendered in the farmer's language at creation time
(simplest correct approach for a single-farmer-owned row - no need to
re-render per reader since only the owning farmer ever reads it).

Deduplication (Requirement 27) is enforced by a DB unique constraint on
(farmer_id, dedup_key) - not just application logic. `dedup_key` encodes
enough context (alert type + subject + time bucket, e.g.
"rain_alert:farm:{farm_id}:2026-06-01") that the same real-world event
can never produce two rows, while genuinely distinct events (a new day,
a different farm) correctly get their own notification.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NotificationCategory(str, enum.Enum):
    WEATHER_ALERT = "weather_alert"
    RAIN_ALERT = "rain_alert"
    HEAVY_RAIN_ALERT = "heavy_rain_alert"
    CROP_ALERT = "crop_alert"
    DISEASE_ALERT = "disease_alert"
    HARVEST_ALERT = "harvest_alert"
    STOCK_ALERT = "stock_alert"  # D22-06/D24-08/D24-09 (docs/audit/c04_inputs.md): input inventory low-stock/expiry
    PAYMENT_ALERT = "payment_alert"  # D64-06/D66-04 (docs/audit/c10_payments_finance.md): payment failure
    # ORDER_ALERT, MARKET_ALERT deliberately NOT included - future phases only.


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("farmer_id", "dedup_key", name="uq_notifications_farmer_dedup_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SAEnum(NotificationCategory, name="notification_category", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SAEnum(NotificationPriority, name="notification_priority", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)

    dedup_key: Mapped[str] = mapped_column(String(300), nullable=False)

    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "farm", "crop_cycle"
    related_entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # D89-01/02/07 (docs/FINAL_GAP_REPORT.md): which version of the
    # deterministic rule module produced this notification (e.g.
    # "weather_alert_rules_v1"), so a historical notification stays
    # explainable/reproducible even after the rule itself changes -
    # mirrors CropRiskScoreResponse.rule_version's existing pattern.
    # Nullable because not every notification is rule-triggered.
    rule_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
