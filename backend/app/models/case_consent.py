"""
CaseConsent: what the farmer agreed to share, before the FIRST time a
case shares anything externally. `shared_items` is explicit (e.g.
["crop_photo", "ai_result", "crop_stage", "farm_area"]) - never an
unlabeled blanket consent. `withdrawn_at` supports revocation (future
sharing stops) without destroying the historical record (accountability
requirement - the row is never deleted).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CaseConsent(Base):
    __tablename__ = "case_consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_health_cases.id", ondelete="CASCADE"), unique=True, nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False)
    shared_items: Mapped[list] = mapped_column(JSONB, nullable=False)

    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
