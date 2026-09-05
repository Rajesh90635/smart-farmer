import '../../core/api_client.dart';
import 'daily_briefing_models.dart';

class DailyBriefingRepository {
  final ApiClient _apiClient;
  DailyBriefingRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// [languageCodeOverride], when given, asks the backend to compose this
  /// one response in a different language than the farmer's saved profile
  /// preference (used for location-based audio language detection) -
  /// never persisted, never changes the farmer's actual preference.
  Future<DailyBriefing> getDailyBriefing({String? languageCodeOverride}) async {
    final path = languageCodeOverride == null
        ? '/assistant/daily-summary'
        : '/assistant/daily-summary?language_code=$languageCodeOverride';
    final response = await _apiClient.get(path);
    return DailyBriefing.fromJson(response);
  }
}
