# Offline-First Media Capture and Sync

## What was genuinely missing before this phase

Crop photo capture, quality validation, and idempotent upload already
existed (Prompt 5). The disclosed gap was specifically: the client-side
"pending upload" queue was **in-memory only** - a photo queued while
offline was silently lost if the app was closed or killed before
connectivity returned, and a farmer had to manually retry each queued
photo rather than it happening automatically.

## What this phase adds — client-side only, no backend changes

The backend's `(session_id, client_upload_id)` unique constraint (Prompt
5) already provides everything a sync engine needs to be idempotent - it
was inspected and confirmed unchanged. **No backend code was modified
this phase.**

1. **Persistent queue** (`pending_upload_queue.dart`, rewritten in place,
   same public API as before): every queued photo is copied into the
   app's own document directory (via `path_provider` - free, no new
   native permissions) and tracked in a JSON manifest file, both restored
   via `loadFromDisk()` at app startup. A photo captured offline now
   survives the app being closed, killed, or the device rebooting before
   connectivity returns.
2. **Automatic sync on reconnect** (`sync_coordinator.dart`, new): listens
   to the existing `NetworkStatusChecker`'s connectivity stream and
   automatically retries every queued photo the moment the device comes
   back online - a farmer no longer needs to reopen the app or manually
   tap "Retry" for each photo. Every retry (manual or automatic) sends the
   **same** `clientUploadId`, so the backend's real unique constraint
   guarantees no duplicate photo is ever created even if a sync is
   triggered multiple times (e.g. connectivity flapping).
3. **Wired at the correct startup point** (`splash_screen.dart`): the
   splash screen already does async startup work (session restoration)
   before routing - `initializeOfflineSync()` was added there, not a new
   startup mechanism.

## A design issue found and fixed during this same pass

Making `_persist()` write to disk unconditionally would have made the
queue's core list-manipulation logic (`enqueue`/`updateStatus`/`remove`)
untestable without mocking a `path_provider` platform channel - and would
mean a transient disk-write failure could crash an otherwise-successful
in-memory operation. Fixed by making persistence best-effort (wrapped in
try/catch, mirroring the same defensive pattern `loadFromDisk()` already
used) - the in-memory queue is always the source of truth for the running
app session; the on-disk mirror is a durability improvement, not a
dependency the core logic requires to function.

## What is still NOT built (disclosed, not hidden)

- **No sync for anything other than crop photo uploads** - other
  potentially-offline actions (e.g. submitting a case review, accepting
  an offer) still require connectivity at the moment of the action. This
  phase's scope was specifically "media capture and sync," per the
  canonical V3 sequence step.
- **No conflict resolution** - not applicable here (photo upload is
  create-only via a unique idempotency key, so there is no concept of a
  server-side value that could conflict with a queued local change).
- **No storage-quota management** - if a farmer queues many photos while
  offline, on-device storage usage is not monitored or capped this phase.
- **No Flutter tests could be executed** - no Flutter SDK exists in this
  build environment (the same limitation documented for every prior
  Flutter change in this project). The queue's list-manipulation logic
  was written to be testable without a platform-channel mock (see above),
  and 7 unit tests were written/updated accordingly, but not run.
