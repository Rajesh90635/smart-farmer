import uuid

from sqlalchemy.orm import Session

from app.models.consent_record import ConsentRecord
from app.repositories import consent_repository
from app.schemas.consent import ConsentRecordResponse, ConsentUpsertRequest
from app.services.audit_logger import AuditLogger


def list_consents(db: Session, user_id: str) -> list[ConsentRecordResponse]:
    records = consent_repository.list_for_user(db, uuid.UUID(user_id))
    return [ConsentRecordResponse.model_validate(r) for r in records]


def upsert_consent(db: Session, user_id: str, payload: ConsentUpsertRequest) -> ConsentRecordResponse:
    record = ConsentRecord(
        user_id=uuid.UUID(user_id),
        consent_type=payload.consent_type,
        version=payload.version,
        status=payload.status,
    )
    consent_repository.create(db, record)

    action = "CONSENT_ACCEPTED" if payload.status.value == "accepted" else "CONSENT_REVOKED"
    AuditLogger(db).log(action, actor_id=user_id, actor_role="farmer", entity="consent", entity_id=payload.consent_type.value)

    db.commit()
    db.refresh(record)
    return ConsentRecordResponse.model_validate(record)
