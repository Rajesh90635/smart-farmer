import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:smart_farmer_mobile/core/flutter_tts_voice_service.dart';

// FlutterTts's constructor registers a platform method call handler, which
// asserts a binary messenger already exists - needs the test binding
// initialized even though these are otherwise plain unit tests.
void _ensureBinding() => TestWidgetsFlutterBinding.ensureInitialized();

/// Simulates the real, observed web behavior: the underlying
/// speechSynthesis.getVoices() reports zero voices on the first call right
/// after page load (voices load asynchronously) and a non-empty list on
/// every call after that - confirmed live: 0 voices immediately after
/// load, 3 voices ~1.5s later in the same browser session.
class _FlakyFirstCallTts extends FlutterTts {
  int getLanguagesCallCount = 0;

  @override
  Future<dynamic> get getLanguages async {
    getLanguagesCallCount++;
    return getLanguagesCallCount == 1 ? <String>[] : <String>['en-US', 'hi-IN'];
  }

  @override
  Future<dynamic> setLanguage(String language) async => 1;

  @override
  Future<dynamic> speak(String text, {bool focus = false}) async => 1;
}

void main() {
  _ensureBinding();

  group('FlutterTtsVoiceService availability caching', () {
    test('a losing first race does not permanently disable voice for the session', () async {
      final tts = _FlakyFirstCallTts();
      final voice = FlutterTtsVoiceService(tts: tts);

      // First check loses the race (browser hasn't loaded voices yet) -
      // must report unavailable, not throw.
      expect(await voice.isAvailable(), isFalse);

      // A LATER check (e.g. tapping "Listen" again, or on another screen)
      // must get a fresh look, not a permanently cached false.
      expect(await voice.isAvailable(), isTrue);
      expect(tts.getLanguagesCallCount, 2);
    });

    test('once genuinely available, the result is cached and not re-checked', () async {
      final tts = _FlakyFirstCallTts()..getLanguagesCallCount = 1; // pretend the race already won once
      final voice = FlutterTtsVoiceService(tts: tts);

      expect(await voice.isAvailable(), isTrue);
      expect(await voice.isAvailable(), isTrue);
      // Only the one call that actually found voices - no redundant re-checks.
      expect(tts.getLanguagesCallCount, 2);
    });

    test('speak() recovers on a retry after losing the availability race on its first call', () async {
      final tts = _FlakyFirstCallTts();
      final voice = FlutterTtsVoiceService(tts: tts);

      final firstAttempt = await voice.speak('Weather update.', languageCode: 'en');
      expect(firstAttempt, isFalse);

      final secondAttempt = await voice.speak('Weather update.', languageCode: 'en');
      expect(secondAttempt, isTrue);
    });
  });
}
