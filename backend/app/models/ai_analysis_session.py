"""
AIAnalysisSession: groups AI predictions across a CropPhotoSession's
multiple photos (Requirement 20/21) - Photo 1 -> Prediction, Photo 2 ->
Prediction, etc., all linked to one session, WITHOUT inventing a combined
diagnosis. Multi-image model fusion is not implemented (no such model
exists) - this table only preserves the relationship for a future module
(AI + expert + farmer confirmation operating on the same crop-check case).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AIAnalysisSession(Base):
    __tablename__ = "ai_analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_photo_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_photo_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="analysis_session")
