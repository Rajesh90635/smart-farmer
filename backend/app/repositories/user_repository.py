import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.phone_utils import normalize_phone_number
from app.models.role import Role, UserRole
from app.models.user import User


def get_by_phone(db: Session, phone_number: str) -> User | None:
    """Normalizes BEFORE querying (see app/core/phone_utils.py) - this is
    the single choke point that makes every caller (registration's
    duplicate-account check, login's lookup, and any future caller)
    correctly find a user regardless of which accepted phone format was
    supplied, without each caller needing to remember to normalize
    first. A value that fails to normalize (genuinely malformed input,
    not just a differently-formatted valid number) is treated the same
    as "no such user" - a lookup function should never raise for a bad
    key, only return no result, so callers' existing not-found/invalid-
    credentials handling is preserved unchanged."""
    try:
        canonical = normalize_phone_number(phone_number)
    except ValueError:
        return None
    return db.execute(select(User).where(User.phone_number == canonical)).scalar_one_or_none()


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_role_by_code(db: Session, code: str) -> Role | None:
    return db.execute(select(Role).where(Role.code == code)).scalar_one_or_none()


def assign_role(db: Session, user_id: uuid.UUID, role_id: int) -> UserRole:
    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    return user_role


def get_role_codes_for_user(db: Session, user_id: uuid.UUID) -> list[str]:
    rows = db.execute(
        select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
    ).all()
    return [r[0] for r in rows]
