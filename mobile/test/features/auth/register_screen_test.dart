import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/features/auth/language_selection_screen.dart';
import 'package:smart_farmer_mobile/features/auth/register_screen.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

import 'auth_state_test.dart' show FakeAuthRepository;

Widget _wrap(AuthState authState) {
  return ChangeNotifierProvider<AuthState>.value(
    value: authState,
    child: const MaterialApp(
      localizationsDelegates: [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: [Locale('en')],
      home: RegisterScreen(),
    ),
  );
}

void main() {
  testWidgets('renders name, phone, and password fields', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true))));

    expect(find.text('Your name'), findsOneWidget);
    expect(find.text('Phone number'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
  });

  testWidgets('shows validation errors on empty submit', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true))));

    await tester.tap(find.widgetWithText(ElevatedButton, 'Continue'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsNothing);
  });

  testWidgets('valid submit pushes LanguageSelectionScreen', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true))));

    await tester.enterText(find.widgetWithText(TextFormField, 'Your name'), 'Test Farmer');
    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'Str0ngPass');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Continue'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsOneWidget);
  });
}
