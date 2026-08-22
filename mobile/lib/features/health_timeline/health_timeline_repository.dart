import '../../core/api_client.dart';
import 'health_timeline_models.dart';

class HealthTimelineRepository {
  final ApiClient _apiClient;
  HealthTimelineRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropHealthTimeline> getTimeline(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/health-timeline');
    return CropHealthTimeline.fromJson(response);
  }
}
