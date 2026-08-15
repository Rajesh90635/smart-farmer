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
  bool? _cachedAvailability;

  FlutterTtsVoiceService({FlutterTts? tts}) : _tts = tts ?? FlutterTts();

  @override
  Future<bool> isAvailable() async {
    if (_cachedAvailability != null) return _cachedAvailability!;
    try {
      final languages = await _tts.getLanguages;
      _cachedAvailability = languages is List && languages.isNotEmpty;
    } catch (_) {
      _cachedAvailability = false;
    }
    return _cachedAvailability!;
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
