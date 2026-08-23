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
