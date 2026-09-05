"""
Expert SLA automation - the concrete implementation of the long-disclosed
"no background job actually expires stale PENDING assignments yet"
limitation (docs/CASE_MANAGEMENT.md's old "Assignment timeout" section)
and its direct consequences:

- D35-02 SLA monitoring: `_ASSIGNMENT_TIMEOUT_HOURS` on CaseAssignment.expires_at
  now actually gets read by something.
- D35-03 Reminder: a professional close to timing out gets one reminder.
- D34-03 Timeout-triggered reassignment: an expired assignment re-invokes
  the same `_try_auto_assign` used for decline-triggered reassignment
  (case_service.py) - excluding the non-responsive professional (already
  enforced by case_repository.get_excluded_professional_ids including
  EXPIRED).
- D35-04 Escalation on breach: after `case_sla_max_reassignment_attempts`
  timeouts with no professional ever accepting, the case is escalated
  (CaseStatus.ESCALATED) rather than looping forever.
- D35-05 Expert unavailable: a professional who never responds before
  expires_at is the detection signal for "unavailable" this phase - no
  separate long-lived availability flag is flipped on ProfessionalProfile
  (a farmer-invisible, professional-facing side effect would itself need
  its own confirmation/appeal path - out of scope for this pass); the
  case-level exclusion is what actually matters for the farmer's outcome.

Every function here takes its OWN Session - callers (the scheduler, or a
test) are responsible for the session lifecycle, exactly like every other
service function in this codebase.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.case_assignment import AssignmentStatus
from app.models.crop_health_case import CaseStatus
from app.models.notification import NotificationCategory, NotificationPriority
from app.repositories import case_repository, professional_repository
from app.services import case_service, notification_service
from app.services.audit_logger import AuditLogger
from app.services.weather_alert_rules import AlertCandidate

logger = logging.getLogger(__name__)


@dataclass
class CaseSlaSweepResult:
    reminders_sent: int = 0
    expired: int = 0
    reassigned: int = 0
    escalated: int = 0
    case_ids_escalated: list = field(default_factory=list)


def run_case_sla_sweep(db: Session, settings: Settings) -> CaseSlaSweepResult:
    """Entry point called on every scheduler tick (app/services/scheduler.py)
    and directly from tests. A failure processing one assignment/case is
    logged and skipped (see the per-row try/except below) rather than
    aborting the whole sweep - one stuck case must never block SLA
    handling for every other case."""
    result = CaseSlaSweepResult()
    now = datetime.now(timezone.utc)

    _send_expiry_reminders(db, settings, now, result)
    _expire_reassign_or_escalate(db, settings, now, result)

    return result


def _send_expiry_reminders(db: Session, settings: Settings, now: datetime, result: CaseSlaSweepResult) -> None:
    reminder_cutoff = now + timedelta(hours=settings.case_sla_reminder_before_hours)
    pending = case_repository.get_pending_assignments_in_expiry_window(
        db, expires_before=reminder_cutoff, expires_after=now
    )

    for assignment in pending:
        try:
            professional = professional_repository.get_by_id(db, assignment.professional_id)
            if professional is None:
                continue

            candidate = AlertCandidate(
                category=NotificationCategory.CROP_ALERT,
                priority=NotificationPriority.HIGH,
                message_key="CASE_ASSIGNMENT_REMINDER",
                message_params={},
                dedup_suffix=f"assignment_reminder:{assignment.id}",
            )
            created = notification_service.create_alert_notification(
                db, str(professional.user_id), candidate,
                dedup_scope=f"case:{assignment.case_id}", language_code="en",
                related_entity_type="crop_health_case", related_entity_id=str(assignment.case_id),
            )
            if created is not None:
                result.reminders_sent += 1
        except Exception:
            logger.exception("case_sla_sweep: reminder failed for assignment %s", assignment.id)
            db.rollback()


def _expire_reassign_or_escalate(db: Session, settings: Settings, now: datetime, result: CaseSlaSweepResult) -> None:
    past_due = case_repository.get_pending_assignments_in_expiry_window(db, expires_before=now)

    for assignment in past_due:
        try:
            case = case_repository.get_case_by_id(db, assignment.case_id)
            if case is None or case.status in (CaseStatus.CLOSED, CaseStatus.CANCELLED):
                # Case was already closed/cancelled by the farmer through
                # some other path while this assignment sat PENDING -
                # nothing left to expire it into.
                continue

            assignment.status = AssignmentStatus.EXPIRED
            AuditLogger(db).log(
                "CASE_ASSIGNMENT_EXPIRED", actor_id=None, actor_role="scheduler",
                entity="crop_health_case", entity_id=str(case.id),
            )
            db.commit()
            result.expired += 1

            timeout_count = case_repository.count_expired_assignments_for_case(db, case.id)

            if timeout_count > settings.case_sla_max_reassignment_attempts:
                if case.status != CaseStatus.ESCALATED:
                    case.status = CaseStatus.ESCALATED
                    AuditLogger(db).log(
                        "CASE_SLA_BREACH_ESCALATED", actor_id=None, actor_role="scheduler",
                        entity="crop_health_case", entity_id=str(case.id),
                    )
                    db.commit()
                    case_service._notify_case_event(
                        db, case, "CASE_ESCALATED", farmer_id=case.farmer_id,
                        priority=NotificationPriority.CRITICAL,
                        dedup_suffix=f"sla_breach_escalation:{case.id}",
                    )
                    result.escalated += 1
                    result.case_ids_escalated.append(str(case.id))
                continue

            new_assignment = case_service._try_auto_assign(db, case, settings)
            if new_assignment is not None:
                result.reassigned += 1
                case_service._notify_case_event(
                    db, case, "CASE_REASSIGNED", farmer_id=case.farmer_id,
                    dedup_suffix=f"CASE_REASSIGNED:{new_assignment.id}",
                )
        except Exception:
            logger.exception("case_sla_sweep: expiry/reassignment failed for assignment %s", assignment.id)
            db.rollback()
