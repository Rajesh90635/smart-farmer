from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dead_letter_report import DeadLetterReport


def create(db: Session, report: DeadLetterReport) -> DeadLetterReport:
    db.add(report)
    return report


def list_all(db: Session) -> list[DeadLetterReport]:
    return list(db.execute(select(DeadLetterReport).order_by(DeadLetterReport.reported_at.desc())).scalars().all())
