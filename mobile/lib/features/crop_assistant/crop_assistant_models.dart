/// Mirrors backend/app/schemas/crop_assistant.py exactly. This model has
/// no field for a persisted conversation - the backend is deliberately
/// stateless for this crop-scoped assistant. contextUsed lists the
/// exact real data sources that backed the answer; limitations states
/// in plain language what was missing.
library;

class CropAssistantResponse {
  final String cropCycleId;
  final String intent;
  final String answer;
  final List<String> contextUsed;
  final List<String> limitations;

  CropAssistantResponse({
    required this.cropCycleId,
    required this.intent,
    required this.answer,
    required this.contextUsed,
    required this.limitations,
  });

  factory CropAssistantResponse.fromJson(Map<String, dynamic> json) => CropAssistantResponse(
        cropCycleId: json['crop_cycle_id'] as String,
        intent: json['intent'] as String,
        answer: json['answer'] as String,
        contextUsed: (json['context_used'] as List).cast<String>(),
        limitations: (json['limitations'] as List).cast<String>(),
      );
}
