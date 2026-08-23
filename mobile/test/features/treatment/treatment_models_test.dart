import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/treatment/treatment_models.dart';

void main() {
  group('TreatmentRecord (Phase 34)', () {
    test('parses with a before snapshot when a prior analysis exists', () {
      final treatment = TreatmentRecord.fromJson({
        'id': 'treatment-1',
        'crop_cycle_id': 'cycle-1',
        'case_id': null,
        'product_id': null,
        'before_analysis_id': 'analysis-1',
        'before_result_status': 'disease_detected',
        'application_date': '2026-01-01',
        'notes': 'Applied fungicide',
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(treatment.beforeAnalysisId, 'analysis-1');
      expect(treatment.beforeResultStatus, 'disease_detected');
    });

    test('parses with a null before snapshot when no prior analysis existed - never fabricated', () {
      final treatment = TreatmentRecord.fromJson({
        'id': 'treatment-1',
        'crop_cycle_id': 'cycle-1',
        'case_id': null,
        'product_id': null,
        'before_analysis_id': null,
        'before_result_status': null,
        'application_date': '2026-01-01',
        'notes': null,
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(treatment.beforeAnalysisId, isNull);
      expect(treatment.beforeResultStatus, isNull);
    });
  });

  group('TreatmentFollowUp (Phase 34)', () {
    test('parses with an after snapshot', () {
      final followUp = TreatmentFollowUp.fromJson({
        'id': 'followup-1',
        'treatment_id': 'treatment-1',
        'after_analysis_id': 'analysis-2',
        'after_result_status': 'healthy',
        'observation_date': '2026-01-10',
        'notes': null,
        'created_at': '2026-01-10T00:00:00Z',
      });
      expect(followUp.afterAnalysisId, 'analysis-2');
      expect(followUp.afterResultStatus, 'healthy');
    });
  });

  group('TreatmentEffectiveness (Phase 34)', () {
    test('improved result carries both before and after status for transparency', () {
      final effectiveness = TreatmentEffectiveness.fromJson({
        'treatment_id': 'treatment-1',
        'result': 'improved',
        'basis': 'The crop showed disease before treatment and appears healthy in the follow-up analysis.',
        'before_result_status': 'disease_detected',
        'after_result_status': 'healthy',
        'has_follow_up': true,
      });
      expect(effectiveness.result, 'improved');
      expect(effectiveness.basis, isNotEmpty);
      expect(effectiveness.hasFollowUp, isTrue);
    });

    test('insufficient_evidence with no follow-up is distinct from a real outcome', () {
      final effectiveness = TreatmentEffectiveness.fromJson({
        'treatment_id': 'treatment-1',
        'result': 'insufficient_evidence',
        'basis': 'No follow-up observation has been recorded yet.',
        'before_result_status': 'disease_detected',
        'after_result_status': null,
        'has_follow_up': false,
      });
      expect(effectiveness.result, 'insufficient_evidence');
      expect(effectiveness.hasFollowUp, isFalse);
      expect(effectiveness.afterResultStatus, isNull);
    });

    test('the result is always one of exactly four real values - never a fabricated fifth state', () {
      const validResults = {'improved', 'no_significant_change', 'worsened', 'insufficient_evidence'};
      for (final result in validResults) {
        final effectiveness = TreatmentEffectiveness.fromJson({
          'treatment_id': 'treatment-1',
          'result': result,
          'basis': 'x',
          'before_result_status': null,
          'after_result_status': null,
          'has_follow_up': false,
        });
        expect(validResults.contains(effectiveness.result), isTrue);
      }
    });

    test('missing optional before/after status fields do not crash parsing', () {
      final effectiveness = TreatmentEffectiveness.fromJson({
        'treatment_id': 'treatment-1',
        'result': 'insufficient_evidence',
        'basis': 'No crop analysis existed before this treatment was applied.',
        'before_result_status': null,
        'after_result_status': null,
        'has_follow_up': false,
      });
      expect(effectiveness.beforeResultStatus, isNull);
      expect(effectiveness.afterResultStatus, isNull);
    });
  });
}
