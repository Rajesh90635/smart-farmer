# Crop Photo Module

## Hierarchy

Every photo belongs to Farmer → Farm → Plot → CropCycle → **CropPhotoSession**
→ **CropPhoto**. Never stored against a farmer without crop context.

## Why a session exists

A single "crop check" often needs several photos (whole-plant, affected
leaf, close-up, stem). `CropPhotoSession` groups them. No AI aggregation
across a session's photos is implemented yet — that's the future disease-
detection phase's job; this phase only supports Crop → Photo Session →
Photos → Upload.

## Data model

**CropPhotoSession**: `id`, `crop_cycle_id` (FK), `farmer_id` (denormalized),
`label` (nullable), timestamps.

**CropPhoto**:

| Field | Notes |
|---|---|
| session_id, crop_cycle_id, plot_id, farm_id, farmer_id | All FKs, all set **server-side** from the validated ownership chain — never from client input. This table uniquely denormalizes the full chain (unlike Plot/CropCycle) because this prompt's spec explicitly required farmer_id-indexed ownership checks and the listed index set. |
| client_upload_id | Farmer-generated idempotency key — see "Idempotency" below |
| storage_key, thumbnail_storage_key | Returned by `FileStorage.save()` — never pre-computed and assumed (see docs/IMAGE_STORAGE.md for a bug this caused) |
| original_filename | Sanitized for **display only** — never used to build a path |
| mime_type, file_size_bytes, width_px, height_px | Of the **stored** (processed) image, not the original upload |
| capture_timestamp | Nullable — not populated this phase (see Limitations) |
| latitude, longitude | Only populated with explicit per-photo consent (`share_location=true`) — never read silently from EXIF |
| source | camera / gallery |
| upload_status | uploaded / failed / ready / deleted |
| image_quality_status | pending / accepted / rejected — independent of upload_status |
| quality_reasons | e.g. "too_dark,too_blurry" — technical only, never a disease term |

**Deliberately not added:** a separate `processing_status` field. All
processing is synchronous this phase, so it would just duplicate
`upload_status` — revisit if processing moves to a background queue.

## Storage decision

Only the **processed** image (EXIF-stripped, orientation-normalized,
compressed, capped at `photo_max_dimension_px`) is persisted, plus one
thumbnail. The original upload bytes are held in memory only long enough
to validate and process, never separately stored — avoids duplicate files
while keeping enough quality for future AI analysis.

## Idempotency

`client_upload_id` is a farmer-device-generated key sent with every
upload, including retries. A DB **unique constraint** on
`(session_id, client_upload_id)` — not just application logic — guarantees
a retried upload after a network failure returns the existing photo record
rather than creating a duplicate. Verified by
`test_retry_with_same_client_upload_id_does_not_duplicate`.

## Deletion policy: soft delete

`DELETE /crop-photos/{id}` sets `upload_status = deleted`. The row and
underlying files are left intact. A hard delete could silently break a
future AI analysis or expert review that already referenced this photo —
soft delete means the referenced subject never disappears out from under
another workflow. Deactivated photos are excluded from every normal
list/get/serve path.

## Future AI contract

`app/services/ai_contract.py` defines `AIInferenceService.analyze()`,
returning `NOT_IMPLEMENTED` — **not called from any endpoint this phase**.
When the disease-detection phase begins, this interface (or an HTTP call to
the separate `ai/` service) gets wired into the upload flow without the
photo-upload code needing to change.

## Known limitations (this phase)

- `capture_timestamp` is never populated — EXIF is stripped before any
  capture-time metadata would be read. Revisit if this timestamp is
  actually needed (upload_timestamp is populated and reliable).
- No byte-level upload progress percentage — only an indeterminate
  "uploading" state client-side (see `mobile/lib/core/api_client.dart`).
- Flutter widget-level tests for the capture/preview/upload navigation
  flow are not written — `image_picker` requires platform channels not
  available in this build environment's test runner; only pure-Dart logic
  (queue, model parsing) is unit-tested.
