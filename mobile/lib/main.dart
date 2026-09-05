import 'package:flutter/material.dart';

import 'app.dart';
import 'core/locale_controller.dart';
import 'core/voice_language_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final localeController = LocaleController();
  await localeController.loadSaved();
  final voiceLanguageController = VoiceLanguageController();
  await voiceLanguageController.loadSaved();
  runApp(SmartFarmerApp(localeController: localeController, voiceLanguageController: voiceLanguageController));
}
