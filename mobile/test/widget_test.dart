// Basic app smoke test. This file was still the unmodified default
// Flutter counter-app template (referencing a nonexistent `MyApp` class -
// this app's actual root widget is `SmartFarmerApp`) and failed to even
// compile - a real, pre-existing gap, only surfaced once `flutter test`
// was actually run for the first time in this project's history.
//
// Kept deliberately minimal: SmartFarmerApp's splash screen kicks off
// real async work on the first frame (session restoration via
// flutter_secure_storage, offline-sync init via path_provider) that isn't
// mocked here, so this only verifies the app builds and renders its
// initial loading state - it never pumps past that first frame.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/app.dart';

void main() {
  testWidgets('SmartFarmerApp builds and shows the splash loading screen first', (WidgetTester tester) async {
    await tester.pumpWidget(const SmartFarmerApp());
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
