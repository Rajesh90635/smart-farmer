"""
Farmer profile endpoints. Every route here operates on the CALLER's own
profile only (via the JWT subject) - there is deliberately no
GET /farmers/{id} route in this phase, which is what makes "attempt to
access another farmer's profile" structurally impossible rather than
merely checked for (see tests/test_farmer_profile.py).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.consent import ConsentRecordResponse, ConsentUpsertRequest
from app.schemas.dashboard import FarmerDashboardResponse
from app.schemas.farmer import FarmerProfileResponse, FarmerProfileUpdateRequest
from app.services import consent_service, dashboard_service, data_privacy_service, farmer_service

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.get("/me", response_model=FarmerProfileResponse)
def get_me(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmerProfileResponse:
    return farmer_service.get_profile(db, current_user.user_id)


@router.put("/me", response_model=FarmerProfileResponse)
def update_me(
    payload: FarmerProfileUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmerProfileResponse:
    return farmer_service.update_profile(db, current_user.user_id, payload)


@router.get("/me/consents", response_model=list[ConsentRecordResponse])
def get_my_consents(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[ConsentRecordResponse]:
    return consent_service.list_consents(db, current_user.user_id)


@router.post("/me/consents", response_model=ConsentRecordResponse, status_code=201)
def upsert_my_consent(
    payload: ConsentUpsertRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ConsentRecordResponse:
    return consent_service.upsert_consent(db, current_user.user_id, payload)


@router.get("/me/dashboard", response_model=FarmerDashboardResponse)
def get_my_dashboard(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmerDashboardResponse:
    """Farm/plot/crop summary only - no disease, weather, or market data
    yet, per this phase's explicit scope limit (see PROJECT_STATUS.md)."""
    return dashboard_service.get_dashboard(db, current_user.user_id)


@router.get("/me/data-export")
def export_my_data(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> dict:
    """D100-09: see app/services/data_privacy_service.py's module
    docstring for exactly what is and isn't included - a good-faith MVP
    scope, not a certified compliance export."""
    return data_privacy_service.export_my_data(db, current_user.user_id)


@router.post("/me/delete-account", status_code=204)
def delete_my_account(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    """D100-09: deactivates the account and scrubs direct PII (phone,
    email, name); does NOT hard-delete farms/orders/sales/notifications -
    see app/services/data_privacy_service.py's module docstring for the
    full retention rationale."""
    data_privacy_service.request_account_deletion(db, current_user.user_id)
