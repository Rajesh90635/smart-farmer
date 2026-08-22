import '../../core/api_client.dart';
import 'treatment_models.dart';

class TreatmentRepository {
  final ApiClient _apiClient;
  TreatmentRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<TreatmentRecord> createTreatment({
    required String cropCycleId,
    required String applicationDate,
    String? notes,
    String? caseId,
    String? productId,
  }) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/treatments', body: {
      'application_date': applicationDate,
      if (notes != null) 'notes': notes,
      if (caseId != null) 'case_id': caseId,
      if (productId != null) 'product_id': productId,
    });
    return TreatmentRecord.fromJson(response);
  }

  Future<List<TreatmentRecord>> listTreatments(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/treatments');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(TreatmentRecord.fromJson).toList();
  }

  Future<TreatmentFollowUp> createFollowUp({
    required String treatmentId,
    required String observationDate,
    String? afterAnalysisId,
    String? notes,
  }) async {
    final response = await _apiClient.post('/treatments/$treatmentId/follow-ups', body: {
      'observation_date': observationDate,
      if (afterAnalysisId != null) 'after_analysis_id': afterAnalysisId,
      if (notes != null) 'notes': notes,
    });
    return TreatmentFollowUp.fromJson(response);
  }

  Future<List<TreatmentFollowUp>> listFollowUps(String treatmentId) async {
    final response = await _apiClient.get('/treatments/$treatmentId/follow-ups');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(TreatmentFollowUp.fromJson).toList();
  }

  Future<TreatmentEffectiveness> getEffectiveness(String treatmentId) async {
    final response = await _apiClient.get('/treatments/$treatmentId/effectiveness');
    return TreatmentEffectiveness.fromJson(response);
  }
}
