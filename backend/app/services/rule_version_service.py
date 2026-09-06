"""
D89-03 (docs/audit/FINAL_CANONICAL_group_D.md): effective-dated history of
a rule module's real threshold values. `record_snapshot_if_changed` is the
write path (called from the orchestration layer that already evaluates a
rule against live Settings, never from the rule's own pure functions -
those stay DB-free by design); `get_thresholds_effective_at` is the
reproducibility read path.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.rule_version_snapshot import RuleVersionSnapshot
from app.repositories import rule_version_repository


def record_snapshot_if_changed(db: Session, rule_id: str, version: str, threshold_values: dict) -> RuleVersionSnapshot:
    """Idempotent: called on every rule evaluation, but only ever writes
    when the real threshold values actually differ from the currently
    open snapshot - a normal request where Settings hasn't changed since
    the last call is a single SELECT, no write."""
    now = datetime.now(timezone.utc)
    current = rule_version_repository.get_open_snapshot(db, rule_id)
    if current is not None and current.version == version and current.threshold_values == threshold_values:
        return current

    if current is not None:
        current.effective_to = now

    snapshot = RuleVersionSnapshot(rule_id=rule_id, version=version, threshold_values=threshold_values, effective_from=now, effective_to=None)
    rule_version_repository.create(db, snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_thresholds_effective_at(db: Session, rule_id: str, at: datetime) -> RuleVersionSnapshot | None:
    return rule_version_repository.get_effective_at(db, rule_id, at)
