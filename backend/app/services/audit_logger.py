"""
Audit logging service.

Deliberately does NOT commit on its own. The calling business module adds
an audit row to the same SQLAlchemy session as its business write and
commits once — an audit entry that could be lost independently of the
action it records defeats the purpose of an audit trail.
"""
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogger:
    def __init__(self, db: Session):
        self._db = db

    def log(
        self,
        action: str,
        *,
        actor_id: str | None = None,
        actor_role: str | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity=entity,
            entity_id=entity_id,
        )
        self._db.add(entry)
        return entry
