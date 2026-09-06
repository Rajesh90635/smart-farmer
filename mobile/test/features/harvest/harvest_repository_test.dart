import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/harvest/harvest_repository.dart';

/// D81-07 (docs/audit/FINAL_CANONICAL_group_D.md): see
/// plot_repository_test.dart for why no HTTP fake is needed - the offline
/// branch never reaches ApiClient.
class _AlwaysOfflineChecker extends NetworkStatusChecker {
  @override
  Future<bool> isOnline() async => false;
}

void main() {
  test('confirmReady queues the write and throws QueuedForSyncException when offline', () async {
    final repo = HarvestRepository(apiClient: ApiClient());
    final queue = PendingWriteQueue();

    await expectLater(
      () => repo.confirmReady(
        harvestId: 'harvest-1',
        actualHarvestDate: '2026-06-15',
        estimatedQuantity: '120.5',
        networkChecker: _AlwaysOfflineChecker(),
        writeQueue: queue,
      ),
      throwsA(isA<QueuedForSyncException>()),
    );

    expect(queue.items.length, 1);
    final write = queue.items.first;
    expect(write.method, 'POST');
    expect(write.path, '/harvests/harvest-1/confirm-ready');
    expect(write.body['actual_harvest_date'], '2026-06-15');
    expect(write.body['estimated_quantity'], '120.5');
  });
}
