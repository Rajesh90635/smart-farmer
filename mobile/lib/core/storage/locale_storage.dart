import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists the farmer's chosen UI language on-device so the app opens in
/// the right language on the very next launch - before any network call
/// (or even login) has a chance to tell us the backend's preferred_language_code.
/// Reuses FlutterSecureStorage (already a dependency for auth tokens) rather
/// than adding a new plugin just for a language code.
class LocaleStorage {
  static const _languageCodeKey = 'ui_language_code';

  final FlutterSecureStorage _storage;

  LocaleStorage({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  Future<String?> readLanguageCode() => _storage.read(key: _languageCodeKey);

  Future<void> saveLanguageCode(String code) => _storage.write(key: _languageCodeKey, value: code);
}
