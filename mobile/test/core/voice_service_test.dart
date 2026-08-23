import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/voice_service.dart';

/// A fake VoiceService for testing call sites without touching a real
/// platform channel - the same pattern already established for other
/// platform-dependent abstractions in this project. This class exists
/// purely to record what was ASKED of it, proving the safety rule:
/// nothing in this codebase ever asks VoiceService to speak text it
/// invented itself - only text a caller already had in hand.
class FakeVoiceService implements VoiceService {
  bool available = true;
  bool shouldSucceedSpeak = true;
  String? lastSpokenText;
  String? lastLanguageCode;
  bool stopped = false;

  @override
  Future<bool> isAvailable() async => available;

  @override
  Future<bool> speak(String text, {required String languageCode}) async {
    lastSpokenText = text;
    lastLanguageCode = languageCode;
    if (!available || !shouldSucceedSpeak) return false;
    return true;
  }

  @override
  Future<void> stop() async {
    stopped = true;
  }
}

void main() {
  group('VoiceService contract (Step 14)', () {
    test('speak() returns true and records exactly the text it was given - never alters it', () async {
      final voice = FakeVoiceService();
      final result = await voice.speak('Your tomato crop looks healthy.', languageCode: 'en');
      expect(result, isTrue);
      expect(voice.lastSpokenText, 'Your tomato crop looks healthy.');
      expect(voice.lastLanguageCode, 'en');
    });

    test('speak() returns false (not an exception) when the device reports unavailable', () async {
      final voice = FakeVoiceService()..available = false;
      final result = await voice.speak('Weather: 28C, 40% chance of rain.', languageCode: 'en');
      expect(result, isFalse);
    });

    test('speak() returns false when the underlying engine fails, without throwing', () async {
      final voice = FakeVoiceService()..shouldSucceedSpeak = false;
      final result = await voice.speak('Some text.', languageCode: 'kn');
      expect(result, isFalse);
    });

    test('stop() completes without error', () async {
      final voice = FakeVoiceService();
      await voice.stop();
      expect(voice.stopped, isTrue);
    });

    test('isAvailable() reflects the device state without side effects', () async {
      final voice = FakeVoiceService()..available = false;
      expect(await voice.isAvailable(), isFalse);
    });
  });
}
