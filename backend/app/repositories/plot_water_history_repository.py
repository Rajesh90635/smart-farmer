import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plot_water_history import PlotWaterHistory


def create(db: Session, entry: PlotWaterHistory) -> PlotWaterHistory:
    db.add(entry)
    return entry


def list_for_plot(db: Session, plot_id: uuid.UUID) -> list[PlotWaterHistory]:
    return list(
        db.execute(
            select(PlotWaterHistory).where(PlotWaterHistory.plot_id == plot_id).order_by(PlotWaterHistory.changed_at.asc())
        ).scalars().all()
    )
