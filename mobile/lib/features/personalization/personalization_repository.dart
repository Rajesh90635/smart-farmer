import '../../core/api_client.dart';
import 'personalization_models.dart';

class PersonalizationRepository {
  final ApiClient _apiClient;
  PersonalizationRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<PersonalizationProfile> getProfile() async {
    final response = await _apiClient.get('/farmers/me/personalization');
    return PersonalizationProfile.fromJson(response);
  }

  Future<AdvisoryFeedback> submitFeedback({
    required String cropCycleId,
    required String sourceType,
    String? sourceReference,
    required String feedbackType,
    String? note,
  }) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/advisory-feedback', body: {
      'source_type': sourceType,
      if (sourceReference != null) 'source_reference': sourceReference,
      'feedback_type': feedbackType,
      if (note != null) 'note': note,
    });
    return AdvisoryFeedback.fromJson(response);
  }

  Future<LearningSummary> getLearningSummary(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/learning-summary');
    return LearningSummary.fromJson(response);
  }
}
