# Case Audit

## Reused infrastructure, not a new table

Per the explicit "do not create duplicate tables if equivalent structures
already exist" instruction, case auditing uses the EXISTING generic
`AuditLog` table (introduced in the foundation phase, Prompt 2) rather
than a new `CaseAudit` table. Every case-related audit row has
`entity='crop_health_case'` and `entity_id=<case_id>`, making
`GET /api/v1/cases/{id}/audit` a simple filtered query, not a new storage
mechanism.

## Events actually logged this phase

| Action | When |
|---|---|
| CASE_CREATED | Case creation |
| CASE_ASSIGNED | Auto-assignment succeeds |
| CASE_ASSIGNMENT_ACCEPTED | Professional accepts |
| CASE_ASSIGNMENT_DECLINED | Professional declines |
| CASE_REVIEW_SUBMITTED | Review submitted |
| CASE_CLOSED | Farmer closes the case |
| CASE_SECOND_OPINION_REQUESTED | Farmer requests a second opinion |
| CASE_PHOTO_ACCESSED | A professional fetches the authorized photo (see docs/PHOTO_SHARING_PRIVACY.md) |
| PROFESSIONAL_REGISTERED / PROFESSIONAL_VERIFY / PROFESSIONAL_REJECT / PROFESSIONAL_SUSPEND / PROFESSIONAL_REACTIVATE | Professional lifecycle events |

**Not yet logged as distinct events** (disclosed gap): `CASE_REASSIGNED`
as its own action name - a reassignment currently shows up as a second
`CASE_ASSIGNED` row, which is traceable (timestamps + the professional_id
on the resulting `CaseAssignment` distinguish it) but isn't labeled
`CASE_REASSIGNED` specifically.

## Immutability

`AuditLog` rows are append-only by convention (no service code updates or
deletes them) - the same guarantee already documented for every other use
of this table since the foundation phase. A DB-role-level `NO UPDATE/DELETE`
grant remains a pre-pilot hardening item (documented in `docs/SECURITY.md`
since the foundation phase, not newly introduced here).

## What is never logged

The actual image content, the farmer's phone number, or any other PII
beyond actor id/role and the entity being acted on - consistent with the
"do not log the actual image" and "do not log unnecessary personal data"
rules.
