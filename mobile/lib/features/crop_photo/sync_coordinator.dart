import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import 'crop_photo_repository.dart';
import 'network_status_checker.dart';
import 'pending_upload_queue.dart';

/// The other genuinely missing piece of offline-first sync (alongside
/// persistence, see pending_upload_queue.dart): a farmer should not have
/// to remember to manually tap "Retry" on every queued photo the moment
/// their connection comes back - this listens for the device coming back
/// online and automatically retries every retryable queued upload, using
/// the SAME clientUploadId each time, which is what makes a retry safe
/// against the backend's real (session_id, client_upload_id) unique
/// constraint even if triggered multiple times (e.g. connectivity
/// flapping briefly) - a duplicate photo is never created.
///
/// This does not replace the manual "Retry" button already in
/// camera_capture_screen.dart - a farmer can still retry immediately
/// without waiting for this listener; both paths converge on the same
/// idempotent upload call.
class SyncCoordinator {
  final PendingUploadQueue _queue;
  final NetworkStatusChecker _networkChecker;
  final CropPhotoRepository _repository;
  bool _syncing = false;

  SyncCoordinator({
    required PendingUploadQueue queue,
    required NetworkStatusChecker networkChecker,
    required CropPhotoRepository repository,
  })  : _queue = queue,
        _networkChecker = networkChecker,
        _repository = repository;

  /// Call once at app startup, after PendingUploadQueue.loadFromDisk().
  void start() {
    _networkChecker.onStatusChange().listen((isOnline) {
      if (isOnline) {
        syncNow();
      }
    });
    syncNow();
  }

  /// Attempts every currently-retryable queued upload. Safe to call
  /// concurrently - re-entrant calls are no-ops while a sync is already
  /// in progress.
  Future<void> syncNow() async {
    if (_syncing) return;
    _syncing = true;
    try {
      final online = await _networkChecker.isOnline();
      if (!online) return;

      final toRetry = List.of(_queue.retryable);
      for (final pending in toRetry) {
        await _attemptUpload(pending);
      }
    } finally {
      _syncing = false;
    }
  }

  Future<void> _attemptUpload(PendingUpload pending) async {
    await _queue.updateStatus(pending.clientUploadId, PendingUploadStatus.uploading);
    try {
      final bytes = await pending.readBytes();
      final result = await _repository.uploadPhoto(
        sessionId: pending.sessionId,
        fileBytes: bytes,
        fileName: pending.fileName,
        mimeType: pending.mimeType,
        clientUploadId: pending.clientUploadId,
        source: pending.source,
      );
      // A quality-rejected result is a SUCCESSFUL HTTP response (the
      // photo was received and stored server-side, just flagged
      // unsuitable for reliable diagnosis) - not an exception, and not a
      // transport failure. It must never be re-queued or retried: doing
      // so would just re-send the exact same rejected photo forever.
      // Marked 'uploaded' and removed from the LOCAL queue either way -
      // the farmer can still discover a quality rejection later via the
      // existing crop photo list/detail screens (which already render
      // photo.isLowQuality + qualityFriendlyMessages), without this
      // background sync needing to surface a popup/notification of its
      // own (deliberately not spamming the farmer every time sync runs).
      if (result.isLowQuality) {
        // Intentionally the same terminal handling as an accepted
        // upload - documented explicitly here so a future change to this
        // method doesn't accidentally start retrying quality rejections.
      }
      await _queue.updateStatus(pending.clientUploadId, PendingUploadStatus.uploaded);
      await _queue.remove(pending.clientUploadId);
    } on ApiException catch (e) {
      // A bug found during Step 10 verification: an expired/invalid
      // session (401) would previously be retried forever, identically
      // to a transient network error, on every future connectivity
      // change. A 401 will never succeed by simply retrying the same
      // request again - the farmer needs to re-authenticate first, so
      // this is marked as a distinct, non-auto-retried terminal state
      // rather than fed back into the same retry loop.
      if (e.statusCode == 401) {
        await _queue.updateStatus(
          pending.clientUploadId,
          PendingUploadStatus.authenticationRequired,
          errorMessage: 'Please log in again to finish uploading this photo.',
        );
      } else {
        await _recordFailureAndMaybeExhaust(pending, e.toString());
      }
    } catch (e) {
      await _recordFailureAndMaybeExhaust(pending, e.toString());
    }
  }

  /// Also found during Step 10 verification: nothing capped how many
  /// times a permanently-failing upload (e.g. a corrupted local file, a
  /// request the backend will always reject) would be auto-retried -
  /// every connectivity change retried it again, forever. After
  /// kMaxAutomaticRetries attempts, the upload stops being offered to
  /// automatic sync but is NOT deleted - it remains queued so a farmer
  /// can still see it and retry manually later (e.g. after the app is
  /// updated, or after checking the photo itself).
  Future<void> _recordFailureAndMaybeExhaust(PendingUpload pending, String errorMessage) async {
    pending.retryCount += 1;
    if (pending.retryCount >= kMaxAutomaticRetries) {
      await _queue.updateStatus(pending.clientUploadId, PendingUploadStatus.retriesExhausted, errorMessage: errorMessage);
    } else {
      await _queue.updateStatus(pending.clientUploadId, PendingUploadStatus.failed, errorMessage: errorMessage);
    }
  }
}

/// Loads the persisted queue and starts the ALREADY-PROVIDED SyncCoordinator
/// singleton (registered in app.dart's MultiProvider) - called once from
/// splash_screen.dart at startup. Reading it from Provider, rather than
/// constructing a new instance here, is what makes the coordinator
/// reachable later (e.g. `context.read<SyncCoordinator>().syncNow()` from
/// login_screen.dart after re-authentication, or from
/// PendingUploadsScreen's manual "Retry" button) - a real, previously
/// missing "manual recovery" path.
Future<void> initializeOfflineSync(BuildContext context) async {
  final queue = context.read<PendingUploadQueue>();
  await queue.loadFromDisk();
  context.read<SyncCoordinator>().start();
}
