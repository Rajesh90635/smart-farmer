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

## Assignment timeout

CaseAssignment.expires_at is set to 24 hours after assignment
(_ASSIGNMENT_TIMEOUT_HOURS, configurable) - the field exists and is
populated, but no background job actually expires stale PENDING
assignments yet (disclosed limitation, consistent with this project's
repeated "no background scheduler yet" pattern from the Weather phase). A
professional who never responds will show as PENDING indefinitely until
either they act or an admin intervenes - automatic timeout-driven
reassignment is future work using the same _try_auto_assign function.

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
