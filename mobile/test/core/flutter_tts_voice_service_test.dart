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
  Future<dynamic> isLanguageAvailable(String language) async => true;

  @override
  Future<dynamic> setLanguage(String language) async => 1;

  @override
  Future<dynamic> speak(String text, {bool focus = false}) async => 1;
}

/// Matches flutter_tts's ACTUAL web implementation (flutter_tts_web.dart):
/// its 'speak' method-channel case calls the browser's speechSynthesis and
/// `break`s without ever returning a value, unless awaitSpeakCompletion is
/// enabled - and even then the completer resolves with no value on
/// success. So `speak()` returns null on web, never the `1` that mobile's
/// platform channel returns on success.
class _WebLikeTts extends FlutterTts {
  @override
  Future<dynamic> get getLanguages async => <String>['en-US'];

  @override
  Future<dynamic> isLanguageAvailable(String language) async => true;

  @override
  Future<dynamic> setLanguage(String language) async => 1;

  @override
  Future<dynamic> speak(String text, {bool focus = false}) async => null;
}

/// Matches the ACTUAL bug this was written to catch: flutter_tts's web
/// 'setLanguage' method-channel case (flutter_tts_web.dart) always returns
/// 1 - even when the browser has no voice for the requested language, it
/// silently keeps whatever voice/lang was already active instead of
/// failing. `isLanguageAvailable` is the one method web implements
/// honestly (it checks the real speechSynthesis voice list), so it must be
/// what `speak()` actually trusts - not `setLanguage`'s return value.
class _WebNoMatchingVoiceTts extends FlutterTts {
  @override
  Future<dynamic> get getLanguages async => <String>['en-US'];

  @override
  Future<dynamic> isLanguageAvailable(String language) async => language == 'en-IN';

  @override
  Future<dynamic> setLanguage(String language) async => 1; // lies: always "succeeds" on web.

  @override
  Future<dynamic> speak(String text, {bool focus = false}) async => null;
}

void main() {
  _ensureBinding();

  group('FlutterTtsVoiceService.speak() success detection', () {
    test('a null speak() result (the real web behavior) still counts as started', () async {
      final voice = FlutterTtsVoiceService(tts: _WebLikeTts());
      final started = await voice.speak('Weather update.', languageCode: 'en');
      expect(started, isTrue);
    });
  });

  group('FlutterTtsVoiceService.speak() per-language availability', () {
    test('speaks when the requested language has a real matching voice', () async {
      final voice = FlutterTtsVoiceService(tts: _WebNoMatchingVoiceTts());
      final started = await voice.speak('Weather update.', languageCode: 'en');
      expect(started, isTrue);
    });

    test('reports unavailable, and never calls speak(), for a language the '
        'browser has no voice for - even though web setLanguage lies and '
        'reports success', () async {
      final voice = FlutterTtsVoiceService(tts: _WebNoMatchingVoiceTts());
      final started = await voice.speak('హెచ్చరిక.', languageCode: 'te');
      expect(started, isFalse);
    });
  });

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
