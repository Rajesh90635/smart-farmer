"""
Authentication endpoints: register, login, refresh, logout, change-password,
reset-password.

Password-based auth (phone number + password) was chosen for this phase
instead of an app-wide OTP-only login, specifically to avoid requiring a
paid SMS provider for every login - consistent with the free-first
constraint. /reset-password/request-otp and /reset-password DO now use a
real SMS OTP provider (see app/services/sms/) specifically to verify the
caller owns the phone number before a password reset is allowed - this was
previously a deliberately-accepted gap (see docs/SECURITY.md's history)
and is closed as of this phase, gated on Settings.sms_provider actually
being configured (falls back to refusing every reset otherwise - see
NotConfiguredSmsOtpProvider - never to the old no-verification behavior).
"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, get_current_user
from app.core.sms_provider_dependency import get_sms_provider
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RequestPasswordResetOtpRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import auth_service
from app.services.sms.sms_otp_provider import SmsOtpProvider

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login(db, payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.refresh(db, payload)


@router.post("/reset-password/request-otp", status_code=status.HTTP_204_NO_CONTENT)
def request_reset_password_otp(
    payload: RequestPasswordResetOtpRequest,
    sms_provider: SmsOtpProvider = Depends(get_sms_provider),
    db: Session = Depends(get_db),
) -> Response:
    auth_service.request_password_reset_otp(db, sms_provider, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", response_model=TokenResponse)
def reset_password(
    payload: ResetPasswordRequest,
    sms_provider: SmsOtpProvider = Depends(get_sms_provider),
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_service.reset_password(db, sms_provider, payload)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    auth_service.change_password(db, current_user, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    auth_service.logout(db, current_user, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
