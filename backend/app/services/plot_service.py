import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.area_units import to_square_meters
from app.core.errors import AppError
from app.models.farm import FarmStatus
from app.models.plot import Plot
from app.repositories import farm_repository, plot_repository
from app.schemas.plot import PlotCreateRequest, PlotListResponse, PlotResponse, PlotUpdateRequest
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


def _get_owned_farm_or_404(db: Session, farmer_id: str, farm_id: uuid.UUID):
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)
    return farm


def create_plot(db: Session, farmer_id: str, farm_id: uuid.UUID, payload: PlotCreateRequest) -> PlotResponse:
    # Verifying farm ownership BEFORE creating a plot under it is what
    # makes "a farmer must never manipulate another farmer's plot"
    # actually true at creation time, not just at read time.
    _get_owned_farm_or_404(db, farmer_id, farm_id)

    plot = Plot(
        farm_id=farm_id,
        plot_name=payload.plot_name,
        area_value=payload.area_value,
        area_unit=payload.area_unit,
        area_sqm=to_square_meters(payload.area_value, payload.area_unit),
        latitude=payload.latitude,
        longitude=payload.longitude,
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
    )
    plot_repository.create(db, plot)
    db.flush()

    AuditLogger(db).log("PLOT_CREATED", actor_id=farmer_id, actor_role="farmer", entity="plot", entity_id=str(plot.id))

    db.commit()
    db.refresh(plot)
    return PlotResponse.model_validate(plot)


def list_plots_for_farm(
    db: Session, farmer_id: str, farm_id: uuid.UUID, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0
) -> PlotListResponse:
    _get_owned_farm_or_404(db, farmer_id, farm_id)
    plots, total = plot_repository.list_for_farm(db, farm_id, limit=limit, offset=offset)
    return PlotListResponse(items=[PlotResponse.model_validate(p) for p in plots], total=total)


def get_my_plot(db: Session, farmer_id: str, plot_id: uuid.UUID) -> PlotResponse:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)
    return PlotResponse.model_validate(plot)


def update_my_plot(db: Session, farmer_id: str, plot_id: uuid.UUID, payload: PlotUpdateRequest) -> PlotResponse:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    if payload.plot_name is not None:
        plot.plot_name = payload.plot_name
    if payload.latitude is not None:
        plot.latitude = payload.latitude
    if payload.longitude is not None:
        plot.longitude = payload.longitude
    if payload.soil_type is not None:
        plot.soil_type = payload.soil_type
    if payload.irrigation_type is not None:
        plot.irrigation_type = payload.irrigation_type

    if payload.area_value is not None or payload.area_unit is not None:
        new_value = payload.area_value if payload.area_value is not None else plot.area_value
        new_unit = payload.area_unit if payload.area_unit is not None else plot.area_unit
        plot.area_value = new_value
        plot.area_unit = new_unit
        plot.area_sqm = to_square_meters(new_value, new_unit)

    AuditLogger(db).log("PLOT_UPDATED", actor_id=farmer_id, actor_role="farmer", entity="plot", entity_id=str(plot.id))

    db.commit()
    db.refresh(plot)
    return PlotResponse.model_validate(plot)


def deactivate_my_plot(db: Session, farmer_id: str, plot_id: uuid.UUID) -> None:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    plot.status = FarmStatus.INACTIVE  # soft delete - same reasoning as Farm

    AuditLogger(db).log("PLOT_DEACTIVATED", actor_id=farmer_id, actor_role="farmer", entity="plot", entity_id=str(plot.id))

    db.commit()
