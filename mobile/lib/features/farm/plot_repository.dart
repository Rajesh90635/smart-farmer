import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import '../crop_photo/network_status_checker.dart';
import 'farm_models.dart';

class PlotRepository {
  final ApiClient _apiClient;
  PlotRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<List<Plot>> listPlotsForFarm(String farmId) async {
    final response = await _apiClient.get('/farms/$farmId/plots');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Plot.fromJson).toList();
  }

  Future<Plot> getPlot(String plotId) async {
    final response = await _apiClient.get('/plots/$plotId');
    return Plot.fromJson(response);
  }

  /// D81-02 (docs/audit/FINAL_CANONICAL_group_D.md): same optional-param
  /// offline-queueing shape as FarmRepository.createFarm (D81-01) - see
  /// that method's own docstring. Omitting both params preserves the
  /// exact prior always-online behavior unchanged.
  Future<Plot> createPlot(
    String farmId, {
    required String plotName,
    required double areaValue,
    required String areaUnit,
    String? soilType,
    String? irrigationType,
    NetworkStatusChecker? networkChecker,
    PendingWriteQueue? writeQueue,
  }) async {
    final body = {
      'plot_name': plotName,
      'area_value': areaValue,
      'area_unit': areaUnit,
      if (soilType != null) 'soil_type': soilType,
      if (irrigationType != null) 'irrigation_type': irrigationType,
    };

    if (networkChecker != null && writeQueue != null && !(await networkChecker.isOnline())) {
      await writeQueue.enqueue(PendingWrite(clientRequestId: generateClientRequestId(), method: 'POST', path: '/farms/$farmId/plots', body: body));
      throw const QueuedForSyncException();
    }

    final response = await _apiClient.post('/farms/$farmId/plots', body: body);
    return Plot.fromJson(response);
  }

  Future<Plot> updatePlot(String plotId, {String? plotName, double? areaValue, String? areaUnit}) async {
    final response = await _apiClient.put('/plots/$plotId', body: {
      if (plotName != null) 'plot_name': plotName,
      if (areaValue != null) 'area_value': areaValue,
      if (areaUnit != null) 'area_unit': areaUnit,
    });
    return Plot.fromJson(response);
  }

  Future<void> deactivatePlot(String plotId) async {
    await _apiClient.delete('/plots/$plotId');
  }
}
