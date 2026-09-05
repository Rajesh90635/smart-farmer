import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create(db: Session, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    return token


def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).scalar_one_or_none()


def revoke(db: Session, token: RefreshToken) -> None:
    token.revoked_at = datetime.now(timezone.utc)


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> int:
    """D100-09: used by account deletion - logs the farmer out of every
    session/device at once. Returns the count revoked."""
    now = datetime.now(timezone.utc)
    tokens = db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
    ).scalars().all()
    for token in tokens:
        token.revoked_at = now
    return len(tokens)
