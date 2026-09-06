import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/farm/crop_repository.dart';

/// D81-03 (docs/audit/FINAL_CANONICAL_group_D.md): see plot_repository_test.dart
/// for why no HTTP fake is needed - the offline branch never reaches ApiClient.
class _AlwaysOfflineChecker extends NetworkStatusChecker {
  @override
  Future<bool> isOnline() async => false;
}

void main() {
  test('createCropCycle queues the write and throws QueuedForSyncException when offline', () async {
    final repo = CropRepository(apiClient: ApiClient());
    final queue = PendingWriteQueue();

    await expectLater(
      () => repo.createCropCycle(
        'plot-1',
        cropId: 'crop-1',
        sowingDate: '2026-06-01',
        season: 'kharif',
        networkChecker: _AlwaysOfflineChecker(),
        writeQueue: queue,
      ),
      throwsA(isA<QueuedForSyncException>()),
    );

    expect(queue.items.length, 1);
    final write = queue.items.first;
    expect(write.method, 'POST');
    expect(write.path, '/plots/plot-1/crops');
    expect(write.body['crop_id'], 'crop-1');
    expect(write.body['sowing_date'], '2026-06-01');
    expect(write.body['season'], 'kharif');
  });
}
