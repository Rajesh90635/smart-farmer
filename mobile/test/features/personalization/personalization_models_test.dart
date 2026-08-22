import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/personalization/personalization_models.dart';

void main() {
  group('LearnedPreference (Phase 39)', () {
    test('insufficient evidence parses with null confidence and observation together', () {
      final preference = LearnedPreference.fromJson({
        'signal_name': 'treatment_follow_up_consistency',
        'observation': null,
        'evidence_count': 1,
        'confidence': null,
        'last_observed_at': null,
        'explanation': 'Only 1 treatment(s) recorded.',
      });
      expect(preference.confidence, isNull);
      expect(preference.observation, isNull);
      expect(preference.evidenceCount, 1);
    });

    test('sufficient evidence parses with a real observation and confidence', () {
      final preference = LearnedPreference.fromJson({
        'signal_name': 'treatment_follow_up_consistency',
        'observation': 'This farmer consistently records a follow-up after applying treatments.',
        'evidence_count': 4,
        'confidence': 'low',
        'last_observed_at': '2026-01-10T00:00:00Z',
        'explanation': 'Based on 4 of 4 recorded treatments having a follow-up.',
      });
      expect(preference.confidence, 'low');
      expect(preference.observation, isNotEmpty);
    });
  });

  group('PersonalizationProfile (Phase 39)', () {
    test('parses multiple preferences independently', () {
      final profile = PersonalizationProfile.fromJson({
        'farmer_id': 'farmer-1',
        'preferences': [
          {'signal_name': 'preferred_crop', 'observation': null, 'evidence_count': 0, 'confidence': null, 'last_observed_at': null, 'explanation': 'x'},
          {
            'signal_name': 'task_completion_consistency',
            'observation': null,
            'evidence_count': 0,
            'confidence': null,
            'last_observed_at': null,
            'explanation': 'y',
          },
        ],
      });
      expect(profile.preferences.length, 2);
    });
  });

  group('LearningSummary (Phase 39)', () {
    test('ml_training_justified is always false and always present', () {
      final summary = LearningSummary.fromJson({
        'crop_cycle_id': 'cycle-1',
        'feature_snapshot': {
          'feature_version': 'v1-foundation',
          'crop_cycle_id': 'cycle-1',
          'extracted_at': '2026-01-01T00:00:00Z',
          'available_at_time': {'cultivation_status': 'growing'},
          'outcome_label': null,
          'outcome_known_only_after': null,
        },
        'ml_training_justified': false,
        'ml_readiness_note': 'ML training is not yet justified.',
      });
      expect(summary.mlTrainingJustified, isFalse);
      expect(summary.featureSnapshot.outcomeLabel, isNull);
    });

    test('outcome_label parses correctly when a crop has been harvested', () {
      final summary = LearningSummary.fromJson({
        'crop_cycle_id': 'cycle-1',
        'feature_snapshot': {
          'feature_version': 'v1-foundation',
          'crop_cycle_id': 'cycle-1',
          'extracted_at': '2026-01-01T00:00:00Z',
          'available_at_time': {},
          'outcome_label': {'actual_revenue': '5000.00', 'actual_profit_loss': '2000.00'},
          'outcome_known_only_after': '2026-03-01',
        },
        'ml_training_justified': false,
        'ml_readiness_note': 'x',
      });
      expect(summary.featureSnapshot.outcomeLabel, isNotNull);
      expect(summary.featureSnapshot.outcomeKnownOnlyAfter, '2026-03-01');
    });
  });

  group('AdvisoryFeedback (Phase 39)', () {
    test('parses correctly with an optional source reference', () {
      final feedback = AdvisoryFeedback.fromJson({
        'id': 'feedback-1',
        'crop_cycle_id': 'cycle-1',
        'source_type': 'risk_score',
        'source_reference': null,
        'feedback_type': 'helpful',
        'note': null,
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(feedback.sourceType, 'risk_score');
      expect(feedback.feedbackType, 'helpful');
    });
  });
}
