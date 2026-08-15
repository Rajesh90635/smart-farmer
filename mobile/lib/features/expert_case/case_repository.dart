import '../../core/api_client.dart';
import 'case_models.dart';

/// Farmer-facing subset only - accept/decline/review are professional-role
/// endpoints (require_role(expert/field_agent)), out of scope per Step 13's
/// own instruction to implement the farmer-side request/status flow first
/// and report expert-side UI as a remaining limitation.
class CaseRepository {
  final ApiClient _apiClient;
  CaseRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<ExpertCase> createCase({
    required String cropCycleId,
    String? cropPhotoId,
    String? aiAnalysisId,
    required String requestedProfessionalRole,
    required String reason,
    required List<String> consentSharedItems,
  }) async {
    final response = await _apiClient.post('/cases', body: {
      'crop_cycle_id': cropCycleId,
      if (cropPhotoId != null) 'crop_photo_id': cropPhotoId,
      if (aiAnalysisId != null) 'ai_analysis_id': aiAnalysisId,
      'requested_professional_role': requestedProfessionalRole,
      'reason': reason,
      'consent_shared_items': consentSharedItems,
    });
    return ExpertCase.fromJson(response);
  }

  Future<ExpertCase> getCase(String caseId) async {
    final response = await _apiClient.get('/cases/$caseId');
    return ExpertCase.fromJson(response);
  }

  Future<List<ExpertCase>> listMyCases() async {
    final response = await _apiClient.get('/cases');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(ExpertCase.fromJson).toList();
  }

  Future<ExpertCase> closeCase(String caseId) async {
    final response = await _apiClient.post('/cases/$caseId/close');
    return ExpertCase.fromJson(response);
  }

  Future<List<CaseAuditEntry>> getCaseAudit(String caseId) async {
    final response = await _apiClient.getList('/cases/$caseId/audit');
    return response.map((e) => CaseAuditEntry.fromJson(e as Map<String, dynamic>)).toList();
  }
}
