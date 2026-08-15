/// Mirrors backend/app/schemas/assistant.py:DailySummaryResponse exactly
/// (language_code, lines, generated_at) - `lines` are ALREADY-composed,
/// real farmer-facing sentences from actual tool data (weather/crop/
/// harvest/marketplace/delivery/expert-case), never generated or altered
/// here. This class has no field or method that could add a line beyond
/// what the backend actually sent.
library;

class DailyBriefing {
  final String languageCode;
  final List<String> lines;
  final String generatedAt;

  DailyBriefing({required this.languageCode, required this.lines, required this.generatedAt});

  /// The exact text spoken by Listen - simply the same lines already
  /// shown on screen, joined with a pause-friendly separator. No
  /// separate "voice summary" is ever generated - screen and audio can
  /// never disagree, because they are the same text.
  String get audioText => lines.join('. ');

  factory DailyBriefing.fromJson(Map<String, dynamic> json) => DailyBriefing(
        languageCode: json['language_code'] as String,
        lines: (json['lines'] as List).cast<String>(),
        generatedAt: json['generated_at'] as String,
      );
}
