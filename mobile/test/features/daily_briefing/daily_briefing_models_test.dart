import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/daily_briefing/daily_briefing_models.dart';

void main() {
  group('DailyBriefing (Step 14)', () {
    test('parses real backend fields exactly, without adding or inventing lines', () {
      final json = {
        'language_code': 'en',
        'lines': ['Weather: 28.0°C, 40% chance of rain today.', 'Crop: your tomato is at the flowering stage.'],
        'generated_at': '2026-01-01T06:00:00Z',
      };
      final briefing = DailyBriefing.fromJson(json);
      expect(briefing.lines.length, 2);
      expect(briefing.lines, json['lines']);
    });

    test('honest empty-farm fallback is rendered as a normal line, not specially fabricated', () {
      final json = {
        'language_code': 'en',
        'lines': ['No new updates for your farm right now.'],
        'generated_at': '2026-01-01T06:00:00Z',
      };
      final briefing = DailyBriefing.fromJson(json);
      expect(briefing.lines, ['No new updates for your farm right now.']);
    });

    test('audioText is derived only from the on-screen lines - never a separately generated voice summary', () {
      final briefing = DailyBriefing(
        languageCode: 'en',
        lines: ['Weather: 28C, 40% chance of rain.', 'Harvest: currently approaching.'],
        generatedAt: '2026-01-01T06:00:00Z',
      );
      for (final line in briefing.lines) {
        expect(briefing.audioText.contains(line), isTrue);
      }
    });

    test('a single-line briefing produces audioText identical to that one line', () {
      final briefing = DailyBriefing(languageCode: 'en', lines: ['No new updates for your farm right now.'], generatedAt: '2026-01-01T06:00:00Z');
      expect(briefing.audioText, 'No new updates for your farm right now.');
    });
  });
}
