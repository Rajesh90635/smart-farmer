import '../../core/api_client.dart';
import 'farm_models.dart';

class CropRepository {
  final ApiClient _apiClient;
  CropRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<List<CropMaster>> searchCropMaster(String? query) async {
    final path = query != null && query.isNotEmpty ? '/crops/master?query=$query' : '/crops/master';
    final response = await _apiClient.getList(path);
    return response.cast<Map<String, dynamic>>().map(CropMaster.fromJson).toList();
  }

  Future<List<CropCycle>> listCropCyclesForPlot(String plotId) async {
    final response = await _apiClient.get('/plots/$plotId/crops');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(CropCycle.fromJson).toList();
  }

  /// Farmer-wide, across every farm/plot - for pickers (the Camera tab's
  /// "which crop am I checking" step) that have no plot/crop context of
  /// their own to scope a request to.
  Future<List<CropCycle>> listAllMyCropCycles() async {
    final response = await _apiClient.get('/crops');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(CropCycle.fromJson).toList();
  }

  Future<CropCycle> getCropCycle(String cropCycleId) async {
    final response = await _apiClient.get('/crops/$cropCycleId');
    return CropCycle.fromJson(response);
  }

  Future<CropCycle> createCropCycle(
    String plotId, {
    required String cropId,
    String? season,
    required String sowingDate,
    String? expectedHarvestDate,
    String? seedVariety,
  }) async {
    final response = await _apiClient.post('/plots/$plotId/crops', body: {
      'crop_id': cropId,
      if (season != null) 'season': season,
      'sowing_date': sowingDate,
      if (expectedHarvestDate != null) 'expected_harvest_date': expectedHarvestDate,
      if (seedVariety != null) 'seed_variety': seedVariety,
    });
    return CropCycle.fromJson(response);
  }

  Future<CropCycle> updateCropCycleStatus(String cropCycleId, String cultivationStatus) async {
    final response = await _apiClient.put('/crops/$cropCycleId', body: {'cultivation_status': cultivationStatus});
    return CropCycle.fromJson(response);
  }

  Future<CropCycle> closeCropCycle(String cropCycleId, String actualHarvestDate) async {
    final response =
        await _apiClient.post('/crops/$cropCycleId/close', body: {'actual_harvest_date': actualHarvestDate});
    return CropCycle.fromJson(response);
  }
}
