import '../../core/api_client.dart';
import 'weather_action_models.dart';

class WeatherActionRepository {
  final ApiClient _apiClient;
  WeatherActionRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropWeatherAction> getWeatherActions(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/weather-actions');
    return CropWeatherAction.fromJson(response);
  }
}
