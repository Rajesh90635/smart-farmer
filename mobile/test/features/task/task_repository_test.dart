import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/task/task_repository.dart';

/// D81-04 (docs/audit/FINAL_CANONICAL_group_D.md): see
/// plot_repository_test.dart for why no HTTP fake is needed - the offline
/// branch never reaches ApiClient.
class _AlwaysOfflineChecker extends NetworkStatusChecker {
  @override
  Future<bool> isOnline() async => false;
}

void main() {
  test('createTask queues the write and throws QueuedForSyncException when offline', () async {
    final repo = TaskRepository(apiClient: ApiClient());
    final queue = PendingWriteQueue();

    await expectLater(
      () => repo.createTask(
        cropCycleId: 'cycle-1',
        taskType: 'irrigation',
        title: 'Water the field',
        dueDate: '2026-06-10',
        networkChecker: _AlwaysOfflineChecker(),
        writeQueue: queue,
      ),
      throwsA(isA<QueuedForSyncException>()),
    );

    expect(queue.items.length, 1);
    final write = queue.items.first;
    expect(write.method, 'POST');
    expect(write.path, '/crop-cycles/cycle-1/tasks');
    expect(write.body['task_type'], 'irrigation');
    expect(write.body['title'], 'Water the field');
    expect(write.body['due_date'], '2026-06-10');
  });
}
