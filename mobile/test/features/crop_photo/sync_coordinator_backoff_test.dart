import 'dart:io';

import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_repository.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/sync_coordinator.dart';

/// D83-02 (docs/audit/FINAL_CANONICAL_group_D.md): exponential backoff
/// gating automatic retries, so connectivity flapping doesn't trigger
/// rapid repeated attempts. A fake, controllable clock (rather than a
/// real `sleep()`) keeps this test fast and deterministic.
class FakeOnlineConnectivityPlatform extends ConnectivityPlatform {
  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => [ConnectivityResult.wifi];

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged => const Stream.empty();
}

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
  final dir = await Directory.systemTemp.createTemp('sync_coordinator_backoff_test_');
  final file = File('${dir.path}/$id.jpg');
  await file.writeAsBytes([0, 1, 2, 3], flush: true);
  return PendingUpload(
    clientUploadId: id, sessionId: 'session-1', cropCycleId: 'cycle-1',
    localFilePath: file.path, fileName: '$id.jpg', mimeType: 'image/jpeg', source: 'camera',
  );
}

class _FakeClock {
  DateTime current = DateTime(2026, 1, 1);
  DateTime now() => current;
}

void main() {
  ConnectivityPlatform.instance = FakeOnlineConnectivityPlatform();

  test('a second syncNow() immediately after a failed attempt does not retry yet (within the backoff window)', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final clock = _FakeClock();
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(), now: clock.now,
    );

    await coordinator.syncNow(); // first attempt: always eligible, fails -> retryCount 1
    expect(queue.items.first.retryCount, 1);

    await coordinator.syncNow(); // clock hasn't moved - still inside the backoff window
    expect(queue.items.first.retryCount, 1, reason: 'must not retry again before the backoff delay elapses');
  });

  test('once the fake clock advances past the backoff window, the next syncNow() retries', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final clock = _FakeClock();
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(), now: clock.now,
    );

    await coordinator.syncNow(); // retryCount 1, backoff = kBackoffBaseSeconds * 2^0
    clock.current = clock.current.add(const Duration(seconds: kBackoffBaseSeconds + 1));

    await coordinator.syncNow();
    expect(queue.items.first.retryCount, 2, reason: 'must retry once the backoff delay has elapsed');
  });

  test('a fresh (never-attempted) item is never delayed by the backoff gate', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(await _makeUpload('a'));
    final clock = _FakeClock();
    final coordinator = SyncCoordinator(
      queue: queue, networkChecker: NetworkStatusChecker(), repository: AlwaysFailingCropPhotoRepository(), now: clock.now,
    );

    await coordinator.syncNow();
    expect(queue.items.first.retryCount, 1, reason: 'the very first attempt must never be gated');
  });
}
