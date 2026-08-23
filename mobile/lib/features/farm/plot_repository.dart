import '../../core/api_client.dart';
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

  Future<Plot> createPlot(
    String farmId, {
    required String plotName,
    required double areaValue,
    required String areaUnit,
    String? soilType,
    String? irrigationType,
  }) async {
    final response = await _apiClient.post('/farms/$farmId/plots', body: {
      'plot_name': plotName,
      'area_value': areaValue,
      'area_unit': areaUnit,
      if (soilType != null) 'soil_type': soilType,
      if (irrigationType != null) 'irrigation_type': irrigationType,
    });
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
