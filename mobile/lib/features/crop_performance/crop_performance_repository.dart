import '../../core/api_client.dart';
import 'crop_performance_models.dart';

class CropPerformanceRepository {
  final ApiClient _apiClient;
  CropPerformanceRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<PerformanceScore> getPerformanceScore(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/performance');
    return PerformanceScore.fromJson(response);
  }

  Future<CropComparison> compareCropCycles(String cropCycleId, String otherCropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/comparison/$otherCropCycleId');
    return CropComparison.fromJson(response);
  }

  Future<InputRoi> getInputRoi(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/input-roi');
    return InputRoi.fromJson(response);
  }

  Future<IrrigationIntelligence> getIrrigationIntelligence(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/irrigation-intelligence');
    return IrrigationIntelligence.fromJson(response);
  }
}
