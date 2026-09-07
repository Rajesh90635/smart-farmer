"""
StorageUsage: D53-04/05/07 (docs/audit/FINAL_CANONICAL_group_C.md) - one
row per "harvest moved into storage" episode, linking a Storage to a
HarvestRecord with stored_at/released_at timestamps and the quantity
placed. farmer_id is denormalized directly onto this row (not resolved
via a join through Storage/HarvestRecord each time) - the same
"child entity carries its own farmer_id" convention HarvestListing
already uses despite also being reachable via harvest_record_id.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StorageUsage(Base):
    __tablename__ = "storage_usages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("storages.id", ondelete="CASCADE"), nullable=False, index=True)
    harvest_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("harvest_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
