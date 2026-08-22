import '../../core/api_client.dart';
import 'crop_risk_models.dart';

class CropRiskRepository {
  final ApiClient _apiClient;
  CropRiskRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropRiskScore> getRiskScore(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/risk-score');
    return CropRiskScore.fromJson(response);
  }
}
