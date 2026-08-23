# Offline Architecture (Foundation Phase)

## What exists today

`mobile/lib/core/connectivity/connectivity_controller.dart` defines:
- `ConnectivityStatus` (`online` / `offline` / `unknown`) — the vocabulary
  every screen and service will depend on.
- `ConnectivityController` — a `ChangeNotifier` placeholder. Not yet wired
  to a real connectivity plugin (e.g. `connectivity_plus`) — that wiring
  happens in the Offline-First epic.
- `OfflineBanner` — a widget that shows a persistent, visible banner
  whenever status is `offline`, per the UX rule that offline state must
  always be visible, never silent.

`ApiClient` (`mobile/lib/core/api_client.dart`) surfaces network failures
as a distinct `ApiException` rather than swallowing them — the future
offline-queue logic needs to be able to tell "the server rejected this"
apart from "there is no network," and that distinction has to exist from
the first network call onward, not be retrofitted later.

## Full design (documented now, not yet built)

Per the approved architecture's offline-first requirements:

| Scenario | Planned behavior |
|---|---|
| No internet | Photo capture, diary entries, and form submissions write to a local on-device queue (SQLite) tagged "pending sync" — never blocked, never silently discarded |
| Slow internet | Chunked/resumable upload where practical; UI shows progress, not a frozen screen |
| Network failure mid-upload | Checksum/size-mismatch detection triggers automatic retry from the queue, not silent treatment as success |
| Partial upload | Server rejects incomplete files; client keeps the item queued rather than assuming success |
| Duplicate upload | Each queued item carries a client-generated idempotency key so a retried sync can't create two records for one capture |
| Sync conflict (same entity edited on two devices) | MVP: last-write-wins with a visible warning to the farmer. Full conflict-resolution UI is a P2 feature per the approved architecture, not MVP |

## Why this isn't built yet

Building the local queue/retry/conflict logic before there's any real data
to capture (no Farm/Crop module exists yet) would mean designing it against
guesses rather than the actual shapes of the first real offline-capable
features (crop photo upload, crop diary entries). It's scheduled
immediately after those modules exist — see PROJECT_STATUS.md.
