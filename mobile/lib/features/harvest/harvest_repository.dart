import '../../core/api_client.dart';
import 'harvest_models.dart';

class HarvestRepository {
  final ApiClient _apiClient;
  HarvestRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Returns the most recently created harvest for this crop cycle, or
  /// creates one if none exists yet - matches the backend's own
  /// get-or-create semantics exactly (POST, no body).
  Future<HarvestRecord> getOrCreateHarvestForCropCycle(String cropCycleId) async {
    final response = await _apiClient.post('/harvests/from-crop-cycle/$cropCycleId');
    return HarvestRecord.fromJson(response);
  }

  /// Always inserts a new harvest row for this crop cycle, even if one
  /// already exists - for legitimate multi-harvest crops only.
  Future<HarvestRecord> createNewHarvestForCropCycle(String cropCycleId) async {
    final response = await _apiClient.post('/harvests/from-crop-cycle/$cropCycleId/new-harvest');
    return HarvestRecord.fromJson(response);
  }

  Future<List<HarvestRecord>> listHarvestsForCropCycle(String cropCycleId) async {
    final response = await _apiClient.get('/harvests/from-crop-cycle/$cropCycleId');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(HarvestRecord.fromJson).toList();
  }

  Future<List<HarvestRecord>> listMyHarvests({int limit = 100, int offset = 0}) async {
    final response = await _apiClient.get('/harvests?limit=$limit&offset=$offset');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(HarvestRecord.fromJson).toList();
  }

  /// Only takes effect while the harvest's status is still `planned` - a
  /// silent no-op otherwise, matching the backend's own behavior exactly.
  Future<HarvestRecord> markApproaching(String harvestId) async {
    final response = await _apiClient.post('/harvests/$harvestId/approaching');
    return HarvestRecord.fromJson(response);
  }

  Future<HarvestRecord> confirmReady({
    required String harvestId,
    String? actualHarvestDate,
    String? estimatedQuantity,
  }) async {
    final response = await _apiClient.post('/harvests/$harvestId/confirm-ready', body: {
      if (actualHarvestDate != null) 'actual_harvest_date': actualHarvestDate,
      if (estimatedQuantity != null) 'estimated_quantity': estimatedQuantity,
    });
    return HarvestRecord.fromJson(response);
  }

  /// Throws ApiException(code: 'DUPLICATE_LISTING_WARNING') if an active
  /// listing already exists for this harvest and confirmDuplicate is
  /// false - callers should offer the farmer a way to retry with
  /// confirmDuplicate: true rather than treating it as a plain failure.
  Future<HarvestListing> createListing({
    required String harvestId,
    required String quantityAvailable,
    required String unit,
    required String deliveryOption,
    String? qualityGrade,
    String? expectedAvailabilityDate,
    Map<String, dynamic>? serviceArea,
    String? preferredPrice,
    String? notes,
    bool confirmDuplicate = false,
  }) async {
    final response = await _apiClient.post('/harvests/$harvestId/listing', body: {
      'quantity_available': quantityAvailable,
      'unit': unit,
      'delivery_option': deliveryOption,
      if (qualityGrade != null) 'quality_grade': qualityGrade,
      if (expectedAvailabilityDate != null) 'expected_availability_date': expectedAvailabilityDate,
      if (serviceArea != null) 'service_area': serviceArea,
      if (preferredPrice != null) 'preferred_price': preferredPrice,
      if (notes != null) 'notes': notes,
      'confirm_duplicate': confirmDuplicate,
    });
    return HarvestListing.fromJson(response);
  }

  Future<List<HarvestListing>> listMyListings({int limit = 100, int offset = 0}) async {
    final response = await _apiClient.get('/harvests/listings/me?limit=$limit&offset=$offset');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(HarvestListing.fromJson).toList();
  }
}
