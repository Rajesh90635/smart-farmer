import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_risk/crop_risk_models.dart';

Map<String, dynamic> _riskJson({
  required String overallRisk,
  required List<Map<String, dynamic>> factors,
  String? recommendation,
}) =>
    {
      'crop_cycle_id': 'cycle-1',
      'overall_risk': overallRisk,
      'factors': factors,
      'recommendation': recommendation,
    };

Map<String, dynamic> _factorJson({required String name, required String source, required String value, required String explanation}) => {
      'factor_name': name,
      'source': source,
      'value': value,
      'explanation': explanation,
    };

void main() {
  group('CropRiskScore (Phase 33)', () {
    test('insufficient_data with all-unknown factors parses honestly - never a fabricated low', () {
      final risk = CropRiskScore.fromJson(_riskJson(
        overallRisk: 'insufficient_data',
        factors: [
          _factorJson(name: 'Recent Disease Detection', source: 'AI crop photo analysis', value: 'unknown', explanation: 'No analysis yet.'),
          _factorJson(name: 'Treatment Response', source: 'Not tracked in this application', value: 'unknown', explanation: 'Not tracked.'),
        ],
      ));
      expect(risk.overallRisk, 'insufficient_data');
      expect(risk.factors.every((f) => f.value == 'unknown'), isTrue);
      expect(risk.recommendation, isNull);
    });

    test('every factor carries a source and explanation - never a bare value', () {
      final risk = CropRiskScore.fromJson(_riskJson(
        overallRisk: 'high',
        factors: [
          _factorJson(name: 'Recent Disease Detection', source: 'AI crop photo analysis', value: 'high', explanation: 'Disease detected recently.'),
        ],
        recommendation: 'Consider requesting an expert review.',
      ));
      final factor = risk.factors.first;
      expect(factor.source, isNotEmpty);
      expect(factor.explanation, isNotEmpty);
      expect(factor.value, 'high');
    });

    test('recommendation is structurally separate from factors - a suggestion, not an observed fact', () {
      final risk = CropRiskScore.fromJson(_riskJson(
        overallRisk: 'high',
        factors: [_factorJson(name: 'Recent Disease Detection', source: 'AI crop photo analysis', value: 'high', explanation: 'x')],
        recommendation: 'Consider requesting an expert review.',
      ));
      expect(risk.recommendation, 'Consider requesting an expert review.');
      expect(risk.factors.any((f) => f.explanation.contains('Consider requesting')), isFalse);
    });

    test('low risk with no recommendation parses correctly', () {
      final risk = CropRiskScore.fromJson(_riskJson(
        overallRisk: 'low',
        factors: [_factorJson(name: 'Recent Disease Detection', source: 'AI crop photo analysis', value: 'low', explanation: 'Healthy.')],
      ));
      expect(risk.overallRisk, 'low');
      expect(risk.recommendation, isNull);
    });

    test('multiple factors with different values all parse correctly and independently', () {
      final risk = CropRiskScore.fromJson(_riskJson(
        overallRisk: 'high',
        factors: [
          _factorJson(name: 'Recent Disease Detection', source: 'AI crop photo analysis', value: 'high', explanation: 'a'),
          _factorJson(name: 'Current Weather Risk', source: 'Weather service', value: 'medium', explanation: 'b'),
          _factorJson(name: 'Financial Execution Risk', source: 'Crop financial summary (Phase 31)', value: 'low', explanation: 'c'),
          _factorJson(name: 'Treatment Response', source: 'Not tracked in this application', value: 'unknown', explanation: 'd'),
        ],
      ));
      expect(risk.factors.length, 4);
      expect(risk.factors.map((f) => f.value).toSet(), {'high', 'medium', 'low', 'unknown'});
    });
  });
}
