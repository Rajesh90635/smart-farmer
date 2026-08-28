import 'package:flutter/material.dart';

import 'app.dart';
import 'core/locale_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final localeController = LocaleController();
  await localeController.loadSaved();
  runApp(SmartFarmerApp(localeController: localeController));
}
