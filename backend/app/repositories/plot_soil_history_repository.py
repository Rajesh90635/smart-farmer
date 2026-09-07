import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plot_soil_history import PlotSoilHistory


def create(db: Session, entry: PlotSoilHistory) -> PlotSoilHistory:
    db.add(entry)
    return entry


def list_for_plot(db: Session, plot_id: uuid.UUID) -> list[PlotSoilHistory]:
    return list(
        db.execute(
            select(PlotSoilHistory).where(PlotSoilHistory.plot_id == plot_id).order_by(PlotSoilHistory.changed_at.asc())
        ).scalars().all()
    )
