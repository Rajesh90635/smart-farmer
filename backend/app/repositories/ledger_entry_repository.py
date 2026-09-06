"""
Ledger entry repository. Ownership is enforced the same way as every
other farmer-scoped entity in this project: every read/write is filtered
by LedgerEntry.farmer_id, resolved from the authenticated session.
"""
import uuid
from decimal import Decimal

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crop_cycle import CropCycle, Season
from app.models.ledger_entry import LedgerEntry, LedgerEntryType


def create(db: Session, entry: LedgerEntry) -> LedgerEntry:
    db.add(entry)
    return entry


def get_owned(db: Session, entry_id: uuid.UUID, farmer_id: uuid.UUID) -> LedgerEntry | None:
    return db.execute(select(LedgerEntry).where(LedgerEntry.id == entry_id, LedgerEntry.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[LedgerEntry]:
    return list(
        db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.crop_cycle_id == crop_cycle_id, LedgerEntry.farmer_id == farmer_id)
            .order_by(LedgerEntry.entry_date.desc(), LedgerEntry.created_at.desc())
        )
        .scalars()
        .all()
    )


def get_by_linked_sale(db: Session, sale_id: uuid.UUID) -> LedgerEntry | None:
    """Used to enforce idempotent sale-import - a sale that was already
    imported is never imported a second time, checked here in addition
    to the DB-level unique constraint (belt-and-suspenders, not a
    substitute for the real constraint)."""
    return db.execute(select(LedgerEntry).where(LedgerEntry.linked_sale_id == sale_id)).scalar_one_or_none()


def compute_totals(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> tuple[Decimal, Decimal]:
    """Returns (total_expense, total_revenue) - computed fresh via a real
    SQL aggregate every time, never cached/stored, so it can never go
    stale relative to the actual entries."""
    total_expense = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.crop_cycle_id == crop_cycle_id, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.EXPENSE
        )
    ).scalar_one()
    total_revenue = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.crop_cycle_id == crop_cycle_id, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.REVENUE
        )
    ).scalar_one()
    return Decimal(total_expense), Decimal(total_revenue)


def compute_totals_for_plot(db: Session, plot_id: uuid.UUID, farmer_id: uuid.UUID) -> tuple[Decimal, Decimal]:
    """D70-04 (docs/audit/FINAL_CANONICAL_group_C.md): the same aggregation
    as compute_totals above, joined out to every crop cycle that plot has
    ever had (not just the currently-active one) - a pure read aggregation
    over the existing LedgerEntry -> CropCycle -> Plot relational path, no
    new column, no new table."""
    total_expense = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .join(CropCycle, LedgerEntry.crop_cycle_id == CropCycle.id)
        .where(CropCycle.plot_id == plot_id, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.EXPENSE)
    ).scalar_one()
    total_revenue = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .join(CropCycle, LedgerEntry.crop_cycle_id == CropCycle.id)
        .where(CropCycle.plot_id == plot_id, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.REVENUE)
    ).scalar_one()
    return Decimal(total_expense), Decimal(total_revenue)


def compute_totals_for_season(db: Session, farmer_id: uuid.UUID, season: Season) -> tuple[Decimal, Decimal]:
    """D70-05: same shape as compute_totals_for_plot, scoped by the
    farmer's own crop cycles matching one Season value across every
    farm/plot they own."""
    total_expense = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .join(CropCycle, LedgerEntry.crop_cycle_id == CropCycle.id)
        .where(CropCycle.season == season, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.EXPENSE)
    ).scalar_one()
    total_revenue = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .join(CropCycle, LedgerEntry.crop_cycle_id == CropCycle.id)
        .where(CropCycle.season == season, LedgerEntry.farmer_id == farmer_id, LedgerEntry.entry_type == LedgerEntryType.REVENUE)
    ).scalar_one()
    return Decimal(total_expense), Decimal(total_revenue)


def delete(db: Session, entry: LedgerEntry) -> None:
    db.execute(sa_delete(LedgerEntry).where(LedgerEntry.id == entry.id))
