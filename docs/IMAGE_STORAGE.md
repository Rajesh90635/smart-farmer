# Image Storage

## Abstraction (reused, not duplicated)

Crop photos use the **existing** `FileStorage` interface and
`LocalFileStorage` implementation built in the foundation phase
(`app/services/storage/base.py`, `local_storage.py`) — nothing new was
built here. Business code depends on `FileStorage`, never on the local
filesystem directly, so swapping in Azure Blob/S3-compatible storage later
means writing one new class.

## A real bug found and fixed in this module

The crop-photo service originally **pre-computed** a hierarchical storage
key (`farmer_id/crop_cycle_id/uuid.ext`) and passed it as the `file_name`
argument to `LocalFileStorage.save()` — but `save()` **generates its own
key** internally (a fresh UUID + sanitized filename under the given
container) and returns it; it does not accept a caller-supplied full path
verbatim. The pre-computed key was then persisted to the database while
the file was actually written under save()'s own generated path —
uploads appeared to succeed, but retrieval failed with `FileNotFoundError`
100% of the time. Caught by `test_get_photo_file_returns_image_bytes`.

**Fix:** `LocalFileStorage._sanitize_container()` was extended to support
a hierarchical container path (`"crop-photos/{farmer_id}/{crop_cycle_id}"`)
— safe specifically because `container` is always a server-constructed
value (validated UUIDs), never client input — and the crop-photo service
now always persists the storage key **returned by** `save()`, never one it
invents itself. This is documented here because it's an easy mistake to
repeat with any future caller of this interface: **always use the
returned key**, never assume you know what it will be.

## Directory layout (local/free MVP)

```
storage-data/
  crop-photos/
    {farmer_id}/
      {crop_cycle_id}/
        {random-uuid}-{random-uuid}.jpg          <- main (processed) image
        {random-uuid}-{random-uuid}.jpg          <- thumbnail (separate file)
```
`storage-data/` is outside the source tree and already gitignored (see
root `.gitignore`, added in the foundation phase).

## Secure key generation

`app/core/photo_storage_keys.py` builds only two inputs for `save()`: a
hierarchical container (farmer/crop-cycle scoped) and a random leaf
filename (`build_leaf_filename`) — the **original client filename is never
used** to build any path, only kept (sanitized) as a display-only DB field.
This defeats path traversal by construction: there is nothing
client-controlled in the storage path at all.

## Serving files

Images are served only through the authenticated
`GET /api/v1/crop-photos/{id}/file` endpoint — never a public static path,
never a bare URL a client could reach unauthenticated (Requirement 15).
Ownership is checked before storage is ever touched.

## What's NOT built here (by design)

- No Azure Blob/S3 implementation yet — the interface is ready, the
  implementation isn't needed until a real deployment target requires it.
- No background/async file processing — everything is synchronous this
  phase (see docs/CROP_PHOTO_MODULE.md's note on `processing_status`).
