/// Mirrors backend/app/schemas/health_timeline.py exactly. Every event
/// is a real, dated fact read directly from the backend's aggregation -
/// this model has no field or method that could derive a severity score
/// or interpret a note as a diagnosis. health_status is always the
/// verbatim backend AIAnalysis.result_status value when present, never
/// converted to a percentage.
library;

class TimelineEvent {
  final String eventType;
  final String eventDatetime;
  final String title;
  final String description;
  final String sourceId;
  final String? healthStatus;
  final String? treatmentId;
  final String? caseId;
  final String? photoId;
  final String? analysisId;

  TimelineEvent({
    required this.eventType,
    required this.eventDatetime,
    required this.title,
    required this.description,
    required this.sourceId,
    this.healthStatus,
    this.treatmentId,
    this.caseId,
    this.photoId,
    this.analysisId,
  });

  factory TimelineEvent.fromJson(Map<String, dynamic> json) => TimelineEvent(
        eventType: json['event_type'] as String,
        eventDatetime: json['event_datetime'] as String,
        title: json['title'] as String,
        description: json['description'] as String,
        sourceId: json['source_id'] as String,
        healthStatus: json['health_status'] as String?,
        treatmentId: json['treatment_id'] as String?,
        caseId: json['case_id'] as String?,
        photoId: json['photo_id'] as String?,
        analysisId: json['analysis_id'] as String?,
      );
}

class CropHealthTimeline {
  final String cropCycleId;
  final List<TimelineEvent> events;

  CropHealthTimeline({required this.cropCycleId, required this.events});

  factory CropHealthTimeline.fromJson(Map<String, dynamic> json) => CropHealthTimeline(
        cropCycleId: json['crop_cycle_id'] as String,
        events: (json['events'] as List).map((e) => TimelineEvent.fromJson(e as Map<String, dynamic>)).toList(),
      );
}
