"""
User: the authentication identity. Deliberately minimal — per the "do not
store unnecessary personal information" rule, this holds only what
authentication itself needs (phone number as the login identifier,
password hash, account status, optional recovery email). Farmer-specific
profile data (name, language) lives in FarmerProfile, a separate table, so
a future non-farmer account type (dealer, buyer, field agent, expert staff
login) can reuse User without dragging farmer-only fields along.

Privacy notes (see docs/SECURITY.md "Privacy" section for the full table):
- phone_number: required, sensitive PII, used only for login and account
  recovery. Never exposed to any role other than the user themselves.
- email: optional, sensitive PII, same access rule as phone_number.
- password_hash: never serialized in any API response, ever.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Login identifier. Unique + indexed since it's looked up on every login.
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Optional, for account recovery only in this phase - not used for login.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[AccountStatus] = mapped_column(
        SAEnum(AccountStatus, name="account_status", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=AccountStatus.ACTIVE,
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    farmer_profile: Mapped["FarmerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    consents: Mapped[list["ConsentRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
