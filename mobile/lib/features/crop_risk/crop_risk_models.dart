/// Mirrors backend/app/schemas/crop_risk.py exactly. Every factor is
/// fully explainable - this model has no field or method that could
/// present a bare number without its source/explanation. `value` of
/// 'unknown' means the underlying real data genuinely doesn't exist -
/// never rendered as a guessed "low" risk. `recommendation` is kept
/// structurally separate from `factors` - a suggestion is never
/// presented as an observed fact.
library;

class RiskFactor {
  final String factorName;
  final String source;
  final String value;
  final String explanation;

  RiskFactor({required this.factorName, required this.source, required this.value, required this.explanation});

  factory RiskFactor.fromJson(Map<String, dynamic> json) => RiskFactor(
        factorName: json['factor_name'] as String,
        source: json['source'] as String,
        value: json['value'] as String,
        explanation: json['explanation'] as String,
      );
}

class CropRiskScore {
  final String cropCycleId;
  final String overallRisk;
  final List<RiskFactor> factors;
  final String? recommendation;

  CropRiskScore({required this.cropCycleId, required this.overallRisk, required this.factors, this.recommendation});

  factory CropRiskScore.fromJson(Map<String, dynamic> json) => CropRiskScore(
        cropCycleId: json['crop_cycle_id'] as String,
        overallRisk: json['overall_risk'] as String,
        factors: (json['factors'] as List).map((e) => RiskFactor.fromJson(e as Map<String, dynamic>)).toList(),
        recommendation: json['recommendation'] as String?,
      );
}
