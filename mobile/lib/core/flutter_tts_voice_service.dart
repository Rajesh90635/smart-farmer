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

      final setResult = await _tts.setLanguage(locale);
      if (setResult != 1) return false;

      final speakResult = await _tts.speak(text);
      return speakResult == 1;
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
