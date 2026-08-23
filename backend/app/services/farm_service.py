import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.area_units import to_square_meters
from app.core.errors import AppError
from app.models.farm import Farm, FarmStatus
from app.repositories import farm_repository
from app.schemas.farm import FarmCreateRequest, FarmListResponse, FarmResponse, FarmUpdateRequest
from app.services import location_service
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


def create_farm(db: Session, farmer_id: str, payload: FarmCreateRequest) -> FarmResponse:
    location_service.validate_farm_location(
        db,
        state_id=payload.state_id,
        district_id=payload.district_id,
        mandal_id=payload.mandal_id,
        village_id=payload.village_id,
    )

    farm = Farm(
        farmer_id=uuid.UUID(farmer_id),
        farm_name=payload.farm_name,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        state_id=payload.state_id,
        district_id=payload.district_id,
        mandal_id=payload.mandal_id,
        village_id=payload.village_id,
        area_value=payload.area_value,
        area_unit=payload.area_unit,
        area_sqm=to_square_meters(payload.area_value, payload.area_unit),
    )
    farm_repository.create(db, farm)
    db.flush()

    AuditLogger(db).log("FARM_CREATED", actor_id=farmer_id, actor_role="farmer", entity="farm", entity_id=str(farm.id))

    db.commit()
    db.refresh(farm)
    return FarmResponse.from_orm_farm(farm)


def list_my_farms(db: Session, farmer_id: str, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0) -> FarmListResponse:
    farms, total = farm_repository.list_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return FarmListResponse(items=[FarmResponse.from_orm_farm(f) for f in farms], total=total)


def get_my_farm(db: Session, farmer_id: str, farm_id: uuid.UUID) -> FarmResponse:
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        # 404, not 403: per the ownership-security requirement, a farm
        # that exists but isn't yours must look identical to a farm that
        # doesn't exist at all - this is what actually prevents ID
        # enumeration, not just a policy statement.
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)
    return FarmResponse.from_orm_farm(farm)


def update_my_farm(db: Session, farmer_id: str, farm_id: uuid.UUID, payload: FarmUpdateRequest) -> FarmResponse:
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)

    if payload.farm_name is not None:
        farm.farm_name = payload.farm_name
    if payload.description is not None:
        farm.description = payload.description
    if payload.latitude is not None:
        farm.latitude = payload.latitude
    if payload.longitude is not None:
        farm.longitude = payload.longitude

    if (
        payload.state_id is not None
        or payload.district_id is not None
        or payload.mandal_id is not None
        or payload.village_id is not None
    ):
        # Merge onto the farm's existing chain before validating, so
        # updating just one level (e.g. only village_id) is still checked
        # for consistency against the levels already stored, not just the
        # levels present in this particular request.
        new_state_id = payload.state_id if payload.state_id is not None else farm.state_id
        new_district_id = payload.district_id if payload.district_id is not None else farm.district_id
        new_mandal_id = payload.mandal_id if payload.mandal_id is not None else farm.mandal_id
        new_village_id = payload.village_id if payload.village_id is not None else farm.village_id
        location_service.validate_farm_location(
            db,
            state_id=new_state_id,
            district_id=new_district_id,
            mandal_id=new_mandal_id,
            village_id=new_village_id,
        )
        farm.state_id = new_state_id
        farm.district_id = new_district_id
        farm.mandal_id = new_mandal_id
        farm.village_id = new_village_id

    # Area value and unit must be updated together so area_sqm never gets
    # derived from a mismatched (old_value, new_unit) or (new_value, old_unit) pair.
    if payload.area_value is not None or payload.area_unit is not None:
        new_value = payload.area_value if payload.area_value is not None else farm.area_value
        new_unit = payload.area_unit if payload.area_unit is not None else farm.area_unit
        farm.area_value = new_value
        farm.area_unit = new_unit
        farm.area_sqm = to_square_meters(new_value, new_unit)

    AuditLogger(db).log("FARM_UPDATED", actor_id=farmer_id, actor_role="farmer", entity="farm", entity_id=str(farm.id))

    db.commit()
    db.refresh(farm)
    return FarmResponse.from_orm_farm(farm)


def deactivate_my_farm(db: Session, farmer_id: str, farm_id: uuid.UUID) -> None:
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)

    # Soft delete only - a hard DELETE would orphan or cascade-destroy
    # historical plot/crop-cycle data, which the approved architecture
    # explicitly requires to be retained (crop history persists across
    # seasons). Deactivated farms are excluded from list_for_farmer but
    # remain fully queryable by anyone who already has the id (i.e. the
    # owning farmer) for historical reference.
    farm.status = FarmStatus.INACTIVE

    AuditLogger(db).log("FARM_DEACTIVATED", actor_id=farmer_id, actor_role="farmer", entity="farm", entity_id=str(farm.id))

    db.commit()
