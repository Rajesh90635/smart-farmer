"""
FarmInfrastructure: D2-07 (docs/audit/FINAL_CANONICAL_group_A.md) -
farmer-entered, informational only. No automated logic reads this yet -
it exists purely so a farmer can record what physical infrastructure
(storage/well/shed/equipment) their farm has, mirroring Plot's own
list-per-farm CRUD shape.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class FarmInfrastructureType(str, enum.Enum):
    STORAGE = "storage"
    WELL = "well"
    BOREWELL = "borewell"
    SHED = "shed"
    EQUIPMENT = "equipment"
    OTHER = "other"


class FarmInfrastructure(Base):
    __tablename__ = "farm_infrastructure"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    infrastructure_type: Mapped[FarmInfrastructureType] = mapped_column(
        SAEnum(FarmInfrastructureType, name="farm_infrastructure_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
