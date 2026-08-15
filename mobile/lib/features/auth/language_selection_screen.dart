import 'package:flutter/material.dart';

/// Language options mirror backend/app/core/localization.py's
/// SUPPORTED_LANGUAGE_CODES exactly - a language accepted here must be one
/// the backend will also accept, or a farmer could complete this screen
/// and then fail registration with a confusing validation error.
class LanguageSelectionScreen extends StatelessWidget {
  const LanguageSelectionScreen({super.key});

  static const _languages = [
    ('en', 'English'),
    ('hi', 'हिन्दी (Hindi)'),
    ('kn', 'ಕನ್ನಡ (Kannada)'),
    ('te', 'తెలుగు (Telugu)'),
    ('ta', 'தமிழ் (Tamil)'),
    ('ml', 'മലയാളം (Malayalam)'),
    ('mr', 'मराठी (Marathi)'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Choose your language')),
      body: ListView.builder(
        itemCount: _languages.length,
        itemBuilder: (context, index) {
          final (code, label) = _languages[index];
          return ListTile(
            title: Text(label, style: const TextStyle(fontSize: 18)),
            onTap: () => Navigator.of(context).pop(code),
          );
        },
      ),
    );
  }
}
