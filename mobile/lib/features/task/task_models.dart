/// Mirrors backend/app/schemas/task.py exactly. `displayStatus` is a
/// backend-COMPUTED field (pending/overdue/completed/cancelled) - this
/// Flutter model never recomputes it independently; it only ever renders
/// whatever the backend decided, since "overdue" depends on the
/// backend's own clock and rules, not the device's.
///
/// `weatherAdvisory`, when present, is the EXACT SAME deterministic
/// spray-condition rule already built in Step 15 - reused unchanged, not
/// a new agronomic recommendation invented for tasks.
library;

class WeatherAdvisory {
  final String action;
  final String reasonMessageKey;
  final String basis;

  WeatherAdvisory({required this.action, required this.reasonMessageKey, required this.basis});

  factory WeatherAdvisory.fromJson(Map<String, dynamic> json) => WeatherAdvisory(
        action: json['action'] as String,
        reasonMessageKey: json['reason_message_key'] as String,
        basis: json['basis'] as String,
      );
}

class Task {
  final String id;
  final String cropCycleId;
  final String taskType;
  final String title;
  final String? description;
  final String? dueDate;
  final String status;
  final String displayStatus;
  final String? completedAt;
  final String createdAt;
  final WeatherAdvisory? weatherAdvisory;

  Task({
    required this.id,
    required this.cropCycleId,
    required this.taskType,
    required this.title,
    this.description,
    this.dueDate,
    required this.status,
    required this.displayStatus,
    this.completedAt,
    required this.createdAt,
    this.weatherAdvisory,
  });

  bool get isOverdue => displayStatus == 'overdue';
  bool get isCompleted => displayStatus == 'completed';
  bool get isCancelled => displayStatus == 'cancelled';

  factory Task.fromJson(Map<String, dynamic> json) => Task(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        taskType: json['task_type'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        dueDate: json['due_date'] as String?,
        status: json['status'] as String,
        displayStatus: json['display_status'] as String,
        completedAt: json['completed_at'] as String?,
        createdAt: json['created_at'] as String,
        weatherAdvisory: json['weather_advisory'] != null ? WeatherAdvisory.fromJson(json['weather_advisory'] as Map<String, dynamic>) : null,
      );
}

const List<String> taskTypeOptions = ['general', 'irrigation', 'spraying', 'fertilizing', 'weeding', 'harvesting', 'other'];

const Map<String, String> taskWeatherAdvisoryMessageKeys = {
  'spray_condition_warning': 'sprayConditionWarning',
};
