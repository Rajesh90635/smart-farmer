import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_financial/crop_financial_models.dart';

Map<String, dynamic> _summaryJson({
  String? estimatedCost,
  required String actualCost,
  String? costVariance,
  required String actualRevenue,
  required String actualProfitLoss,
  required bool hasAnyActualRevenue,
  List<Map<String, dynamic>> stageSummaries = const [],
}) =>
    {
      'crop_cycle_id': 'cycle-1',
      'estimated_cost': estimatedCost,
      'actual_cost': actualCost,
      'cost_variance': costVariance,
      'cost_variance_percent': null,
      'expected_revenue': null,
      'actual_revenue': actualRevenue,
      'estimated_profit': null,
      'actual_profit_loss': actualProfitLoss,
      'profit_loss_percent': null,
      'revenue_to_cost_ratio': null,
      'has_any_actual_revenue': hasAnyActualRevenue,
      'stage_summaries': stageSummaries,
    };

void main() {
  group('CropFinancialSummary (Phase 31)', () {
    test('no estimate entered parses as null, never a fabricated zero', () {
      final summary = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: null, actualCost: '0', actualRevenue: '0', actualProfitLoss: '0', hasAnyActualRevenue: false),
      );
      expect(summary.estimatedCost, isNull);
      expect(summary.costVariance, isNull);
    });

    test('expectedRevenue and estimatedProfit are always null - the model never carries a fabricated value', () {
      final summary = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: '500.00', actualCost: '400.00', actualRevenue: '600.00', actualProfitLoss: '200.00', hasAnyActualRevenue: true),
      );
      expect(summary.expectedRevenue, isNull);
      expect(summary.estimatedProfit, isNull);
    });

    test('actualCost and actualRevenue are always real values, never null, even at zero', () {
      final summary = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: null, actualCost: '0', actualRevenue: '0', actualProfitLoss: '0', hasAnyActualRevenue: false),
      );
      expect(summary.actualCost, '0');
      expect(summary.actualRevenue, '0');
    });

    test('hasAnyActualRevenue distinguishes "no sale yet" from "confirmed zero revenue"', () {
      final noSaleYet = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: null, actualCost: '800.00', actualRevenue: '0', actualProfitLoss: '-800.00', hasAnyActualRevenue: false),
      );
      expect(noSaleYet.hasAnyActualRevenue, isFalse);
      expect(noSaleYet.actualProfitLoss, '-800.00');

      final confirmedRevenue = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: null, actualCost: '800.00', actualRevenue: '1000.00', actualProfitLoss: '200.00', hasAnyActualRevenue: true),
      );
      expect(confirmedRevenue.hasAnyActualRevenue, isTrue);
    });

    test('stage summaries parse the exact real backend fields', () {
      final summary = CropFinancialSummary.fromJson(
        _summaryJson(
          estimatedCost: '500.00',
          actualCost: '400.00',
          actualRevenue: '0',
          actualProfitLoss: '-400.00',
          hasAnyActualRevenue: false,
          stageSummaries: [
            {
              'crop_stage_definition_id': 'stage-1',
              'stage_display_name': 'Land Preparation',
              'estimated_amount': '200.00',
              'actual_amount': '180.00',
              'variance': '20.00',
            },
          ],
        ),
      );
      expect(summary.stageSummaries.length, 1);
      expect(summary.stageSummaries.first.stageDisplayName, 'Land Preparation');
      expect(summary.stageSummaries.first.variance, '20.00');
    });

    test('empty stage summaries list parses without crashing', () {
      final summary = CropFinancialSummary.fromJson(
        _summaryJson(estimatedCost: null, actualCost: '0', actualRevenue: '0', actualProfitLoss: '0', hasAnyActualRevenue: false),
      );
      expect(summary.stageSummaries, isEmpty);
    });
  });

  group('CropProfitForecast (Phase 32)', () {
    Map<String, dynamic> forecastJson({
      String? estimatedCost,
      required String actualCost,
      String? remainingEstimatedCost,
      String? projectedTotalCost,
      required String actualRevenue,
      required String committedRevenue,
      String? potentialAdditionalRevenue,
      String? potentialAdditionalRevenueBasis,
      required String projectedTotalRevenue,
      required bool revenueProjectionIsPartial,
      String? projectedProfitLoss,
      List<String> notes = const [],
    }) =>
        {
          'crop_cycle_id': 'cycle-1',
          'estimated_cost': estimatedCost,
          'actual_cost': actualCost,
          'remaining_estimated_cost': remainingEstimatedCost,
          'projected_total_cost': projectedTotalCost,
          'actual_revenue': actualRevenue,
          'committed_revenue': committedRevenue,
          'potential_additional_revenue': potentialAdditionalRevenue,
          'potential_additional_revenue_basis': potentialAdditionalRevenueBasis,
          'projected_total_revenue': projectedTotalRevenue,
          'revenue_projection_is_partial': revenueProjectionIsPartial,
          'projected_profit_loss': projectedProfitLoss,
          'projected_profit_loss_percent': null,
          'data_completeness_notes': notes,
        };

    test('no data at all parses honestly - nulls stay null, actuals stay real zeros', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        estimatedCost: null,
        actualCost: '0',
        actualRevenue: '0',
        committedRevenue: '0',
        projectedTotalRevenue: '0',
        revenueProjectionIsPartial: true,
        notes: ['No cost estimate entered yet.'],
      ));
      expect(forecast.estimatedCost, isNull);
      expect(forecast.projectedTotalCost, isNull);
      expect(forecast.actualCost, '0');
      expect(forecast.dataCompletenessNotes, ['No cost estimate entered yet.']);
    });

    test('committed revenue is distinct from actual revenue - never merged', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        actualCost: '0',
        actualRevenue: '500.00',
        committedRevenue: '1200.00',
        projectedTotalRevenue: '1700.00',
        revenueProjectionIsPartial: true,
      ));
      expect(forecast.actualRevenue, '500.00');
      expect(forecast.committedRevenue, '1200.00');
      expect(forecast.projectedTotalRevenue, '1700.00');
    });

    test('potential additional revenue carries its basis explanation when present', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        actualCost: '0',
        actualRevenue: '0',
        committedRevenue: '0',
        potentialAdditionalRevenue: '25000.00',
        potentialAdditionalRevenueBasis: '1000.00 kg (estimated yield) x Rs 25.00/kg (your listing price)',
        projectedTotalRevenue: '25000.00',
        revenueProjectionIsPartial: false,
      ));
      expect(forecast.potentialAdditionalRevenue, '25000.00');
      expect(forecast.potentialAdditionalRevenueBasis, contains('estimated yield'));
      expect(forecast.revenueProjectionIsPartial, isFalse);
    });

    test('revenueProjectionIsPartial true means potential revenue is null - the flag and the null are always consistent', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        actualCost: '0',
        actualRevenue: '0',
        committedRevenue: '0',
        potentialAdditionalRevenue: null,
        projectedTotalRevenue: '0',
        revenueProjectionIsPartial: true,
      ));
      expect(forecast.potentialAdditionalRevenue, isNull);
      expect(forecast.revenueProjectionIsPartial, isTrue);
    });

    test('projectedProfitLoss is null whenever projectedTotalCost is null - cannot project profit without a cost baseline', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        estimatedCost: null,
        projectedTotalCost: null,
        actualCost: '400.00',
        actualRevenue: '0',
        committedRevenue: '0',
        projectedTotalRevenue: '0',
        revenueProjectionIsPartial: true,
        projectedProfitLoss: null,
      ));
      expect(forecast.projectedTotalCost, isNull);
      expect(forecast.projectedProfitLoss, isNull);
    });

    test('data completeness notes list parses correctly, including multiple notes', () {
      final forecast = CropProfitForecast.fromJson(forecastJson(
        actualCost: '0',
        actualRevenue: '0',
        committedRevenue: '0',
        projectedTotalRevenue: '0',
        revenueProjectionIsPartial: true,
        notes: ['No cost estimate entered yet.', 'No harvest record exists yet.'],
      ));
      expect(forecast.dataCompletenessNotes.length, 2);
    });
  });

  group('CropCostEstimate (Phase 31)', () {
    test('parses with an optional stage tag', () {
      final estimate = CropCostEstimate.fromJson({
        'id': 'estimate-1',
        'crop_cycle_id': 'cycle-1',
        'crop_stage_definition_id': 'stage-1',
        'category': 'seed',
        'estimated_amount': '500.00',
        'description': null,
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(estimate.cropStageDefinitionId, 'stage-1');
      expect(estimate.estimatedAmount, '500.00');
    });

    test('parses without a stage tag (general estimate)', () {
      final estimate = CropCostEstimate.fromJson({
        'id': 'estimate-1',
        'crop_cycle_id': 'cycle-1',
        'crop_stage_definition_id': null,
        'category': 'seed',
        'estimated_amount': '500.00',
        'description': null,
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(estimate.cropStageDefinitionId, isNull);
    });
  });
}
