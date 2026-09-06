import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/ledger/ledger_repository.dart';

/// D81-06 (docs/audit/FINAL_CANONICAL_group_D.md): see
/// plot_repository_test.dart for why no HTTP fake is needed - the offline
/// branch never reaches ApiClient.
class _AlwaysOfflineChecker extends NetworkStatusChecker {
  @override
  Future<bool> isOnline() async => false;
}

void main() {
  test('createEntry queues the write and throws QueuedForSyncException when offline', () async {
    final repo = LedgerRepository(apiClient: ApiClient());
    final queue = PendingWriteQueue();

    await expectLater(
      () => repo.createEntry(
        cropCycleId: 'cycle-1',
        entryType: 'expense',
        category: 'seed',
        amount: '500.00',
        entryDate: '2026-06-01',
        networkChecker: _AlwaysOfflineChecker(),
        writeQueue: queue,
      ),
      throwsA(isA<QueuedForSyncException>()),
    );

    expect(queue.items.length, 1);
    final write = queue.items.first;
    expect(write.method, 'POST');
    expect(write.path, '/crop-cycles/cycle-1/ledger/entries');
    expect(write.body['entry_type'], 'expense');
    expect(write.body['category'], 'seed');
    expect(write.body['amount'], '500.00');
  });
}
