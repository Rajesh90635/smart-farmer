"""D2-07 (docs/audit/FINAL_CANONICAL_group_A.md): farmer-entered farm
infrastructure records, informational only - mirrors plot_service.py's
CRUD shape exactly. No automated logic reads these yet."""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.farm_infrastructure import FarmInfrastructure
from app.repositories import farm_infrastructure_repository, farm_repository
from app.schemas.farm_infrastructure import FarmInfrastructureCreateRequest, FarmInfrastructureListResponse, FarmInfrastructureResponse
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


def _get_owned_farm_or_404(db: Session, farmer_id: str, farm_id: uuid.UUID):
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)
    return farm


def create_infrastructure(
    db: Session, farmer_id: str, farm_id: uuid.UUID, payload: FarmInfrastructureCreateRequest
) -> FarmInfrastructureResponse:
    _get_owned_farm_or_404(db, farmer_id, farm_id)

    item = FarmInfrastructure(farm_id=farm_id, infrastructure_type=payload.infrastructure_type, description=payload.description)
    farm_infrastructure_repository.create(db, item)
    db.flush()

    AuditLogger(db).log("FARM_INFRASTRUCTURE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="farm_infrastructure", entity_id=str(item.id))
    db.commit()
    db.refresh(item)
    return FarmInfrastructureResponse.model_validate(item)


def list_infrastructure_for_farm(
    db: Session, farmer_id: str, farm_id: uuid.UUID, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0
) -> FarmInfrastructureListResponse:
    _get_owned_farm_or_404(db, farmer_id, farm_id)
    items, total = farm_infrastructure_repository.list_for_farm(db, farm_id, limit=limit, offset=offset)
    return FarmInfrastructureListResponse(items=[FarmInfrastructureResponse.model_validate(i) for i in items], total=total)


def delete_infrastructure(db: Session, farmer_id: str, farm_id: uuid.UUID, item_id: uuid.UUID) -> None:
    _get_owned_farm_or_404(db, farmer_id, farm_id)
    item = farm_infrastructure_repository.get_owned(db, item_id, farm_id)
    if item is None:
        raise AppError(error_codes.NOT_FOUND, "Farm infrastructure record not found.", 404)
    farm_infrastructure_repository.delete(db, item)
    AuditLogger(db).log("FARM_INFRASTRUCTURE_DELETED", actor_id=farmer_id, actor_role="farmer", entity="farm_infrastructure", entity_id=str(item_id))
    db.commit()
