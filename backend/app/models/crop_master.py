"""
CropMaster: the reusable crop reference entity. CropCycle rows point here
via crop_id rather than storing a crop name string directly - this is
what makes "Do not duplicate crop names for every crop cycle" true, and
gives future modules (disease models, crop-stage rules, weather rules,
treatment rules, market information) a single place to hang crop-specific
data off of.

local_names is a JSONB dict of {language_code: name} rather than separate
columns per language - adding a new supported language never requires a
migration, consistent with the localization architecture's "don't
hard-code language logic" principle.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropMaster(Base):
    __tablename__ = "crop_master"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    local_names: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scientific_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    crop_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    crop_cycles: Mapped[list["CropCycle"]] = relationship(back_populates="crop")
