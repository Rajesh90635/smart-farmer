/// Mirrors the four Phase 38 backend schemas exactly. score/overallScore
/// fields are nullable and this model never fills a missing value with
/// a neutral guess. roiPercent is always null - stated structurally,
/// matching the backend's own honest limitation.
library;

class PerformanceComponent {
  final String name;
  final int? score;
  final String explanation;

  PerformanceComponent({required this.name, this.score, required this.explanation});

  factory PerformanceComponent.fromJson(Map<String, dynamic> json) => PerformanceComponent(
        name: json['name'] as String,
        score: json['score'] as int?,
        explanation: json['explanation'] as String,
      );
}

class PerformanceScore {
  final String cropCycleId;
  final bool insufficientData;
  final String? overallScore;
  final String dataCompletenessPercent;
  final List<PerformanceComponent> components;

  PerformanceScore({
    required this.cropCycleId,
    required this.insufficientData,
    this.overallScore,
    required this.dataCompletenessPercent,
    required this.components,
  });

  factory PerformanceScore.fromJson(Map<String, dynamic> json) => PerformanceScore(
        cropCycleId: json['crop_cycle_id'] as String,
        insufficientData: json['insufficient_data'] as bool,
        overallScore: json['overall_score'] as String?,
        dataCompletenessPercent: json['data_completeness_percent'] as String,
        components: (json['components'] as List).map((e) => PerformanceComponent.fromJson(e as Map<String, dynamic>)).toList(),
      );
}

class ComparisonMetric {
  final String metricName;
  final String? valueA;
  final String? valueB;
  final String comparison;

  ComparisonMetric({required this.metricName, this.valueA, this.valueB, required this.comparison});

  factory ComparisonMetric.fromJson(Map<String, dynamic> json) => ComparisonMetric(
        metricName: json['metric_name'] as String,
        valueA: json['value_a'] as String?,
        valueB: json['value_b'] as String?,
        comparison: json['comparison'] as String,
      );
}

class CropComparison {
  final String cropCycleIdA;
  final String cropCycleIdB;
  final List<ComparisonMetric> metrics;

  CropComparison({required this.cropCycleIdA, required this.cropCycleIdB, required this.metrics});

  factory CropComparison.fromJson(Map<String, dynamic> json) => CropComparison(
        cropCycleIdA: json['crop_cycle_id_a'] as String,
        cropCycleIdB: json['crop_cycle_id_b'] as String,
        metrics: (json['metrics'] as List).map((e) => ComparisonMetric.fromJson(e as Map<String, dynamic>)).toList(),
      );
}

class InputCategoryBreakdown {
  final String category;
  final String actualCost;
  final String percentOfTotalCost;
  final String? estimatedCost;
  final String? variance;
  final String? roiPercent;

  InputCategoryBreakdown({
    required this.category,
    required this.actualCost,
    required this.percentOfTotalCost,
    this.estimatedCost,
    this.variance,
    this.roiPercent,
  });

  factory InputCategoryBreakdown.fromJson(Map<String, dynamic> json) => InputCategoryBreakdown(
        category: json['category'] as String,
        actualCost: json['actual_cost'] as String,
        percentOfTotalCost: json['percent_of_total_cost'] as String,
        estimatedCost: json['estimated_cost'] as String?,
        variance: json['variance'] as String?,
        roiPercent: json['roi_percent'] as String?,
      );
}

class InputRoi {
  final String cropCycleId;
  final String totalActualCost;
  final List<InputCategoryBreakdown> categories;
  final bool roiAttributionAvailable;
  final String limitationNote;

  InputRoi({
    required this.cropCycleId,
    required this.totalActualCost,
    required this.categories,
    required this.roiAttributionAvailable,
    required this.limitationNote,
  });

  factory InputRoi.fromJson(Map<String, dynamic> json) => InputRoi(
        cropCycleId: json['crop_cycle_id'] as String,
        totalActualCost: json['total_actual_cost'] as String,
        categories: (json['categories'] as List).map((e) => InputCategoryBreakdown.fromJson(e as Map<String, dynamic>)).toList(),
        roiAttributionAvailable: json['roi_attribution_available'] as bool,
        limitationNote: json['limitation_note'] as String,
      );
}

class IrrigationIntelligence {
  final String cropCycleId;
  final String recommendation;
  final String reason;
  final String weatherStatus;
  final String? pendingIrrigationTaskId;
  final bool soilMoistureAvailable;

  IrrigationIntelligence({
    required this.cropCycleId,
    required this.recommendation,
    required this.reason,
    required this.weatherStatus,
    this.pendingIrrigationTaskId,
    required this.soilMoistureAvailable,
  });

  factory IrrigationIntelligence.fromJson(Map<String, dynamic> json) => IrrigationIntelligence(
        cropCycleId: json['crop_cycle_id'] as String,
        recommendation: json['recommendation'] as String,
        reason: json['reason'] as String,
        weatherStatus: json['weather_status'] as String,
        pendingIrrigationTaskId: json['pending_irrigation_task_id'] as String?,
        soilMoistureAvailable: json['soil_moisture_available'] as bool,
      );
}
