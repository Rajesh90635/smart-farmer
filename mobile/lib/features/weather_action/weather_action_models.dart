/// Mirrors backend/app/schemas/weather_action.py exactly. status is
/// always one of 'safe' | 'caution' | 'unsafe' | 'unknown' - this model
/// never converts a missing reading into a fabricated 'safe'. Every
/// assessment carries isDeterministic: true verbatim from the backend.
library;

class ActionAssessment {
  final String actionType;
  final String status;
  final String reason;
  final Map<String, dynamic> evidence;
  final bool isDeterministic;

  ActionAssessment({
    required this.actionType,
    required this.status,
    required this.reason,
    required this.evidence,
    required this.isDeterministic,
  });

  factory ActionAssessment.fromJson(Map<String, dynamic> json) => ActionAssessment(
        actionType: json['action_type'] as String,
        status: json['status'] as String,
        reason: json['reason'] as String,
        evidence: (json['evidence'] as Map).cast<String, dynamic>(),
        isDeterministic: json['is_deterministic'] as bool,
      );
}

class WindowSuggestion {
  final String forecastDate;
  final String status;
  final String reason;

  WindowSuggestion({required this.forecastDate, required this.status, required this.reason});

  factory WindowSuggestion.fromJson(Map<String, dynamic> json) => WindowSuggestion(
        forecastDate: json['forecast_date'] as String,
        status: json['status'] as String,
        reason: json['reason'] as String,
      );
}

class CropWeatherAction {
  final String cropCycleId;
  final bool weatherAvailable;
  final bool isStale;
  final String? fetchedAt;
  final List<ActionAssessment> assessments;
  final WindowSuggestion? recommendedSprayWindow;
  final String? relevantPendingSprayTaskId;
  final List<String> dataCompletenessNotes;

  CropWeatherAction({
    required this.cropCycleId,
    required this.weatherAvailable,
    required this.isStale,
    this.fetchedAt,
    required this.assessments,
    this.recommendedSprayWindow,
    this.relevantPendingSprayTaskId,
    required this.dataCompletenessNotes,
  });

  factory CropWeatherAction.fromJson(Map<String, dynamic> json) => CropWeatherAction(
        cropCycleId: json['crop_cycle_id'] as String,
        weatherAvailable: json['weather_available'] as bool,
        isStale: json['is_stale'] as bool,
        fetchedAt: json['fetched_at'] as String?,
        assessments: (json['assessments'] as List).map((e) => ActionAssessment.fromJson(e as Map<String, dynamic>)).toList(),
        recommendedSprayWindow: json['recommended_spray_window'] != null
            ? WindowSuggestion.fromJson(json['recommended_spray_window'] as Map<String, dynamic>)
            : null,
        relevantPendingSprayTaskId: json['relevant_pending_spray_task_id'] as String?,
        dataCompletenessNotes: (json['data_completeness_notes'] as List).cast<String>(),
      );
}
