import '../../core/api_client.dart';
import 'daily_briefing_models.dart';

class DailyBriefingRepository {
  final ApiClient _apiClient;
  DailyBriefingRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<DailyBriefing> getDailyBriefing() async {
    final response = await _apiClient.get('/assistant/daily-summary');
    return DailyBriefing.fromJson(response);
  }
}
