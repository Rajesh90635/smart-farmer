import 'dart:io';

import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_repository.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/sync_coordinator.dart';

/// D87-01 (docs/audit/FINAL_CANONICAL_group_D.md): a dedicated test for
/// `_recordFailureAndMaybeExhaust`'s counting/transition logic itself -
/// previously only the RESULTING terminal-state filtering
/// (needsManualAction) was tested, never the exhaustion transition that
/// produces it. Since the method is private, it is driven here through
/// the real public syncNow() path, exactly as production code reaches it.
class FakeOnlineConnectivityPlatform extends ConnectivityPlatform {
  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => [ConnectivityResult.wifi];

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged => const Stream.empty();
}

/// Always fails - simulates a permanently-failing upload (a corrupted
/// file, a request the backend will always reject), the exact scenario
/// kMaxAutomaticRetries exists to cap.
class AlwaysFailingCropPhotoRepository extends CropPhotoRepository {
  AlwaysFailingCropPhotoRepository() : super(apiClient: ApiClient());

  @override
  Future<CropPhoto> uploadPhoto({
    required String sessionId,
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    required String clientUploadId,
    required String source,
    bool shareLocation = false,
    double? latitude,
    double? longitude,
    DateTime? captureTimestamp,
  }) async {
    throw Exception('simulated permanent upload failure');
  }
}

Future<PendingUpload> _makeUpload(String id) async {
  final dir = await Directory.systemTemp.createTemp('sync_coordinator_test_');
  final file = File('${dir.path}/$id.jpg');
  await file.writeAsBytes([0, 1, 2, 3], flush: true);
  return PendingUpload(
    clientUploadId: id,
    sessionId: 'session-1',
    cropCycleId: 'cycle-1',
    localFilePath: file.path,
    fileName: '$id.jpg',
    mimeType: 'image/jpeg',
    source: 'camera',
  );
}

void main() {
  ConnectivityPlatform.instance = FakeOnlineConnectivityPlatform();

  test('each failed sync attempt increments retryCount and stays "failed" below the cap', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(),
    );

    for (var attempt = 1; attempt < kMaxAutomaticRetries; attempt++) {
      await coordinator.syncNow();
      final upload = queue.items.first;
      expect(upload.retryCount, attempt);
      expect(upload.status, PendingUploadStatus.failed, reason: 'attempt $attempt should stay below the cap');
    }
  });

  test('the attempt that reaches kMaxAutomaticRetries transitions to retriesExhausted, not failed', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(),
    );

    for (var attempt = 1; attempt <= kMaxAutomaticRetries; attempt++) {
      await coordinator.syncNow();
    }

    final upload = queue.items.first;
    expect(upload.retryCount, kMaxAutomaticRetries);
    expect(upload.status, PendingUploadStatus.retriesExhausted);
  });

  test('once retriesExhausted, further syncNow() calls never attempt this upload again (excluded from retryable)', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(),
    );

    for (var attempt = 1; attempt <= kMaxAutomaticRetries; attempt++) {
      await coordinator.syncNow();
    }
    final retryCountAtExhaustion = queue.items.first.retryCount;

    await coordinator.syncNow();
    await coordinator.syncNow();

    expect(queue.items.first.retryCount, retryCountAtExhaustion, reason: 'exhausted uploads must not be retried automatically again');
    expect(queue.items.first.status, PendingUploadStatus.retriesExhausted);
  });

  test('the error message from the failing attempt is recorded alongside the transition', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(),
    );

    await coordinator.syncNow();

    expect(queue.items.first.lastErrorMessage, contains('simulated permanent upload failure'));
  });
}
