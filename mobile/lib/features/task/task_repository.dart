import '../../core/api_client.dart';
import 'task_models.dart';

class TaskRepository {
  final ApiClient _apiClient;
  TaskRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<Task> createTask({
    required String cropCycleId,
    required String taskType,
    required String title,
    String? description,
    String? dueDate,
  }) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/tasks', body: {
      'task_type': taskType,
      'title': title,
      if (description != null) 'description': description,
      if (dueDate != null) 'due_date': dueDate,
    });
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
