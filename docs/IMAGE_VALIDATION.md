# Image Validation & Quality

## Two separate, independent checks

1. **Validation** (`app/core/image_validation.py`) — hard pass/fail. A
   failing image is **rejected outright, no DB row created**.
2. **Quality** (`app/core/image_quality.py`) — soft heuristic. A
   low-quality image is still **accepted and stored** (the upload
   succeeded), just flagged `image_quality_status = rejected` so the
   farmer can see it and choose to retake.

Never confuse the two: validation failure = nothing is saved; quality
failure = saved, but flagged.

## Validation rules (configurable via Settings, never hard-coded)

| Check | Config | Failure message shown |
|---|---|---|
| Non-empty | — | "The uploaded file is empty." |
| Max size | `photo_max_upload_size_bytes` (default 10 MB) | "Photo is too large. Maximum size is 10 MB." |
| Allowed MIME type | `photo_allowed_mime_types` (JPEG/PNG/WEBP) | "Unsupported photo format..." |
| Not corrupted | Pillow `Image.verify()` | "This does not appear to be a valid image file." |
| Declared type matches actual bytes | Pillow's detected format vs. declared MIME | "The photo's actual format doesn't match its declared type..." — catches a renamed non-image file |
| Minimum dimensions | `photo_min_width_px` / `photo_min_height_px` (default 300×300) | "Photo is too small..." |

## Quality heuristics — technical only, never agricultural

**Hard rule, enforced by code review and by test
(`test_quality_never_mentions_disease_or_agricultural_terms`):** this
module's vocabulary is limited to `too_dark`, `too_bright`, `too_blurry`.
It never claims anything about disease, pests, or plant health.

| Check | Method | Config |
|---|---|---|
| Too dark | Mean grayscale brightness below threshold | `photo_quality_min_mean_brightness` (default 25.0) |
| Too bright | Mean grayscale brightness above threshold | `photo_quality_max_mean_brightness` (default 230.0) |
| Too blurry | Edge-detection (Pillow `FIND_EDGES`) variance below threshold | `photo_quality_min_blur_variance` (default 15.0) |

### A real bug found and fixed in the blur heuristic

The initial implementation measured edge variance across the **entire**
edge-detected image, including a 1–2 pixel border artifact that Pillow's
convolution produces at image boundaries regardless of actual image
content. Verified empirically: a perfectly flat, textureless test image
(which should register as maximally blurry) showed variance ≈108 instead
of ≈0, because the border ring dominated the statistic on top of an
otherwise-zero interior. **Fix:** crop 2px off each edge of the
edge-detected image before computing variance. Verified after the fix: the
same flat image correctly shows variance = 0.0, and a genuinely noisy/
textured image still shows high variance (~14,665) — confirming the fix
didn't break detection of real sharpness, only removed the artifact.

## Processing (applied to every accepted image, regardless of quality verdict)

1. **Orientation normalize** — `ImageOps.exif_transpose()`, applied
   *before* EXIF is stripped (otherwise a portrait photo with only an EXIF
   rotation flag would be stored sideways).
2. **EXIF strip** — unconditional, on every image, regardless of location
   consent (see docs/SECURITY.md "Privacy").
3. **Resize** — capped at `photo_max_dimension_px` (default 1600px longest
   side), preserving aspect ratio.
4. **Re-encode as JPEG** — regardless of input format (PNG/WEBP accepted
   as input, never as stored output — a deliberate simplification).
5. **Thumbnail** — separate file, capped at `photo_thumbnail_max_dimension_px`
   (default 320px).

## Verified with real images, not mocks

Every rule above was tested against genuine Pillow-generated JPEG/PNG
bytes (`tests/photo_factories.py`, `tests/test_image_pipeline.py`) — not
hand-waved fixtures. See PROJECT_STATUS.md for the actual test run output.
