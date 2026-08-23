import '../../core/api_client.dart';
import '../weather/weather_models.dart';
import 'farm_models.dart';

class FarmRepository {
  final ApiClient _apiClient;
  FarmRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<List<Farm>> listMyFarms() async {
    final response = await _apiClient.get('/farms');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Farm.fromJson).toList();
  }

  Future<Farm> getFarm(String farmId) async {
    final response = await _apiClient.get('/farms/$farmId');
    return Farm.fromJson(response);
  }

  Future<Farm> createFarm({
    required String farmName,
    String? description,
    double? latitude,
    double? longitude,
    int? stateId,
    int? districtId,
    int? mandalId,
    int? villageId,
    required double areaValue,
    required String areaUnit,
  }) async {
    final response = await _apiClient.post('/farms', body: {
      'farm_name': farmName,
      if (description != null) 'description': description,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
      if (stateId != null) 'state_id': stateId,
      if (districtId != null) 'district_id': districtId,
      if (mandalId != null) 'mandal_id': mandalId,
      if (villageId != null) 'village_id': villageId,
      'area_value': areaValue,
      'area_unit': areaUnit,
    });
    return Farm.fromJson(response);
  }

  Future<Farm> updateFarm(
    String farmId, {
    String? farmName,
    String? description,
    double? areaValue,
    String? areaUnit,
  }) async {
    final response = await _apiClient.put('/farms/$farmId', body: {
      if (farmName != null) 'farm_name': farmName,
      if (description != null) 'description': description,
      if (areaValue != null) 'area_value': areaValue,
      if (areaUnit != null) 'area_unit': areaUnit,
    });
    return Farm.fromJson(response);
  }

  Future<void> deactivateFarm(String farmId) async {
    await _apiClient.delete('/farms/$farmId');
  }

  /// Reuses the EXISTING, already-complete weather endpoint - no second
  /// weather repository/pipeline created. Ownership is enforced entirely
  /// server-side (backend/app/repositories/farm_repository.py's
  /// get_owned) - this method never trusts a farmId the farmer doesn't
  /// actually own; a mismatch simply returns 404 like every other
  /// farm-scoped call in this app.
  Future<FarmWeather> getWeather(String farmId) async {
    final response = await _apiClient.get('/farms/$farmId/weather');
    return FarmWeather.fromJson(response);
  }
}
