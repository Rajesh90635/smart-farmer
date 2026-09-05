import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/task/task_models.dart';

Map<String, dynamic> _taskJson({
  required String status,
  required String displayStatus,
  String? dueDate,
  Map<String, dynamic>? weatherAdvisory,
  String? dependsOnTaskId,
  bool? dependencyCompleted,
  int? repeatIntervalDays,
}) =>
    {
      'id': 'task-1',
      'crop_cycle_id': 'cycle-1',
      'task_type': 'irrigation',
      'title': 'Check drip lines',
      'description': null,
      'due_date': dueDate,
      'status': status,
      'display_status': displayStatus,
      'completed_at': null,
      'created_at': '2026-01-01T00:00:00Z',
      'weather_advisory': weatherAdvisory,
      'depends_on_task_id': dependsOnTaskId,
      'dependency_completed': dependencyCompleted,
      'repeat_interval_days': repeatIntervalDays,
    };

void main() {
  group('Task (Step 16)', () {
    test('pending task with no due date is never overdue', () {
      final task = Task.fromJson(_taskJson(status: 'pending', displayStatus: 'pending'));
      expect(task.isOverdue, isFalse);
    });

    test('displayStatus overdue is read directly from the backend, never recomputed', () {
      final task = Task.fromJson(_taskJson(status: 'pending', displayStatus: 'overdue', dueDate: '2020-01-01'));
      expect(task.isOverdue, isTrue);
      expect(task.status, 'pending');
    });

    test('completed task is never treated as overdue even with a past due date', () {
      final task = Task.fromJson(_taskJson(status: 'completed', displayStatus: 'completed', dueDate: '2020-01-01'));
      expect(task.isOverdue, isFalse);
      expect(task.isCompleted, isTrue);
    });

    test('cancelled task is recognized distinctly', () {
      final task = Task.fromJson(_taskJson(status: 'cancelled', displayStatus: 'cancelled'));
      expect(task.isCancelled, isTrue);
      expect(task.isCompleted, isFalse);
      expect(task.isOverdue, isFalse);
    });

    test('missing optional fields do not crash parsing', () {
      final task = Task.fromJson(_taskJson(status: 'pending', displayStatus: 'pending'));
      expect(task.description, isNull);
      expect(task.dueDate, isNull);
      expect(task.completedAt, isNull);
      expect(task.weatherAdvisory, isNull);
      expect(task.dependsOnTaskId, isNull);
      expect(task.dependencyCompleted, isNull);
      expect(task.repeatIntervalDays, isNull);
      expect(task.isBlockedByDependency, isFalse);
    });

    test('a task with an incomplete dependency is blocked - D8-07 (docs/FINAL_GAP_REPORT.md)', () {
      final task = Task.fromJson(_taskJson(
        status: 'pending',
        displayStatus: 'pending',
        dependsOnTaskId: 'task-0',
        dependencyCompleted: false,
      ));
      expect(task.isBlockedByDependency, isTrue);
    });

    test('a task whose dependency is already completed is not blocked', () {
      final task = Task.fromJson(_taskJson(
        status: 'pending',
        displayStatus: 'pending',
        dependsOnTaskId: 'task-0',
        dependencyCompleted: true,
      ));
      expect(task.isBlockedByDependency, isFalse);
    });

    test('repeatIntervalDays parses through unchanged - D8-08 (docs/FINAL_GAP_REPORT.md)', () {
      final task = Task.fromJson(_taskJson(status: 'pending', displayStatus: 'pending', repeatIntervalDays: 7));
      expect(task.repeatIntervalDays, 7);
    });

    test('weather advisory parses the exact three real backend fields - reused from Step 15, nothing invented', () {
      final task = Task.fromJson(_taskJson(
        status: 'pending',
        displayStatus: 'pending',
        weatherAdvisory: {'action': 'avoid_spraying', 'reason_message_key': 'spray_condition_warning', 'basis': 'high_wind'},
      ));
      expect(task.weatherAdvisory!.action, 'avoid_spraying');
      expect(task.weatherAdvisory!.reasonMessageKey, 'spray_condition_warning');
      expect(task.weatherAdvisory!.basis, 'high_wind');
    });

    test('the one real weather-advisory message key maps correctly - none invented for an unimplemented rule', () {
      expect(taskWeatherAdvisoryMessageKeys['spray_condition_warning'], 'sprayConditionWarning');
      expect(taskWeatherAdvisoryMessageKeys.length, 1);
    });

    test('taskTypeOptions matches the exact real backend TaskType enum values', () {
      expect(taskTypeOptions, ['general', 'irrigation', 'spraying', 'fertilizing', 'weeding', 'harvesting', 'other']);
    });
  });
}
