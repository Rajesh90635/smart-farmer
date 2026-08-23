from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.repositories import location_repository
from app.schemas.location import DistrictResponse, MandalResponse, StateResponse, VillageResponse


def list_states(db: Session) -> list[StateResponse]:
    return [StateResponse.model_validate(s) for s in location_repository.list_states(db)]


def list_districts_for_state(db: Session, state_id: int) -> list[DistrictResponse]:
    if location_repository.get_state(db, state_id) is None:
        raise AppError(error_codes.NOT_FOUND, "State not found.", 404)
    return [DistrictResponse.model_validate(d) for d in location_repository.list_districts_for_state(db, state_id)]


def list_mandals_for_district(db: Session, district_id: int) -> list[MandalResponse]:
    if location_repository.get_district(db, district_id) is None:
        raise AppError(error_codes.NOT_FOUND, "District not found.", 404)
    return [MandalResponse.model_validate(m) for m in location_repository.list_mandals_for_district(db, district_id)]


def list_villages_for_mandal(db: Session, mandal_id: int) -> list[VillageResponse]:
    if location_repository.get_mandal(db, mandal_id) is None:
        raise AppError(error_codes.NOT_FOUND, "Mandal not found.", 404)
    return [VillageResponse.model_validate(v) for v in location_repository.list_villages_for_mandal(db, mandal_id)]


def validate_farm_location(
    db: Session,
    *,
    state_id: int | None,
    district_id: int | None,
    mandal_id: int | None,
    village_id: int | None,
) -> None:
    """Every provided id must exist, and every provided child must belong
    to its provided parent - a farmer (or a stale client) picking a
    mismatched combination is rejected rather than silently stored, since
    a wrong district/mandal/village would misinform every downstream
    feature (weather-by-location, nearby professionals, etc). A farmer is
    free to stop partway down the hierarchy (e.g. state+district only,
    since mandal/village have no seed data yet) - only actually-supplied
    parent/child pairs are cross-checked.
    """
    village = None
    if village_id is not None:
        village = location_repository.get_village(db, village_id)
        if village is None:
            raise AppError(error_codes.VALIDATION_ERROR, "Village not found.", 400)

    mandal = None
    if mandal_id is not None:
        mandal = location_repository.get_mandal(db, mandal_id)
        if mandal is None:
            raise AppError(error_codes.VALIDATION_ERROR, "Mandal not found.", 400)
    if village is not None and mandal_id is not None and village.mandal_id != mandal_id:
        raise AppError(error_codes.VALIDATION_ERROR, "Village does not belong to the given mandal.", 400)
    if mandal is None and village is not None:
        mandal_id = village.mandal_id
        mandal = location_repository.get_mandal(db, mandal_id)

    district = None
    if district_id is not None:
        district = location_repository.get_district(db, district_id)
        if district is None:
            raise AppError(error_codes.VALIDATION_ERROR, "District not found.", 400)
    if mandal is not None and district_id is not None and mandal.district_id != district_id:
        raise AppError(error_codes.VALIDATION_ERROR, "Mandal does not belong to the given district.", 400)
    if district is None and mandal is not None:
        district_id = mandal.district_id
        district = location_repository.get_district(db, district_id)

    if state_id is not None and location_repository.get_state(db, state_id) is None:
        raise AppError(error_codes.VALIDATION_ERROR, "State not found.", 400)
    if district is not None and state_id is not None and district.state_id != state_id:
        raise AppError(error_codes.VALIDATION_ERROR, "District does not belong to the given state.", 400)
