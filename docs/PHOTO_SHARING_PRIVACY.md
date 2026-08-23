# Photo Sharing Privacy

## No copying, no public URLs

When a case is created and assigned, the professional is NOT given a
copy of the photo file - they're given a `PhotoAccessGrant` row
authorizing them to fetch it through the SAME authenticated
`GET /api/v1/crop-photos/{id}/file` endpoint farmers already use (Prompt
5), never a new parallel endpoint and never a public/bare URL.

## Authorization check (broadened, not duplicated)

`crop_photo_service.get_photo_for_serving_authorized` is the single
authorization function for this endpoint now:
1. If the caller is a FARMER -> the existing farmer-ownership check
   (unchanged since Prompt 5).
2. If the caller is a FIELD_AGENT or EXPERT -> look up their
   ProfessionalProfile, then check for an active (non-expired,
   non-revoked) `PhotoAccessGrant` for this exact photo.
3. Otherwise -> `404` (same ID-enumeration defense used everywhere else
   in this codebase - "not authorized" and "doesn't exist" look
   identical).

Verified by test: an expert WITH a valid grant can fetch the photo; a
DIFFERENT expert with no grant at all (holding a valid EXPERT-role token)
cannot.

## Grant lifecycle

- **Created**: automatically, at the moment a case is auto-assigned to a
  professional (if the case references a `crop_photo_id`) - tied to the
  same expiry as the assignment (24h timeout).
- **Revoked**: automatically, when the farmer closes the case
  (`case_repository.revoke_grants_for_case`). Verified by test that
  access is denied immediately after close.
- **Never deleted**: revocation sets `revoked_at`, the row itself remains
  for accountability (see docs/CASE_AUDIT.md).

## Consent - before ANY sharing

`CaseConsent` is created in the SAME database transaction as the case
itself (`case_service.create_case`) - there is no code path that creates
a case without a consent record. `shared_items` is an explicit list
(e.g. `["crop_photo", "ai_result", "crop_stage"]`), never a blanket
"share everything" flag. Consent withdrawal (`withdrawn_at`) is modeled
but no endpoint currently exposes withdrawing consent for an
already-created case - a disclosed gap, not silently unsupported forever
(the field exists specifically so a future endpoint can set it without a
schema change).

## What is shared vs. never shared

| Shared with an assigned professional | Never shared |
|---|---|
| The specific crop photo (via authorized, expiring access) | The farmer's precise farm GPS coordinates |
| AI result (if the farmer consented to share it) | Any other crop's photos or cases |
| Crop name, crop stage (farmer-confirmed) | Payment/financial information (none exists yet) |
| Farmer's preferred language (for notification localization) | The farmer's phone number or other account identity fields |

## Photo access audit

Every actual photo fetch by a professional logs a `CASE_PHOTO_ACCESSED`
row to the existing generic `AuditLog` (who, when, case id) - never the
image content itself. Verified by test.
