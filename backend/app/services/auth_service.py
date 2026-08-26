from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import get_settings
from app.core.current_user import CurrentUser
from app.core.errors import AppError
from app.core.jwt import create_access_token
from app.core.refresh_tokens import generate_refresh_token, hash_refresh_token
from app.core.roles import Role as RoleCode
from app.core.security_passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.middleware.rate_limit import InMemoryRateLimiter
from app.models.consent_record import REQUIRED_CONSENTS_AT_REGISTRATION, ConsentRecord, ConsentStatus
from app.models.farmer_profile import FarmerProfile
from app.models.user import AccountStatus, User
from app.repositories import refresh_token_repository, user_repository
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.audit_logger import AuditLogger

settings = get_settings()

# Single-process login-attempt limiter, per phone number. See
# app/middleware/rate_limit.py's docstring for why this is explicitly not
# sufficient once the API runs as more than one process.
_login_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=300)


def _resolve_role(db: Session, user_id) -> str:
    """The JWT/audit `role` claim must reflect the role actually assigned
    in `user_roles`, not an assumption - this is what makes non-farmer
    logins (admin, expert, dealer, ...) authenticate as themselves rather
    than silently appearing as a farmer. A user with more than one role
    is treated as admin if admin is among them (the higher-privilege
    claim), otherwise the first assigned role - today every account has
    exactly one role, so this is not yet exercised by multi-role users."""
    role_codes = user_repository.get_role_codes_for_user(db, user_id)
    if RoleCode.ADMIN.value in role_codes:
        return RoleCode.ADMIN.value
    if role_codes:
        return role_codes[0]
    raise AppError("ROLE_NOT_ASSIGNED", "This account has no assigned role.", 500)


def _issue_tokens(db: Session, user: User, role: str) -> TokenResponse:
    access_token = create_access_token(subject=str(user.id), role=role)

    raw_refresh = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_days)
    refresh_token_repository.create(
        db, user_id=user.id, token_hash=hash_refresh_token(raw_refresh), expires_at=expires_at
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.jwt_access_token_minutes * 60,
    )


def register(db: Session, payload: RegisterRequest) -> TokenResponse:
    if user_repository.get_by_phone(db, payload.phone_number) is not None:
        raise AppError(error_codes.DUPLICATE_ACCOUNT, "An account with this phone number already exists.", 409)

    submitted_types = {c.consent_type for c in payload.consents}
    missing = [c.value for c in REQUIRED_CONSENTS_AT_REGISTRATION if c not in submitted_types]
    if missing:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            f"The following consents are required to register: {', '.join(missing)}",
            422,
        )

    user = User(
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        status=AccountStatus.ACTIVE,
    )
    db.add(user)
    db.flush()  # populate user.id before it's referenced below

    db.add(
        FarmerProfile(
            user_id=user.id,
            full_name=payload.full_name,
            preferred_language_code=payload.preferred_language_code,
            preferred_voice_language_code=payload.preferred_voice_language_code or payload.preferred_language_code,
        )
    )

    farmer_role = user_repository.get_role_by_code(db, RoleCode.FARMER.value)
    if farmer_role is None:
        # Should be impossible outside a broken/unmigrated database - fail
        # loudly rather than silently registering a user with no role.
        raise AppError("ROLE_NOT_SEEDED", "The 'farmer' role is not seeded in this environment.", 500)
    user_repository.assign_role(db, user.id, farmer_role.id)

    for consent in payload.consents:
        db.add(
            ConsentRecord(
                user_id=user.id,
                consent_type=consent.consent_type,
                version=consent.version,
                status=ConsentStatus.ACCEPTED,
            )
        )

    tokens = _issue_tokens(db, user, RoleCode.FARMER.value)

    AuditLogger(db).log(
        "USER_REGISTERED", actor_id=str(user.id), actor_role=RoleCode.FARMER.value, entity="user", entity_id=str(user.id)
    )

    db.commit()
    return tokens


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    if not _login_limiter.allow(payload.phone_number):
        raise AppError(error_codes.RATE_LIMITED, "Too many login attempts. Please try again later.", 429)

    user = user_repository.get_by_phone(db, payload.phone_number)

    # Always run a real bcrypt verify, even when the account doesn't exist,
    # so response timing doesn't reveal account existence.
    password_hash_to_check = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash_to_check)

    if user is None or not password_ok:
        AuditLogger(db).log(
            "LOGIN_FAILED",
            entity="user",
            entity_id=str(user.id) if user else None,
        )
        db.commit()
        raise AppError(error_codes.INVALID_CREDENTIALS, "Invalid phone number or password.", 401)

    if user.status != AccountStatus.ACTIVE:
        AuditLogger(db).log("LOGIN_FAILED", actor_id=str(user.id), entity="user", entity_id=str(user.id))
        db.commit()
        raise AppError(error_codes.ACCOUNT_DISABLED, "This account is not active.", 403)

    role = _resolve_role(db, user.id)

    user.last_login_at = datetime.now(timezone.utc)
    tokens = _issue_tokens(db, user, role)

    AuditLogger(db).log(
        "LOGIN_SUCCESS", actor_id=str(user.id), actor_role=role, entity="user", entity_id=str(user.id)
    )

    db.commit()
    return tokens


def refresh(db: Session, payload: RefreshRequest) -> TokenResponse:
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = refresh_token_repository.get_by_hash(db, token_hash)

    now = datetime.now(timezone.utc)
    if stored is None or not stored.is_active(now):
        raise AppError(error_codes.SESSION_EXPIRED, "Session has expired or been revoked. Please log in again.", 401)

    user = user_repository.get_by_id(db, stored.user_id)
    if user is None or user.status != AccountStatus.ACTIVE:
        raise AppError(error_codes.ACCOUNT_DISABLED, "This account is not active.", 403)

    # Rotate: revoke the used refresh token, issue a fresh pair. Reduces the
    # blast radius if a refresh token is ever intercepted and replayed.
    role = _resolve_role(db, user.id)

    refresh_token_repository.revoke(db, stored)
    tokens = _issue_tokens(db, user, role)

    AuditLogger(db).log(
        "TOKEN_REFRESHED", actor_id=str(user.id), actor_role=role, entity="user", entity_id=str(user.id)
    )

    db.commit()
    return tokens


def logout(db: Session, current_user: CurrentUser, payload: LogoutRequest) -> None:
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = refresh_token_repository.get_by_hash(db, token_hash)

    if stored is None or str(stored.user_id) != current_user.user_id:
        # Don't reveal whether the token exists at all if it doesn't belong
        # to the caller - just treat it as already logged out.
        raise AppError(error_codes.INVALID_TOKEN, "Invalid session token.", 401)

    refresh_token_repository.revoke(db, stored)

    AuditLogger(db).log(
        "LOGOUT", actor_id=current_user.user_id, actor_role=current_user.role, entity="user", entity_id=current_user.user_id
    )

    db.commit()
