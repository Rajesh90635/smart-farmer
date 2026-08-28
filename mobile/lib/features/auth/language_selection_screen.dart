import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

/// Language options mirror backend/app/core/localization.py's
/// SUPPORTED_LANGUAGE_CODES exactly - a language accepted here must be one
/// the backend will also accept, or a farmer could complete this screen
/// and then fail registration with a confusing validation error.
class LanguageSelectionScreen extends StatelessWidget {
  const LanguageSelectionScreen({super.key});

  static const languages = [
    ('en', 'English'),
    ('hi', 'हिन्दी (Hindi)'),
    ('kn', 'ಕನ್ನಡ (Kannada)'),
    ('te', 'తెలుగు (Telugu)'),
    ('ta', 'தமிழ் (Tamil)'),
    ('ml', 'മലയാളം (Malayalam)'),
    ('mr', 'मराठी (Marathi)'),
  ];

  /// Human-readable label for a language code, e.g. for displaying the
  /// farmer's current choice on the Profile screen. Falls back to the raw
  /// code for any value outside the list above (should not happen since
  /// both this screen and the backend validate against the same set).
  static String labelForCode(String code) {
    for (final (c, label) in languages) {
      if (c == code) return label;
    }
    return code;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.chooseYourLanguageTitle)),
      body: ListView.builder(
        itemCount: languages.length,
        itemBuilder: (context, index) {
          final (code, label) = languages[index];
          return ListTile(
            title: Text(label, style: const TextStyle(fontSize: 18)),
            onTap: () => Navigator.of(context).pop(code),
          );
        },
      ),
    );
  }
}
