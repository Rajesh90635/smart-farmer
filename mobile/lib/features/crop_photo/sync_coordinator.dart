import 'dart:math' as math;

import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import 'crop_photo_repository.dart';
import 'network_status_checker.dart';
import 'pending_upload_queue.dart';

/// D83-02 (docs/audit/FINAL_CANONICAL_group_D.md): exponential backoff
/// gating automatic retries below, so connectivity flapping (repeated
/// brief online/offline transitions) doesn't hammer the backend with
/// rapid repeated attempts for an item that just failed. Base/max are
/// reasonable defaults chosen here - no product-specified value exists
/// for either. A never-attempted item (retryCount 0, lastAttemptAt null)
/// is always immediately eligible, so a fresh upload/write is never
/// delayed by this gate - only a repeat automatic attempt is.
const int kBackoffBaseSeconds = 5;
const int kBackoffMaxSeconds = 300;

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
  // D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): optional - only farm
  // create/edit routes through this today (see farm_repository.dart);
  // future D81-02..07/09 entities reuse this SAME drain loop, no second
  // coordinator. Omitting both (the default) preserves this class's
  // exact prior photo-only behavior for any existing caller/test.
  final PendingWriteQueue? _writeQueue;
  final ApiClient? _apiClient;
  // D83-02 (docs/audit/FINAL_CANONICAL_group_D.md): overridable only for
  // tests that need to exercise rapid repeated attempts (e.g. the
  // retry-cap tests below, which call syncNow() back-to-back with no
  // real time passing) or that need to advance a fake clock - every real
  // caller (app.dart) uses the class defaults above.
  final int _backoffBaseSeconds;
  final int _backoffMaxSeconds;
  final DateTime Function() _now;
  bool _syncing = false;

  SyncCoordinator({
    required PendingUploadQueue queue,
    required NetworkStatusChecker networkChecker,
    required CropPhotoRepository repository,
    PendingWriteQueue? writeQueue,
    ApiClient? apiClient,
    int backoffBaseSeconds = kBackoffBaseSeconds,
    int backoffMaxSeconds = kBackoffMaxSeconds,
    DateTime Function() now = DateTime.now,
  })  : _queue = queue,
        _networkChecker = networkChecker,
        _repository = repository,
        _writeQueue = writeQueue,
        _apiClient = apiClient,
        _backoffBaseSeconds = backoffBaseSeconds,
        _backoffMaxSeconds = backoffMaxSeconds,
        _now = now;

  /// D83-02: a never-attempted item (retryCount 0, lastAttemptAt null) is
  /// always immediately eligible, so a fresh upload/write is never
  /// delayed by this gate - only a repeat AUTOMATIC attempt is.
  bool _isEligibleForRetry(int retryCount, DateTime? lastAttemptAt) {
    if (lastAttemptAt == null || retryCount <= 0) return true;
    final delaySeconds = math.min(_backoffBaseSeconds * math.pow(2, retryCount - 1).toInt(), _backoffMaxSeconds);
    // Inclusive (>=, not strict >): two back-to-back _now() calls can tie
    // exactly (fast execution, or a low-resolution platform clock) -
    // especially with backoffBaseSeconds: 0 in tests - and a tie must
    // still count as "the delay has elapsed", not gate a retry forever.
    return !_now().isBefore(lastAttemptAt.add(Duration(seconds: delaySeconds)));
  }

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

      // D83-02: skip an item still within its own backoff window - it
      // stays queued and is picked up on a later sync tick once eligible.
      final toRetry = List.of(_queue.retryable.where((u) => _isEligibleForRetry(u.retryCount, u.lastAttemptAt)));
      for (final pending in toRetry) {
        await _attemptUpload(pending);
      }

      final writeQueue = _writeQueue;
      final apiClient = _apiClient;
      if (writeQueue != null && apiClient != null) {
        final toRetryWrites = List.of(writeQueue.retryable.where((w) => _isEligibleForRetry(w.retryCount, w.lastAttemptAt)));
        for (final write in toRetryWrites) {
          await _attemptWrite(writeQueue, apiClient, write);
        }
      }
    } finally {
      _syncing = false;
    }
  }

  /// D81-01: generic dispatch for any queued write - same idempotency
  /// (clientRequestId), 401-terminal-state, and retry-exhaustion
  /// semantics as _attemptUpload below, generalized past photo uploads.
  Future<void> _attemptWrite(PendingWriteQueue writeQueue, ApiClient apiClient, PendingWrite write) async {
    write.lastAttemptAt = _now(); // D83-02: read by _isEligibleForRetry on the NEXT sync tick
    await writeQueue.updateStatus(write.clientRequestId, PendingWriteStatus.sending);
    try {
      if (write.method == 'PUT') {
        await apiClient.put(write.path, body: write.body);
      } else {
        await apiClient.post(write.path, body: write.body);
      }
      await writeQueue.updateStatus(write.clientRequestId, PendingWriteStatus.sent);
      await writeQueue.remove(write.clientRequestId);
    } on SessionExpiredException {
      await writeQueue.updateStatus(
        write.clientRequestId, PendingWriteStatus.authenticationRequired,
        errorMessage: 'Please log in again to finish this update.',
      );
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        await writeQueue.updateStatus(
          write.clientRequestId, PendingWriteStatus.authenticationRequired,
          errorMessage: 'Please log in again to finish this update.',
        );
      } else {
        await _recordWriteFailureAndMaybeExhaust(writeQueue, write, e.toString());
      }
    } catch (e) {
      await _recordWriteFailureAndMaybeExhaust(writeQueue, write, e.toString());
    }
  }

  Future<void> _recordWriteFailureAndMaybeExhaust(PendingWriteQueue writeQueue, PendingWrite write, String errorMessage) async {
    write.retryCount += 1;
    if (write.retryCount >= kMaxAutomaticWriteRetries) {
      await writeQueue.updateStatus(write.clientRequestId, PendingWriteStatus.retriesExhausted, errorMessage: errorMessage);
    } else {
      await writeQueue.updateStatus(write.clientRequestId, PendingWriteStatus.failed, errorMessage: errorMessage);
    }
  }

  Future<void> _attemptUpload(PendingUpload pending) async {
    pending.lastAttemptAt = _now(); // D83-02: read by _isEligibleForRetry on the NEXT sync tick
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
        captureTimestamp: pending.capturedAt,
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
  // D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): same startup-load
  // requirement as PendingUploadQueue above - a farm queued offline
  // before the app was last closed must not be silently lost.
  await context.read<PendingWriteQueue>().loadFromDisk();
  context.read<SyncCoordinator>().start();
}
