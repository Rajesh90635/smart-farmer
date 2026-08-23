import '../../core/api_client.dart';
import 'crop_assistant_models.dart';

class CropAssistantRepository {
  final ApiClient _apiClient;
  CropAssistantRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropAssistantResponse> askQuestion(String cropCycleId, String question) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/assistant', body: {'question': question});
    return CropAssistantResponse.fromJson(response);
  }
}
