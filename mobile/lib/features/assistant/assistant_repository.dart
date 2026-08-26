import '../../core/api_client.dart';
import 'assistant_models.dart';

class AssistantRepository {
  final ApiClient _apiClient;
  AssistantRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// The farmer's current active conversation, or an empty result if
  /// they've never sent a message yet - never creates one just from
  /// opening the screen (see backend/app/api/v1/assistant.py's GET
  /// /assistant/history, added for this screen).
  Future<ConversationHistory> getActiveHistory() async {
    final response = await _apiClient.get('/assistant/history');
    return ConversationHistory.fromJson(response);
  }

  Future<ChatTurnResult> sendMessage(String message, {String? conversationId}) async {
    final response = await _apiClient.post('/assistant/chat', body: {
      'message': message,
      if (conversationId != null) 'conversation_id': conversationId,
    });
    return ChatTurnResult.fromJson(response);
  }

  Future<void> submitFeedback(String messageId, {required bool helpful}) async {
    await _apiClient.post('/assistant/feedback/$messageId', body: {
      'feedback_type': helpful ? 'helpful' : 'not_helpful',
    });
  }
}
