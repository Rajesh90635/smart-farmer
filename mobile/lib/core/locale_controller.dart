import 'package:flutter/material.dart';

import 'storage/locale_storage.dart';

/// App-wide UI language. Held separately from AuthState/FarmerProfile
/// because the language must be settable (and take visible effect
/// immediately) before a farmer has an account at all - during the
/// registration flow's language-selection step - not just from the
/// profile screen after login.
///
/// Mirrors backend/app/core/localization.py's SUPPORTED_LANGUAGE_CODES.
class LocaleController extends ChangeNotifier {
  static const supportedLanguageCodes = ['en', 'hi', 'kn', 'te', 'ta', 'ml', 'mr'];

  final LocaleStorage _storage;

  LocaleController({LocaleStorage? storage}) : _storage = storage ?? LocaleStorage();

  Locale _locale = const Locale('en');
  Locale get locale => _locale;

  /// Loads the on-device saved language, if any. Call once at startup,
  /// before runApp, so the very first frame is already in the right
  /// language instead of flashing English first.
  Future<void> loadSaved() async {
    final saved = await _storage.readLanguageCode();
    if (saved != null && supportedLanguageCodes.contains(saved)) {
      _locale = Locale(saved);
    }
  }

  /// Applied immediately (this is what makes the app's UI actually switch),
  /// and persisted on-device. Syncing the choice to the farmer's backend
  /// profile (when logged in) is the caller's responsibility - the UI
  /// language must not depend on that network call succeeding.
  Future<void> setLocale(String code) async {
    if (!supportedLanguageCodes.contains(code)) return;
    if (_locale.languageCode == code) return;
    _locale = Locale(code);
    notifyListeners();
    await _storage.saveLanguageCode(code);
  }
}
