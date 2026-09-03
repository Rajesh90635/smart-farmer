// Exercises the real registration -> language-selection -> consent flow
// through the actual app widgets (RegisterScreen, LanguageSelectionScreen,
// ConsentScreen), the real LocaleController, and the real generated
// AppLocalizations classes - proving the UI language switches immediately,
// within the same widget tree (no pumpWidget/restart in between), the
// moment a farmer picks a language during registration.
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/locale_controller.dart';
import 'package:smart_farmer_mobile/core/storage/locale_storage.dart';
import 'package:smart_farmer_mobile/features/auth/auth_repository.dart';
import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/features/auth/consent_screen.dart';
import 'package:smart_farmer_mobile/features/auth/register_screen.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations_kn.dart';

/// Avoids the real FlutterSecureStorage platform channel, which has no
/// implementation registered under `flutter test` and would throw
/// MissingPluginException on the very first setLocale() call.
class _InMemoryLocaleStorage extends LocaleStorage {
  String? _saved;
  @override
  Future<String?> readLanguageCode() async => _saved;
  @override
  Future<void> saveLanguageCode(String code) async => _saved = code;
}

final _boundaryKey = GlobalKey();

class _TestHarness extends StatelessWidget {
  const _TestHarness({required this.localeController, required this.authState});
  final LocaleController localeController;
  final AuthState authState;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<LocaleController>.value(value: localeController),
        ChangeNotifierProvider<AuthState>.value(value: authState),
      ],
      child: Consumer<LocaleController>(
        builder: (context, lc, _) => RepaintBoundary(
          key: _boundaryKey,
          child: MaterialApp(
            locale: lc.locale,
            localizationsDelegates: const [
              AppLocalizations.delegate,
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            supportedLocales: const [
              Locale('en'),
              Locale('hi'),
              Locale('kn'),
              Locale('te'),
              Locale('ta'),
              Locale('ml'),
              Locale('mr'),
            ],
            home: const RegisterScreen(),
          ),
        ),
      ),
    );
  }
}

Future<void> _capture(WidgetTester tester, String filename) async {
  await tester.runAsync(() async {
    final boundary = _boundaryKey.currentContext!.findRenderObject() as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 2.0);
    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    await File(filename).writeAsBytes(byteData!.buffer.asUint8List());
  });
}

void main() {
  testWidgets('Picking Kannada during registration switches the UI live, no restart', (tester) async {
    final localeController = LocaleController(storage: _InMemoryLocaleStorage());
    final authState = AuthState(repository: AuthRepository(apiClient: ApiClient()));

    // Single pumpWidget for the whole test - everything after this point
    // happens in the SAME running widget tree, which is exactly what
    // proves the switch is live rather than requiring a restart.
    await tester.pumpWidget(_TestHarness(localeController: localeController, authState: authState));
    await tester.pumpAndSettle();

    expect(find.text('Create your account'), findsOneWidget);
    expect(localeController.locale.languageCode, 'en');

    await tester.enterText(find.widgetWithText(TextFormField, 'Your name'), 'Test Farmer');
    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'Passw0rd1!');
    await tester.pump();

    await tester.tap(find.widgetWithText(ElevatedButton, 'Continue'));
    await tester.pumpAndSettle();

    // Now on LanguageSelectionScreen, still in English (nothing switched yet).
    expect(find.text('Choose your language'), findsOneWidget);
    await _capture(tester, 'test/.artifacts/1_language_selection_en.png');

    await tester.tap(find.text('ಕನ್ನಡ (Kannada)'));
    await tester.pumpAndSettle();

    // The tap popped LanguageSelectionScreen with 'kn'; RegisterScreen's
    // _continue() called LocaleController.setLocale('kn') and then pushed
    // ConsentScreen - all within this one still-running widget tree.
    expect(localeController.locale.languageCode, 'kn');
    expect(find.byType(ConsentScreen), findsOneWidget);

    final kn = AppLocalizationsKn();
    expect(find.text(kn.consentScreenTitle), findsOneWidget);
    expect(find.text(kn.agreeTermsOfServiceLabel), findsOneWidget);
    expect(find.text(kn.agreePrivacyPolicyLabel), findsOneWidget);
    expect(find.text(kn.consentContinueButton), findsOneWidget);

    // The English consent copy must be gone - this is a live switch of the
    // same screen instance, not a second copy layered on top.
    expect(find.text('Before you continue'), findsNothing);
    expect(find.text('I agree to the Terms of Service'), findsNothing);

    expect(Localizations.localeOf(tester.element(find.byType(ConsentScreen))), const Locale('kn'));

    await _capture(tester, 'test/.artifacts/2_consent_screen_kn.png');
  });
}
