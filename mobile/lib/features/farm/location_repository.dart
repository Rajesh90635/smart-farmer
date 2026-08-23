import '../../core/api_client.dart';
import 'location_models.dart';

/// Read-only state/district/mandal/village dropdown data - mirrors
/// backend/app/api/v1/location.py exactly. No write endpoints exist (see
/// that router's own docstring): this data is seeded via migration
/// (states/districts) or added the same way later (mandals/villages,
/// currently empty - no authoritative dataset exists yet, so those
/// dropdowns may legitimately come back empty).
class LocationRepository {
  final ApiClient _apiClient;
  LocationRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<List<LocationOption>> listStates() async {
    final items = await _apiClient.getList('/states');
    return items.cast<Map<String, dynamic>>().map(LocationOption.fromJson).toList();
  }

  Future<List<LocationOption>> listDistricts(int stateId) async {
    final items = await _apiClient.getList('/states/$stateId/districts');
    return items.cast<Map<String, dynamic>>().map(LocationOption.fromJson).toList();
  }

  Future<List<LocationOption>> listMandals(int districtId) async {
    final items = await _apiClient.getList('/districts/$districtId/mandals');
    return items.cast<Map<String, dynamic>>().map(LocationOption.fromJson).toList();
  }

  Future<List<LocationOption>> listVillages(int mandalId) async {
    final items = await _apiClient.getList('/mandals/$mandalId/villages');
    return items.cast<Map<String, dynamic>>().map(LocationOption.fromJson).toList();
  }
}
