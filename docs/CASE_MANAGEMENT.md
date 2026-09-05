# Case Management

## Entity: CropHealthCase

Connects Farmer -> Farm -> Plot -> CropCycle -> Photo -> AIAnalysis ->
Professional -> Verification. Only the 10 specified statuses exist (no
extras): open, waiting_for_assignment, assigned, in_review,
needs_more_information, verified, rejected, escalated, closed, cancelled.

## Creation triggers (4 implemented, per this phase's explicit scope)

`reason` on every case is one of: farmer_requested, ai_low_confidence,
ai_unknown, farmer_dispute. A case is never created without a traceable
reason.

## Lifecycle

```
Farmer creates case (with consent, in the SAME transaction)
   |
Auto-assignment attempted immediately (nearby_professional_service)
   |
   +-- Match found -> ASSIGNED, PhotoAccessGrant created, professional notified
   |
   +-- No match -> WAITING_FOR_ASSIGNMENT (never silently discarded)
   |
Professional ACCEPTS -> IN_REVIEW, farmer notified
   |
Professional DECLINES -> auto-reassignment attempted, excluding the
   |                      declining professional permanently for this case
   |
Professional submits review -> VERIFIED / NEEDS_MORE_INFORMATION / ESCALATED
   |
Farmer CLOSES -> CLOSED, photo access revoked, professional's
                 completed_case_count incremented
```

## Priority (business-rule-derived, not farmer-chosen)

| Reason | Priority |
|---|---|
| farmer_requested | MEDIUM |
| ai_low_confidence | MEDIUM |
| ai_unknown | LOW |
| farmer_dispute | HIGH |

URGENT is never assigned automatically this phase - no rule in this
codebase produces it, consistent with "do not allow every case to become
URGENT."

## Second opinion

Limited to 1 per case (_MAX_SECOND_OPINIONS in case_service.py),
configurable. Requesting one re-opens matching (WAITING_FOR_ASSIGNMENT)
and increments CropHealthCase.second_opinion_count. Verified by test that
a second request beyond the limit returns 409.

## Assignment timeout (Expert SLA sweep)

CaseAssignment.expires_at is set to 24 hours after assignment
(_ASSIGNMENT_TIMEOUT_HOURS, configurable). **This is now actively
enforced**, closing the previously-disclosed "no background job expires
stale PENDING assignments" gap: `app/services/scheduler.py` runs an
in-process APScheduler job (`case_sla_sweep_interval_seconds`, default
5 minutes; disabled in the `testing` environment) that calls
`app/services/case_sla_service.run_case_sla_sweep()`:

1. **Reminder** - a PENDING assignment within `case_sla_reminder_before_hours`
   (default 4h) of expiring sends the professional one reminder
   notification (`CASE_ASSIGNMENT_REMINDER`, HIGH priority; deduplicated
   per-assignment so it is sent exactly once).
2. **Expire** - a PENDING assignment past `expires_at` is marked EXPIRED
   and audit-logged (`CASE_ASSIGNMENT_EXPIRED`) - this is also the
   "professional unavailable" detection signal: a non-responsive
   professional is never re-offered the same case
   (`case_repository.get_excluded_professional_ids` already excludes
   EXPIRED, same mechanism as a DECLINE).
3. **Reassign** - if the case has had at most `case_sla_max_reassignment_attempts`
   (default 2) total EXPIRED assignments, the same `_try_auto_assign`
   used for decline-triggered reassignment re-runs, excluding every
   professional already tried; the farmer is notified (`CASE_REASSIGNED`).
4. **Escalate** - beyond that many timeouts with no professional ever
   accepting, the case moves to `ESCALATED` (`CASE_SLA_BREACH_ESCALATED`
   audit entry) and the farmer gets a CRITICAL-priority notification -
   the only place CRITICAL is currently used (see
   docs/NOTIFICATION_ARCHITECTURE.md).

Verified by `tests/test_case_sla_service.py` (reminder dedup, timeout
reassignment excluding the non-responder, breach escalation with a
CRITICAL notification, and that a farmer-closed case is never resurrected
by a late-expiring assignment).

## Audit trail: reused, not duplicated

GET /cases/{id}/audit queries the EXISTING generic AuditLog table
(Prompt 3) filtered to entity='crop_health_case' - no new CaseAudit table
was created, per the explicit "do not create duplicate tables if
equivalent structures already exist" instruction. Every lifecycle
transition (CASE_CREATED, CASE_ASSIGNED, CASE_ASSIGNMENT_ACCEPTED,
CASE_ASSIGNMENT_DECLINED, CASE_REVIEW_SUBMITTED, CASE_CLOSED,
CASE_SECOND_OPINION_REQUESTED) is logged there. Verified by test.

## Ownership

Every case/assignment/review lookup is scoped to the caller (farmer via
farmer_id, professional via an existing CaseAssignment row for that exact
case) - cross-farmer and cross-professional access both return 404,
verified by test.
