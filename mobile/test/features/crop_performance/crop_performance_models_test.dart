import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_performance/crop_performance_models.dart';

void main() {
  group('PerformanceScore (Phase 38.1)', () {
    test('missing component score parses as null, never a fabricated guess', () {
      final score = PerformanceScore.fromJson({
        'crop_cycle_id': 'cycle-1',
        'insufficient_data': false,
        'overall_score': '45.00',
        'data_completeness_percent': '40.00',
        'components': [
          {'name': 'financial_performance', 'score': null, 'explanation': 'No cost estimate exists.'},
          {'name': 'stage_progression', 'score': 40, 'explanation': 'Currently growing.'},
        ],
      });
      final financial = score.components.firstWhere((c) => c.name == 'financial_performance');
      expect(financial.score, isNull);
    });

    test('insufficient_data true parses with a null overall score', () {
      final score = PerformanceScore.fromJson({
        'crop_cycle_id': 'cycle-1',
        'insufficient_data': true,
        'overall_score': null,
        'data_completeness_percent': '0.00',
        'components': [],
      });
      expect(score.insufficientData, isTrue);
      expect(score.overallScore, isNull);
    });
  });

  group('CropComparison (Phase 38.2)', () {
    test('insufficient_data comparison never claims a verdict', () {
      final comparison = CropComparison.fromJson({
        'crop_cycle_id_a': 'cycle-1',
        'crop_cycle_id_b': 'cycle-2',
        'metrics': [
          {'metric_name': 'actual_revenue', 'value_a': null, 'value_b': '5000.00', 'comparison': 'insufficient_data'},
        ],
      });
      expect(comparison.metrics.first.comparison, 'insufficient_data');
      expect(comparison.metrics.first.valueA, isNull);
    });

    test('a_higher and b_higher parse correctly for real comparisons', () {
      final comparison = CropComparison.fromJson({
        'crop_cycle_id_a': 'cycle-1',
        'crop_cycle_id_b': 'cycle-2',
        'metrics': [
          {'metric_name': 'actual_cost', 'value_a': '100.00', 'value_b': '500.00', 'comparison': 'a_higher'},
        ],
      });
      expect(comparison.metrics.first.comparison, 'a_higher');
    });
  });

  group('InputRoi (Phase 38.3)', () {
    test('roi_percent is always null - never a fabricated ROI figure', () {
      final roi = InputRoi.fromJson({
        'crop_cycle_id': 'cycle-1',
        'total_actual_cost': '1000.00',
        'categories': [
          {'category': 'seed', 'actual_cost': '300.00', 'percent_of_total_cost': '30.00', 'estimated_cost': null, 'variance': null, 'roi_percent': null},
        ],
        'roi_attribution_available': false,
        'limitation_note': 'This project has no data linking input purchases to crop yield or revenue.',
      });
      expect(roi.roiAttributionAvailable, isFalse);
      expect(roi.categories.first.roiPercent, isNull);
    });

    test('empty categories list parses correctly when no expenses exist', () {
      final roi = InputRoi.fromJson({
        'crop_cycle_id': 'cycle-1',
        'total_actual_cost': '0',
        'categories': [],
        'roi_attribution_available': false,
        'limitation_note': 'x',
      });
      expect(roi.categories, isEmpty);
    });
  });

  group('IrrigationIntelligence (Phase 38.4)', () {
    test('soil_moisture_available is always false and always present', () {
      final intelligence = IrrigationIntelligence.fromJson({
        'crop_cycle_id': 'cycle-1',
        'recommendation': 'delay',
        'reason': 'Heavy rain is likely.',
        'weather_status': 'unsafe',
        'pending_irrigation_task_id': null,
        'soil_moisture_available': false,
      });
      expect(intelligence.soilMoistureAvailable, isFalse);
      expect(intelligence.recommendation, 'delay');
    });

    test('irrigate_now with a pending task ID parses correctly', () {
      final intelligence = IrrigationIntelligence.fromJson({
        'crop_cycle_id': 'cycle-1',
        'recommendation': 'irrigate_now',
        'reason': 'No weather reason to delay.',
        'weather_status': 'safe',
        'pending_irrigation_task_id': 'task-1',
        'soil_moisture_available': false,
      });
      expect(intelligence.pendingIrrigationTaskId, 'task-1');
    });

    test('unknown recommendation parses correctly when weather is unavailable', () {
      final intelligence = IrrigationIntelligence.fromJson({
        'crop_cycle_id': 'cycle-1',
        'recommendation': 'unknown',
        'reason': 'Weather data is not available.',
        'weather_status': 'unknown',
        'pending_irrigation_task_id': null,
        'soil_moisture_available': false,
      });
      expect(intelligence.recommendation, 'unknown');
    });
  });
}
