import 'package:flutter/material.dart';

import '../../core/location_language_resolver.dart';
import '../../l10n/app_localizations.dart';

/// Language options mirror backend/app/core/localization.py's
/// SUPPORTED_LANGUAGE_CODES exactly - a language accepted here must be one
/// the backend will also accept, or a farmer could complete this screen
/// and then fail registration with a confusing validation error.
class LanguageSelectionScreen extends StatefulWidget {
  const LanguageSelectionScreen({super.key, LocationLanguageResolver? locationResolver})
      : _locationResolver = locationResolver;

  final LocationLanguageResolver? _locationResolver;

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
  State<LanguageSelectionScreen> createState() => _LanguageSelectionScreenState();
}

class _LanguageSelectionScreenState extends State<LanguageSelectionScreen> {
  late final LocationLanguageResolver _locationResolver = widget._locationResolver ?? LocationLanguageResolver();
  bool _detecting = false;

  /// D41-02 (docs/audit/FINAL_CANONICAL_group_B.md): auto-detect existed
  /// only for spoken audio language (VoiceLanguageController), never for
  /// the UI display language itself - reuses the exact same resolver,
  /// never a second location->language mapping.
  Future<void> _detectFromLocation() async {
    setState(() => _detecting = true);
    final code = await _locationResolver.resolveLanguageCode();
    if (!mounted) return;
    setState(() => _detecting = false);
    if (code != null) {
      Navigator.of(context).pop(code);
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(AppLocalizations.of(context)!.languageSelectionDetectFailedMessage)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.chooseYourLanguageTitle)),
      body: ListView.builder(
        itemCount: LanguageSelectionScreen.languages.length + 1,
        itemBuilder: (context, index) {
          if (index == 0) {
            return ListTile(
              leading: _detecting
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.my_location),
              title: Text(l10n.languageSelectionDetectFromLocationLabel, style: const TextStyle(fontSize: 18)),
              onTap: _detecting ? null : _detectFromLocation,
            );
          }
          final (code, label) = LanguageSelectionScreen.languages[index - 1];
          return ListTile(
            title: Text(label, style: const TextStyle(fontSize: 18)),
            onTap: () => Navigator.of(context).pop(code),
          );
        },
      ),
    );
  }
}
