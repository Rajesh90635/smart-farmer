/// Mirrors backend/app/schemas/assistant.py exactly - the persisted,
/// farmer-wide AI Assistant (distinct from the stateless, crop-scoped
/// CropAssistantResponse in features/crop_assistant/). Every field here
/// is a verbatim backend value: intent/sources/confidence are shown,
/// never recomputed or upgraded client-side.
library;

class ChatMessage {
  final String id;
  final String role; // 'farmer' | 'assistant'
  final String content;
  final String languageCode;
  final String? intent;
  final List<String>? toolsCalled;
  final List<String>? sources;
  final String? confidence;
  final DateTime createdAt;

  ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.languageCode,
    required this.intent,
    required this.toolsCalled,
    required this.sources,
    required this.confidence,
    required this.createdAt,
  });

  bool get isFromFarmer => role == 'farmer';

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
        id: json['id'] as String,
        role: json['role'] as String,
        content: json['content'] as String,
        languageCode: json['language_code'] as String,
        intent: json['intent'] as String?,
        toolsCalled: (json['tools_called'] as List?)?.cast<String>(),
        sources: (json['sources'] as List?)?.cast<String>(),
        confidence: json['confidence'] as String?,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class ConversationHistory {
  final String? conversationId;
  final List<ChatMessage> messages;

  ConversationHistory({required this.conversationId, required this.messages});

  factory ConversationHistory.fromJson(Map<String, dynamic> json) => ConversationHistory(
        conversationId: json['conversation_id'] as String?,
        messages: (json['messages'] as List)
            .map((m) => ChatMessage.fromJson(m as Map<String, dynamic>))
            .toList(),
      );
}

class ChatTurnResult {
  final String conversationId;
  final ChatMessage farmerMessage;
  final ChatMessage assistantMessage;

  ChatTurnResult({required this.conversationId, required this.farmerMessage, required this.assistantMessage});

  factory ChatTurnResult.fromJson(Map<String, dynamic> json) => ChatTurnResult(
        conversationId: json['conversation_id'] as String,
        farmerMessage: ChatMessage.fromJson(json['farmer_message'] as Map<String, dynamic>),
        assistantMessage: ChatMessage.fromJson(json['assistant_message'] as Map<String, dynamic>),
      );
}
