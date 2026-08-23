"""
State / District / Mandal / Village: administrative-division master data
for location dropdowns (farm/farmer registration, service areas, etc.) -
replaces free-text location entry with a normalized reference. Only
Andhra Pradesh's states/districts are seeded so far (see the migration);
Mandal and Village have no seed data anywhere yet - no authoritative
mandal/village dataset was available, so these tables are created empty
and populated later rather than fabricated. Other states/mandals/villages
are added the same way as the app expands to them.
"""
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    districts: Mapped[list["District"]] = relationship(back_populates="state", cascade="all, delete-orphan")


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("state_id", "name", name="uq_district_state_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    state: Mapped["State"] = relationship(back_populates="districts")
    mandals: Mapped[list["Mandal"]] = relationship(back_populates="district", cascade="all, delete-orphan")


class Mandal(Base):
    __tablename__ = "mandals"
    __table_args__ = (UniqueConstraint("district_id", "name", name="uq_mandal_district_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    district: Mapped["District"] = relationship(back_populates="mandals")
    villages: Mapped[list["Village"]] = relationship(back_populates="mandal", cascade="all, delete-orphan")


class Village(Base):
    __tablename__ = "villages"
    __table_args__ = (UniqueConstraint("mandal_id", "name", name="uq_village_mandal_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mandal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mandals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    mandal: Mapped["Mandal"] = relationship(back_populates="villages")
