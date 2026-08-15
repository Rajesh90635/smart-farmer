"""
AIModelRegistry: knows which model generated every AI result (Requirement
32/33). An active model is never silently swapped - a new model version is
always a NEW row, never an in-place edit of an existing one, so historical
AIAnalysis rows (which store model_name/model_version as immutable strings
in addition to this FK) always identify the exact model that produced them
even after the registry's "active" row changes.

The single seeded row this phase (see migration) represents "no real model
is configured yet" as an honest, queryable fact - not a magic string
scattered through code. See docs/AI_MODEL_REGISTRY.md.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AIModelRegistry(Base):
    __tablename__ = "ai_model_registry"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_ai_model_registry_name_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_size: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "224x224"
    # List of crop_master.id strings. A JSONB array rather than a join
    # table - "do not create unnecessary tables" - revisit if per-crop
    # metadata (e.g. per-crop accuracy) is ever needed on this relationship.
    supported_crop_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
