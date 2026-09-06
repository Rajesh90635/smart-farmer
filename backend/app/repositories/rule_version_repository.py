from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule_version_snapshot import RuleVersionSnapshot


def get_open_snapshot(db: Session, rule_id: str) -> RuleVersionSnapshot | None:
    return db.execute(
        select(RuleVersionSnapshot).where(RuleVersionSnapshot.rule_id == rule_id, RuleVersionSnapshot.effective_to.is_(None))
    ).scalar_one_or_none()


def get_effective_at(db: Session, rule_id: str, at: datetime) -> RuleVersionSnapshot | None:
    """D89-03: the historical-reproducibility lookup - the one snapshot
    whose effective window covers `at`, open-ended windows included."""
    return db.execute(
        select(RuleVersionSnapshot)
        .where(
            RuleVersionSnapshot.rule_id == rule_id,
            RuleVersionSnapshot.effective_from <= at,
            (RuleVersionSnapshot.effective_to.is_(None)) | (RuleVersionSnapshot.effective_to > at),
        )
        .order_by(RuleVersionSnapshot.effective_from.desc())
        .limit(1)
    ).scalar_one_or_none()


def create(db: Session, snapshot: RuleVersionSnapshot) -> RuleVersionSnapshot:
    db.add(snapshot)
    return snapshot
