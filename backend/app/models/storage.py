"""
Storage: D53-01/02/03 (docs/audit/FINAL_CANONICAL_group_C.md) - a physical
storage facility a farmer records (own on-farm storage, a rented
warehouse/cold-storage/godown, etc.), mirroring harvest_service.py's
CRUD/ownership conventions (farmer_id-scoped, same as HarvestRecord).
cost_per_unit_per_day is an optional, farmer-entered rate only - it never
auto-generates a LedgerEntry; the farmer records actual spend themselves
under the existing LedgerCategory.STORAGE category (already added by
D69-08 - this row's own dependency, satisfied before this batch).
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StorageType(str, enum.Enum):
    ON_FARM = "on_farm"
    RENTED_WAREHOUSE = "rented_warehouse"
    COLD_STORAGE = "cold_storage"
    GODOWN = "godown"
    OTHER = "other"


class Storage(Base):
    __tablename__ = "storages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    location: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_type: Mapped[StorageType] = mapped_column(
        SAEnum(StorageType, name="storage_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    capacity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cost_per_unit_per_day: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
