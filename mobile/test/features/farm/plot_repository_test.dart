import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/farm/plot_repository.dart';

/// D81-02 (docs/audit/FINAL_CANONICAL_group_D.md): a real, queryable
/// offline state for the repository test below - the offline branch never
/// reaches ApiClient, so no HTTP fake is needed for these cases.
class _AlwaysOfflineChecker extends NetworkStatusChecker {
  @override
  Future<bool> isOnline() async => false;
}

void main() {
  group('PlotRepository.createPlot offline queueing', () {
    test('queues the write and throws QueuedForSyncException when offline', () async {
      final repo = PlotRepository(apiClient: ApiClient());
      final queue = PendingWriteQueue();

      await expectLater(
        () => repo.createPlot(
          'farm-1',
          plotName: 'North Field',
          areaValue: 2.5,
          areaUnit: 'acre',
          irrigationType: 'drip',
          networkChecker: _AlwaysOfflineChecker(),
          writeQueue: queue,
        ),
        throwsA(isA<QueuedForSyncException>()),
      );

      expect(queue.items.length, 1);
      final write = queue.items.first;
      expect(write.method, 'POST');
      expect(write.path, '/farms/farm-1/plots');
      expect(write.body['plot_name'], 'North Field');
      expect(write.body['area_value'], 2.5);
      expect(write.body['area_unit'], 'acre');
      expect(write.body['irrigation_type'], 'drip');
      expect(write.status, PendingWriteStatus.waitingForNetwork);
    });
  });
}
