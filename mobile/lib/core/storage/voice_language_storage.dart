import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists the farmer's chosen audio-language MODE (manual vs
/// location-based) on-device, exactly mirroring LocaleStorage's pattern
/// for the display-language choice - a separate key because this is a
/// distinct preference (how audio language is picked), not the display
/// language itself.
class VoiceLanguageStorage {
  static const _modeKey = 'voice_language_mode';

  final FlutterSecureStorage _storage;

  VoiceLanguageStorage({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  Future<String?> readMode() => _storage.read(key: _modeKey);

  Future<void> saveMode(String mode) => _storage.write(key: _modeKey, value: mode);
}
