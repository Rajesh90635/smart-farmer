import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.area_units import to_square_meters
from app.core.errors import AppError
from app.models.farm import FarmStatus
from app.models.plot import Plot
from app.models.plot_soil_history import PlotSoilHistory
from app.models.plot_water_history import PlotWaterHistory
from app.repositories import farm_repository, plot_repository, plot_soil_history_repository, plot_water_history_repository
from app.schemas.plot import PlotCreateRequest, PlotListResponse, PlotResponse, PlotUpdateRequest
from app.schemas.plot_history import (
    PlotSoilHistoryListResponse,
    PlotSoilHistoryResponse,
    PlotWaterHistoryListResponse,
    PlotWaterHistoryResponse,
)
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


def _record_soil_history(db: Session, plot_id: uuid.UUID, soil_type: str | None, soil_category) -> None:
    """D19-04 (docs/audit/FINAL_CANONICAL_group_A.md): mirrors
    crop_cycle_service._record_stage_history's convention - records that
    a change actually happened, when. Only called for a genuine change."""
    entry = PlotSoilHistory(
        plot_id=plot_id,
        soil_type=soil_type,
        soil_category=soil_category,
        changed_at=datetime.now(timezone.utc),
    )
    plot_soil_history_repository.create(db, entry)


def _record_water_history(db: Session, plot_id: uuid.UUID, water_availability) -> None:
    """D17-06 (docs/audit/FINAL_CANONICAL_group_A.md). Only called for a
    genuine change - never speculatively."""
    entry = PlotWaterHistory(
        plot_id=plot_id,
        water_availability=water_availability,
        changed_at=datetime.now(timezone.utc),
    )
    plot_water_history_repository.create(db, entry)


def _serialize_boundary_points(points) -> list[dict] | None:
    """D3-07 (docs/audit/FINAL_CANONICAL_group_A.md): Decimal isn't JSON-
    serializable, so each point is stored as plain floats in the JSONB
    column - display/reference precision only, never used for financial
    or area computation (area_value/area_sqm stay Decimal, unaffected)."""
    if points is None:
        return None
    return [{"latitude": float(p.latitude), "longitude": float(p.longitude)} for p in points]


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
        boundary_points=_serialize_boundary_points(payload.boundary_points),
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
        irrigation_source=payload.irrigation_source,
        soil_category=payload.soil_category,
        water_availability=payload.water_availability,
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

    soil_changed = (
        payload.soil_type is not None and payload.soil_type != plot.soil_type
    ) or (
        payload.soil_category is not None and payload.soil_category != plot.soil_category
    )
    water_changed = payload.water_availability is not None and payload.water_availability != plot.water_availability

    if payload.plot_name is not None:
        plot.plot_name = payload.plot_name
    if payload.latitude is not None:
        plot.latitude = payload.latitude
    if payload.longitude is not None:
        plot.longitude = payload.longitude
    if payload.boundary_points is not None:
        plot.boundary_points = _serialize_boundary_points(payload.boundary_points)
    if payload.soil_type is not None:
        plot.soil_type = payload.soil_type
    if payload.irrigation_type is not None:
        plot.irrigation_type = payload.irrigation_type
    if payload.irrigation_source is not None:
        plot.irrigation_source = payload.irrigation_source
    if payload.soil_category is not None:
        plot.soil_category = payload.soil_category
    if payload.water_availability is not None:
        plot.water_availability = payload.water_availability

    if payload.area_value is not None or payload.area_unit is not None:
        new_value = payload.area_value if payload.area_value is not None else plot.area_value
        new_unit = payload.area_unit if payload.area_unit is not None else plot.area_unit
        plot.area_value = new_value
        plot.area_unit = new_unit
        plot.area_sqm = to_square_meters(new_value, new_unit)

    AuditLogger(db).log("PLOT_UPDATED", actor_id=farmer_id, actor_role="farmer", entity="plot", entity_id=str(plot.id))
    if soil_changed:
        _record_soil_history(db, plot.id, plot.soil_type, plot.soil_category)
    if water_changed:
        _record_water_history(db, plot.id, plot.water_availability)

    db.commit()
    db.refresh(plot)
    return PlotResponse.model_validate(plot)


def get_soil_history_for_plot(db: Session, farmer_id: str, plot_id: uuid.UUID) -> PlotSoilHistoryListResponse:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    items = plot_soil_history_repository.list_for_plot(db, plot_id)
    return PlotSoilHistoryListResponse(items=[PlotSoilHistoryResponse.model_validate(i) for i in items], total=len(items))


def get_water_history_for_plot(db: Session, farmer_id: str, plot_id: uuid.UUID) -> PlotWaterHistoryListResponse:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    items = plot_water_history_repository.list_for_plot(db, plot_id)
    return PlotWaterHistoryListResponse(items=[PlotWaterHistoryResponse.model_validate(i) for i in items], total=len(items))


def deactivate_my_plot(db: Session, farmer_id: str, plot_id: uuid.UUID) -> None:
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    plot.status = FarmStatus.INACTIVE  # soft delete - same reasoning as Farm

    AuditLogger(db).log("PLOT_DEACTIVATED", actor_id=farmer_id, actor_role="farmer", entity="plot", entity_id=str(plot.id))

    db.commit()
