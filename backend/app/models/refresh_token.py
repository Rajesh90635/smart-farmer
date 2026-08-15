"""
RefreshToken (session). The raw refresh token is a high-entropy random
string generated at issuance and returned to the client exactly once —
only its SHA-256 hash is ever stored, so a database read can't be used to
impersonate a session (same principle as password hashing, applied to
tokens). Revocation is "soft delete" via revoked_at so audit history isn't
lost on logout.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # SHA-256 hex digest of the raw refresh token. Never the raw value.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now
