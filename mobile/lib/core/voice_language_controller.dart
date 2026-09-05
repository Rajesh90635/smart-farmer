import 'package:flutter/foundation.dart';

import 'location_language_resolver.dart';
import 'storage/voice_language_storage.dart';

/// How the app decides which language spoken audio should use.
enum VoiceLanguageMode {
  /// Speak in whatever language the on-screen content is already in
  /// (the farmer's manually chosen display language, or a message's own
  /// backend-assigned language) - the default, and this app's original
  /// behavior before location-based detection existed.
  manual,

  /// Detect the farmer's current region from their device's GPS location
  /// and speak in that region's language instead, regardless of the
  /// farmer's manually chosen display language.
  location,
}

/// App-wide audio-language preference, separate from LocaleController
/// (which controls the app's DISPLAYED text language). A farmer can keep
/// reading the app in one language while choosing how spoken audio picks
/// its language - mirrors LocaleController's own load/persist pattern.
class VoiceLanguageController extends ChangeNotifier {
  final VoiceLanguageStorage _storage;
  final LocationLanguageResolver _locationResolver;

  VoiceLanguageController({VoiceLanguageStorage? storage, LocationLanguageResolver? locationResolver})
      : _storage = storage ?? VoiceLanguageStorage(),
        _locationResolver = locationResolver ?? LocationLanguageResolver();

  VoiceLanguageMode _mode = VoiceLanguageMode.manual;
  VoiceLanguageMode get mode => _mode;

  Future<void> loadSaved() async {
    final saved = await _storage.readMode();
    if (saved == VoiceLanguageMode.location.name) _mode = VoiceLanguageMode.location;
  }

  Future<void> setMode(VoiceLanguageMode mode) async {
    if (_mode == mode) return;
    _mode = mode;
    notifyListeners();
    await _storage.saveMode(mode.name);
  }

  /// Returns the language code a voice call site should actually speak
  /// in: [contentLanguageCode] as-is in manual mode; the GPS-detected
  /// region's language in location mode, falling back to
  /// [contentLanguageCode] whenever detection fails (no permission, no
  /// GPS fix, no network, or a region this app has no language mapping
  /// for) - never blocks or fails a Listen button just because location
  /// detection didn't work.
  Future<String> resolveLanguageCode({required String contentLanguageCode}) async {
    if (_mode == VoiceLanguageMode.manual) return contentLanguageCode;
    final detected = await _locationResolver.resolveLanguageCode();
    return detected ?? contentLanguageCode;
  }
}
