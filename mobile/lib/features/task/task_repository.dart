import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import '../crop_photo/network_status_checker.dart';
import 'task_models.dart';

class TaskRepository {
  final ApiClient _apiClient;
  TaskRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// D81-04 (docs/audit/FINAL_CANONICAL_group_D.md): same optional-param
  /// offline-queueing shape as FarmRepository.createFarm (D81-01).
  Future<Task> createTask({
    required String cropCycleId,
    required String taskType,
    required String title,
    String? description,
    String? dueDate,
    String? dependsOnTaskId,
    int? repeatIntervalDays,
    NetworkStatusChecker? networkChecker,
    PendingWriteQueue? writeQueue,
  }) async {
    final body = {
      'task_type': taskType,
      'title': title,
      if (description != null) 'description': description,
      if (dueDate != null) 'due_date': dueDate,
      if (dependsOnTaskId != null) 'depends_on_task_id': dependsOnTaskId,
      if (repeatIntervalDays != null) 'repeat_interval_days': repeatIntervalDays,
    };

    if (networkChecker != null && writeQueue != null && !(await networkChecker.isOnline())) {
      await writeQueue.enqueue(
        PendingWrite(clientRequestId: generateClientRequestId(), method: 'POST', path: '/crop-cycles/$cropCycleId/tasks', body: body),
      );
      throw const QueuedForSyncException();
    }

    final response = await _apiClient.post('/crop-cycles/$cropCycleId/tasks', body: body);
    return Task.fromJson(response);
  }

  Future<List<Task>> listTasksForCropCycle(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/tasks');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Task.fromJson).toList();
  }

  Future<Task> getTask(String taskId) async {
    final response = await _apiClient.get('/tasks/$taskId');
    return Task.fromJson(response);
  }

  Future<Task> completeTask(String taskId) async {
    final response = await _apiClient.post('/tasks/$taskId/complete');
    return Task.fromJson(response);
  }

  Future<Task> cancelTask(String taskId) async {
    final response = await _apiClient.post('/tasks/$taskId/cancel');
    return Task.fromJson(response);
  }
}
