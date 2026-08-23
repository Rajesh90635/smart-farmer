import '../../core/api_client.dart';
import 'crop_financial_models.dart';

class CropFinancialRepository {
  final ApiClient _apiClient;
  CropFinancialRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropFinancialSummary> getFinancialSummary(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/financial-summary');
    return CropFinancialSummary.fromJson(response);
  }

  Future<CropProfitForecast> getProfitForecast(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/profit-forecast');
    return CropProfitForecast.fromJson(response);
  }

  Future<CropCostEstimate> createEstimate({
    required String cropCycleId,
    required String category,
    required String estimatedAmount,
    String? description,
    String? cropStageDefinitionId,
  }) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/cost-estimates', body: {
      'category': category,
      'estimated_amount': estimatedAmount,
      if (description != null) 'description': description,
      if (cropStageDefinitionId != null) 'crop_stage_definition_id': cropStageDefinitionId,
    });
    return CropCostEstimate.fromJson(response);
  }

  Future<List<CropCostEstimate>> listEstimates(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/cost-estimates');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(CropCostEstimate.fromJson).toList();
  }

  Future<void> deleteEstimate(String estimateId) async {
    await _apiClient.delete('/cost-estimates/$estimateId');
  }
}
