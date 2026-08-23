import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/expert_case/case_models.dart';

Map<String, dynamic> _caseJson({
  required String status,
  String? finalVerifiedClass,
  String? finalVerificationSource,
}) =>
    {
      'id': 'case-1',
      'crop_cycle_id': 'cycle-1',
      'crop_photo_id': 'photo-1',
      'ai_analysis_id': 'analysis-1',
      'requested_professional_role': 'expert',
      'reason': 'ai_low_confidence',
      'status': status,
      'priority': 'medium',
      'final_verified_class': finalVerifiedClass,
      'final_verification_source': finalVerificationSource,
      'second_opinion_count': 0,
      'created_at': '2026-01-01T00:00:00Z',
      'closed_at': null,
    };

void main() {
  group('ExpertCase (Step 13)', () {
    test('waiting_for_assignment is not completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'waiting_for_assignment'));
      expect(c.isCompleted, isFalse);
    });

    test('assigned is not completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'assigned'));
      expect(c.isCompleted, isFalse);
    });

    test('in_review is not completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'in_review'));
      expect(c.isCompleted, isFalse);
    });

    test('verified is completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'verified'));
      expect(c.isCompleted, isTrue);
    });

    test('rejected is completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'rejected'));
      expect(c.isCompleted, isTrue);
    });

    test('closed is completed', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'closed'));
      expect(c.isCompleted, isTrue);
    });

    test('cancelled is NOT treated as completed (distinct from a real result)', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'cancelled'));
      expect(c.isCompleted, isFalse);
    });

    test('finalVerificationSource carries only a role string, never fabricated identity', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'verified', finalVerificationSource: 'expert'));
      expect(c.finalVerificationSource, 'expert');
    });

    test('finalVerifiedClass is null when the backend never set it (e.g. "confirmed" outcome)', () {
      final c = ExpertCase.fromJson(_caseJson(status: 'verified'));
      expect(c.finalVerifiedClass, isNull);
    });

    test('every real backend CaseStatus value maps to a known l10n key - none invented, none missing', () {
      const realBackendStatuses = [
        'open',
        'waiting_for_assignment',
        'assigned',
        'in_review',
        'needs_more_information',
        'verified',
        'rejected',
        'escalated',
        'closed',
        'cancelled',
      ];
      for (final status in realBackendStatuses) {
        expect(caseStatusMessageKeys.containsKey(status), isTrue, reason: 'missing mapping for real backend status: $status');
      }
      expect(caseStatusMessageKeys.length, realBackendStatuses.length);
    });
  });

  group('CaseAuditEntry (Step 13)', () {
    test('parses only the three fields the backend actually returns - no notes, no identity', () {
      final entry = CaseAuditEntry.fromJson({
        'action': 'CASE_ASSIGNED',
        'actor_role': 'automation_service',
        'occurred_at': '2026-01-01T00:00:00Z',
      });
      expect(entry.action, 'CASE_ASSIGNED');
      expect(entry.actorRole, 'automation_service');
      expect(entry.occurredAt, '2026-01-01T00:00:00Z');
    });
  });
}
