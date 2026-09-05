import 'package:flutter_tts/flutter_tts.dart';

import 'voice_service.dart';

/// Maps our app's language codes to BCP-47 locale tags flutter_tts/the
/// underlying platform TTS engines expect. Only the 7 codes the backend
/// (app/core/localization.py) actually recognizes are mapped - no locale
/// is invented for a code the rest of the app doesn't support either.
const Map<String, String> _languageCodeToLocale = {
  'en': 'en-IN',
  'hi': 'hi-IN',
  'kn': 'kn-IN',
  'te': 'te-IN',
  'ta': 'ta-IN',
  'ml': 'ml-IN',
  'mr': 'mr-IN',
};

class FlutterTtsVoiceService implements VoiceService {
  final FlutterTts _tts;
  bool _cachedAvailability = false;

  FlutterTtsVoiceService({FlutterTts? tts}) : _tts = tts ?? FlutterTts();

  @override
  Future<bool> isAvailable() async {
    // Only a positive result is ever cached. On web, the underlying
    // speechSynthesis.getVoices() is a well-known race: it often reports
    // zero voices immediately after page load and only populates them a
    // moment later (confirmed: 0 voices at load, 3 after ~1.5s in this
    // browser). Caching a negative result here would permanently disable
    // voice for the rest of the session on every screen after just one
    // unlucky early check - so a false result is never remembered, and
    // the next speak() attempt (any screen) gets a fresh, usually
    // successful, check instead.
    if (_cachedAvailability) return true;
    try {
      final languages = await _tts.getLanguages;
      final available = languages is List && languages.isNotEmpty;
      if (available) _cachedAvailability = true;
      return available;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<bool> speak(String text, {required String languageCode}) async {
    if (text.trim().isEmpty) return false;
    try {
      final available = await isAvailable();
      if (!available) return false;

      final locale = _languageCodeToLocale[languageCode];
      if (locale == null) return false;

      // `setLanguage`'s return code is NOT trustworthy for this on every
      // platform: Android's engine genuinely fails setLanguage (returns 0)
      // when the device has no voice for `locale`, but flutter_tts's web
      // implementation always returns 1 from setLanguage regardless of
      // whether any matching voice exists - it silently keeps whatever
      // voice/lang was already selected (e.g. English, left over from a
      // previous call) instead of failing, so a farmer picking a language
      // this browser has no voice for got the app reporting success while
      // it read (or garbled) the text in the wrong language. `isLanguageAvailable`
      // is implemented honestly on both platforms - checked here directly
      // so an unsupported language is correctly reported as unavailable
      // instead of speaking in the wrong voice.
      final languageAvailable = await _tts.isLanguageAvailable(locale);
      if (languageAvailable != true) return false;

      final setResult = await _tts.setLanguage(locale);
      if (setResult != 1) return false;

      // Not `speakResult == 1`: flutter_tts's web implementation only
      // returns 1 for setLanguage/stop/etc. - for `speak` specifically, its
      // 'speak' case calls the browser's speechSynthesis and just `break`s
      // without ever awaiting or returning anything (returns null), unless
      // awaitSpeakCompletion is enabled, in which case it resolves the
      // completer with no value on success (still not 1). So `== 1` is
      // permanently false on web even when speech genuinely plays - here,
      // completing without throwing IS the success signal (a real failure
      // surfaces as an exception, already handled by the catch below),
      // matching this method's documented contract.
      await _tts.speak(text);
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> stop() async {
    try {
      await _tts.stop();
    } catch (_) {
      // Stopping speech that already isn't playing, or a platform-channel
      // hiccup, must never surface as an error to the farmer.
    }
  }
}
