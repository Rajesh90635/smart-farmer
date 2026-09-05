import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/app.dart';
import 'package:smart_farmer_mobile/core/locale_controller.dart';
import 'package:smart_farmer_mobile/core/voice_language_controller.dart';

void main() {
  testWidgets('App builds and shows a loading indicator on splash', (tester) async {
    await tester.pumpWidget(SmartFarmerApp(localeController: LocaleController(), voiceLanguageController: VoiceLanguageController()));
    // Do NOT pumpAndSettle here - SplashScreen kicks off an async session
    // restoration call (which hits secure storage / the network) that
    // won't complete in a widget test without mocking those dependencies.
    // This test only asserts the app builds and shows the initial loading
    // state, not the full auth flow - see NOTE in PROJECT_STATUS.md about
    // mocking AuthRepository for deeper Flutter auth-flow tests.
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
