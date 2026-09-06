import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import '../crop_photo/network_status_checker.dart';
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

  /// D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): when both
  /// `networkChecker` and `writeQueue` are supplied AND the device is
  /// offline, the write is queued instead of sent, and this throws
  /// `QueuedForSyncException` (a distinct, non-error outcome) instead of
  /// returning a `Farm` - there is no server-assigned id yet to return.
  /// Omitting either param (the default) preserves the exact prior
  /// always-online behavior unchanged - every existing call site/test
  /// keeps working without modification.
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
    NetworkStatusChecker? networkChecker,
    PendingWriteQueue? writeQueue,
  }) async {
    final body = {
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
    };

    if (networkChecker != null && writeQueue != null && !(await networkChecker.isOnline())) {
      await writeQueue.enqueue(PendingWrite(clientRequestId: generateClientRequestId(), method: 'POST', path: '/farms', body: body));
      throw const QueuedForSyncException();
    }

    final response = await _apiClient.post('/farms', body: body);
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
