import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/weather_action/weather_action_models.dart';

Map<String, dynamic> _actionJson({
  required bool weatherAvailable,
  required List<Map<String, dynamic>> assessments,
  Map<String, dynamic>? window,
  String? pendingTaskId,
  List<String> notes = const [],
  bool isStale = false,
}) =>
    {
      'crop_cycle_id': 'cycle-1',
      'weather_available': weatherAvailable,
      'is_stale': isStale,
      'fetched_at': weatherAvailable ? '2026-06-01T00:00:00Z' : null,
      'assessments': assessments,
      'recommended_spray_window': window,
      'relevant_pending_spray_task_id': pendingTaskId,
      'data_completeness_notes': notes,
    };

Map<String, dynamic> _assessmentJson({required String actionType, required String status, Map<String, dynamic> evidence = const {}}) => {
      'action_type': actionType,
      'status': status,
      'reason': 'Test reason',
      'evidence': evidence,
      'is_deterministic': true,
    };

void main() {
  group('CropWeatherAction (Phase 37)', () {
    test('weather unavailable parses with unknown assessments, never fabricated safe', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: false,
        assessments: [
          _assessmentJson(actionType: 'spray', status: 'unknown'),
          _assessmentJson(actionType: 'irrigation', status: 'unknown'),
          _assessmentJson(actionType: 'harvest', status: 'unknown'),
        ],
        notes: ['Weather data is not available for this farm right now.'],
      ));
      expect(action.weatherAvailable, isFalse);
      expect(action.assessments.every((a) => a.status == 'unknown'), isTrue);
      expect(action.dataCompletenessNotes, isNotEmpty);
    });

    test('safe spray assessment carries isDeterministic true verbatim', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'safe', evidence: {'wind_speed_kmh': 10, 'rain_probability_percent': 5})],
      ));
      final spray = action.assessments.first;
      expect(spray.status, 'safe');
      expect(spray.isDeterministic, isTrue);
      expect(spray.evidence['wind_speed_kmh'], 10);
    });

    test('recommended spray window parses correctly when present', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'unsafe')],
        window: {'forecast_date': '2026-06-03', 'status': 'safe', 'reason': 'Lower wind expected.'},
      ));
      expect(action.recommendedSprayWindow, isNotNull);
      expect(action.recommendedSprayWindow!.forecastDate, '2026-06-03');
    });

    test('null recommended window parses correctly - never fabricated when none exists', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'unsafe')],
        window: null,
        notes: ['No suitable spraying window was found in the available forecast data.'],
      ));
      expect(action.recommendedSprayWindow, isNull);
    });

    test('pending spray task reference parses correctly when present and absent', () {
      final withTask = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'safe')],
        pendingTaskId: 'task-1',
      ));
      expect(withTask.relevantPendingSprayTaskId, 'task-1');

      final withoutTask = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'safe')],
      ));
      expect(withoutTask.relevantPendingSprayTaskId, isNull);
    });

    test('stale flag parses correctly', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [_assessmentJson(actionType: 'spray', status: 'safe')],
        isStale: true,
      ));
      expect(action.isStale, isTrue);
    });

    test('all three action types parse independently with different statuses', () {
      final action = CropWeatherAction.fromJson(_actionJson(
        weatherAvailable: true,
        assessments: [
          _assessmentJson(actionType: 'spray', status: 'unsafe'),
          _assessmentJson(actionType: 'irrigation', status: 'caution'),
          _assessmentJson(actionType: 'harvest', status: 'safe'),
        ],
      ));
      expect(action.assessments.length, 3);
      expect(action.assessments.map((a) => a.status).toSet(), {'unsafe', 'caution', 'safe'});
    });
  });
}
