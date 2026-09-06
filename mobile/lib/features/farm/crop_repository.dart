import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import '../crop_photo/network_status_checker.dart';
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

  /// Structured varieties for a crop (e.g. "Pusa Ruby" for Tomato), used to
  /// populate the optional variety dropdown after a crop is selected.
  Future<List<CropVariety>> listVarietiesForCrop(String cropId) async {
    final response = await _apiClient.getList('/crops/$cropId/varieties');
    return response.cast<Map<String, dynamic>>().map(CropVariety.fromJson).toList();
  }

  /// D81-03 (docs/audit/FINAL_CANONICAL_group_D.md): same optional-param
  /// offline-queueing shape as FarmRepository.createFarm (D81-01).
  Future<CropCycle> createCropCycle(
    String plotId, {
    required String cropId,
    String? season,
    required String sowingDate,
    String? expectedHarvestDate,
    String? seedVariety,
    String? varietyId,
    String? resownFromCropCycleId,
    NetworkStatusChecker? networkChecker,
    PendingWriteQueue? writeQueue,
  }) async {
    final body = {
      'crop_id': cropId,
      if (season != null) 'season': season,
      'sowing_date': sowingDate,
      if (expectedHarvestDate != null) 'expected_harvest_date': expectedHarvestDate,
      if (seedVariety != null) 'seed_variety': seedVariety,
      if (varietyId != null) 'variety_id': varietyId,
      // D11-02 (docs/audit/FINAL_CANONICAL_group_A.md): only ever sent
      // when the farmer explicitly confirms the re-sow prompt below -
      // never inferred or auto-set.
      if (resownFromCropCycleId != null) 'resown_from_crop_cycle_id': resownFromCropCycleId,
    };

    if (networkChecker != null && writeQueue != null && !(await networkChecker.isOnline())) {
      await writeQueue.enqueue(PendingWrite(clientRequestId: generateClientRequestId(), method: 'POST', path: '/plots/$plotId/crops', body: body));
      throw const QueuedForSyncException();
    }

    final response = await _apiClient.post('/plots/$plotId/crops', body: body);
    return CropCycle.fromJson(response);
  }

  Future<CropCycle> updateCropCycleStatus(String cropCycleId, String cultivationStatus) async {
    final response = await _apiClient.put('/crops/$cropCycleId', body: {'cultivation_status': cultivationStatus});
    return CropCycle.fromJson(response);
  }

  Future<CropCycle> closeCropCycle(String cropCycleId, String actualHarvestDate, {String? lessonsLearned}) async {
    final response = await _apiClient.post('/crops/$cropCycleId/close', body: {
      'actual_harvest_date': actualHarvestDate,
      if (lessonsLearned != null) 'lessons_learned': lessonsLearned,
    });
    return CropCycle.fromJson(response);
  }
}
