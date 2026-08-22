import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/health_timeline/health_timeline_models.dart';

Map<String, dynamic> _eventJson({
  required String eventType,
  required String eventDatetime,
  String? healthStatus,
  String? treatmentId,
  String? caseId,
  String? photoId,
  String? analysisId,
}) =>
    {
      'event_type': eventType,
      'event_datetime': eventDatetime,
      'title': 'Test title',
      'description': 'Test description',
      'source_id': 'source-1',
      'health_status': healthStatus,
      'treatment_id': treatmentId,
      'case_id': caseId,
      'photo_id': photoId,
      'analysis_id': analysisId,
    };

void main() {
  group('TimelineEvent (Phase 35)', () {
    test('parses an ai_analysis event with a real verbatim health status', () {
      final event = TimelineEvent.fromJson(_eventJson(
        eventType: 'ai_analysis',
        eventDatetime: '2026-01-10T00:00:00Z',
        healthStatus: 'disease_detected',
        analysisId: 'analysis-1',
      ));
      expect(event.eventType, 'ai_analysis');
      expect(event.healthStatus, 'disease_detected');
      expect(event.analysisId, 'analysis-1');
    });

    test('non-health events parse with a null health status - never fabricated', () {
      final event = TimelineEvent.fromJson(_eventJson(eventType: 'crop_cycle_started', eventDatetime: '2026-01-01T00:00:00Z'));
      expect(event.healthStatus, isNull);
    });

    test('treatment_applied event carries a treatment reference', () {
      final event = TimelineEvent.fromJson(_eventJson(
        eventType: 'treatment_applied',
        eventDatetime: '2026-01-01T00:00:00Z',
        treatmentId: 'treatment-1',
      ));
      expect(event.treatmentId, 'treatment-1');
    });

    test('health_case_created event carries a case reference', () {
      final event = TimelineEvent.fromJson(_eventJson(
        eventType: 'health_case_created',
        eventDatetime: '2026-01-01T00:00:00Z',
        caseId: 'case-1',
      ));
      expect(event.caseId, 'case-1');
    });
  });

  group('CropHealthTimeline (Phase 35)', () {
    test('empty timeline parses correctly, not a crash', () {
      final timeline = CropHealthTimeline.fromJson({'crop_cycle_id': 'cycle-1', 'events': []});
      expect(timeline.events, isEmpty);
    });

    test('multiple event types preserve their given order from the backend', () {
      final timeline = CropHealthTimeline.fromJson({
        'crop_cycle_id': 'cycle-1',
        'events': [
          _eventJson(eventType: 'treatment_applied', eventDatetime: '2026-06-01T00:00:00Z'),
          _eventJson(eventType: 'crop_cycle_started', eventDatetime: '2026-01-01T00:00:00Z'),
        ],
      });
      expect(timeline.events.length, 2);
      expect(timeline.events.first.eventType, 'treatment_applied');
      expect(timeline.events.last.eventType, 'crop_cycle_started');
    });

    test('partial event data (most optional fields null) parses without crashing', () {
      final timeline = CropHealthTimeline.fromJson({
        'crop_cycle_id': 'cycle-1',
        'events': [_eventJson(eventType: 'stage_changed', eventDatetime: '2026-02-01T00:00:00Z')],
      });
      final event = timeline.events.first;
      expect(event.healthStatus, isNull);
      expect(event.treatmentId, isNull);
      expect(event.caseId, isNull);
      expect(event.photoId, isNull);
      expect(event.analysisId, isNull);
    });
  });
}
