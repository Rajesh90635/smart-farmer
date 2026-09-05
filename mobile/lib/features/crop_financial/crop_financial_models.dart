/// Mirrors backend/app/schemas/cost_estimate.py exactly.
///
/// THE ABSOLUTE FINANCIAL RULE, encoded here structurally: `estimatedCost`
/// is nullable because "no estimate entered yet" is a real, distinct
/// state from "estimated at zero" - this Flutter model never collapses
/// that distinction into a fabricated zero. `expectedRevenue` and
/// `estimatedProfit` are permanently-null fields - the backend never
/// sends anything else, since no yield/price dataset exists anywhere in
/// this project.
library;

class CropCostEstimate {
  final String id;
  final String cropCycleId;
  final String? cropStageDefinitionId;
  final String category;
  final String estimatedAmount;
  final String? description;
  final String createdAt;

  CropCostEstimate({
    required this.id,
    required this.cropCycleId,
    this.cropStageDefinitionId,
    required this.category,
    required this.estimatedAmount,
    this.description,
    required this.createdAt,
  });

  factory CropCostEstimate.fromJson(Map<String, dynamic> json) => CropCostEstimate(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        cropStageDefinitionId: json['crop_stage_definition_id'] as String?,
        category: json['category'] as String,
        estimatedAmount: json['estimated_amount'] as String,
        description: json['description'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class StageFinancialSummary {
  final String cropStageDefinitionId;
  final String stageDisplayName;
  final String? estimatedAmount;
  final String? actualAmount;
  final String? variance;

  StageFinancialSummary({
    required this.cropStageDefinitionId,
    required this.stageDisplayName,
    this.estimatedAmount,
    this.actualAmount,
    this.variance,
  });

  factory StageFinancialSummary.fromJson(Map<String, dynamic> json) => StageFinancialSummary(
        cropStageDefinitionId: json['crop_stage_definition_id'] as String,
        stageDisplayName: json['stage_display_name'] as String,
        estimatedAmount: json['estimated_amount'] as String?,
        actualAmount: json['actual_amount'] as String?,
        variance: json['variance'] as String?,
      );
}

/// Phase 32 - mirrors backend/app/schemas/profit_forecast.py exactly.
/// `potentialAdditionalRevenue` is only ever computed from the farmer's
/// OWN listing price x their OWN yield figure - never a fabricated
/// market price. `revenueProjectionIsPartial` tells the UI whether the
/// projection may be missing unsold/unlisted harvest value.
/// `dataCompletenessNotes` are real, backend-generated explanations of
/// exactly what's missing - never left for the farmer to guess.
class CropProfitForecast {
  final String cropCycleId;

  final String? estimatedCost;
  final String actualCost;
  final String? remainingEstimatedCost;
  final String? projectedTotalCost;

  final String actualRevenue;
  final String committedRevenue;
  final String? potentialAdditionalRevenue;
  final String? potentialAdditionalRevenueBasis;
  final String projectedTotalRevenue;
  final bool revenueProjectionIsPartial;

  final String? projectedProfitLoss;
  final String? projectedProfitLossPercent;

  final List<String> dataCompletenessNotes;

  CropProfitForecast({
    required this.cropCycleId,
    this.estimatedCost,
    required this.actualCost,
    this.remainingEstimatedCost,
    this.projectedTotalCost,
    required this.actualRevenue,
    required this.committedRevenue,
    this.potentialAdditionalRevenue,
    this.potentialAdditionalRevenueBasis,
    required this.projectedTotalRevenue,
    required this.revenueProjectionIsPartial,
    this.projectedProfitLoss,
    this.projectedProfitLossPercent,
    required this.dataCompletenessNotes,
  });

  factory CropProfitForecast.fromJson(Map<String, dynamic> json) => CropProfitForecast(
        cropCycleId: json['crop_cycle_id'] as String,
        estimatedCost: json['estimated_cost'] as String?,
        actualCost: json['actual_cost'] as String,
        remainingEstimatedCost: json['remaining_estimated_cost'] as String?,
        projectedTotalCost: json['projected_total_cost'] as String?,
        actualRevenue: json['actual_revenue'] as String,
        committedRevenue: json['committed_revenue'] as String,
        potentialAdditionalRevenue: json['potential_additional_revenue'] as String?,
        potentialAdditionalRevenueBasis: json['potential_additional_revenue_basis'] as String?,
        projectedTotalRevenue: json['projected_total_revenue'] as String,
        revenueProjectionIsPartial: json['revenue_projection_is_partial'] as bool,
        projectedProfitLoss: json['projected_profit_loss'] as String?,
        projectedProfitLossPercent: json['projected_profit_loss_percent'] as String?,
        dataCompletenessNotes: (json['data_completeness_notes'] as List).cast<String>(),
      );
}

class CropFinancialSummary {
  final String cropCycleId;
  final String? estimatedCost;
  final String actualCost;
  final String? costVariance;
  final String? costVariancePercent;

  final String? expectedRevenue;
  final String actualRevenue;

  final String? estimatedProfit;
  final String actualProfitLoss;
  final String? profitLossPercent;
  final String? revenueToCostRatio;

  final bool hasAnyActualRevenue;
  final List<StageFinancialSummary> stageSummaries;

  final String? costPerAcre;
  final String? revenuePerAcre;
  final String? profitLossPerAcre;

  CropFinancialSummary({
    required this.cropCycleId,
    this.estimatedCost,
    required this.actualCost,
    this.costVariance,
    this.costVariancePercent,
    this.expectedRevenue,
    required this.actualRevenue,
    this.estimatedProfit,
    required this.actualProfitLoss,
    this.profitLossPercent,
    this.revenueToCostRatio,
    required this.hasAnyActualRevenue,
    required this.stageSummaries,
    this.costPerAcre,
    this.revenuePerAcre,
    this.profitLossPerAcre,
  });

  factory CropFinancialSummary.fromJson(Map<String, dynamic> json) => CropFinancialSummary(
        cropCycleId: json['crop_cycle_id'] as String,
        estimatedCost: json['estimated_cost'] as String?,
        actualCost: json['actual_cost'] as String,
        costVariance: json['cost_variance'] as String?,
        costVariancePercent: json['cost_variance_percent'] as String?,
        expectedRevenue: json['expected_revenue'] as String?,
        actualRevenue: json['actual_revenue'] as String,
        estimatedProfit: json['estimated_profit'] as String?,
        actualProfitLoss: json['actual_profit_loss'] as String,
        profitLossPercent: json['profit_loss_percent'] as String?,
        revenueToCostRatio: json['revenue_to_cost_ratio'] as String?,
        hasAnyActualRevenue: json['has_any_actual_revenue'] as bool,
        stageSummaries: (json['stage_summaries'] as List).map((e) => StageFinancialSummary.fromJson(e as Map<String, dynamic>)).toList(),
        costPerAcre: json['cost_per_acre'] as String?,
        revenuePerAcre: json['revenue_per_acre'] as String?,
        profitLossPerAcre: json['profit_loss_per_acre'] as String?,
      );
}
