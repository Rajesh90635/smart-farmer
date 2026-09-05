import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/features/auth/reset_password_screen.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

import 'auth_state_test.dart' show FakeAuthRepository;

Widget _wrap(AuthState authState, Map<String, WidgetBuilder> routes) {
  return ChangeNotifierProvider<AuthState>.value(
    value: authState,
    child: MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('en')],
      home: const ResetPasswordScreen(),
      routes: routes,
    ),
  );
}

void main() {
  testWidgets('starts on the phone-number step, requesting a code reveals the reset step', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), const {}));

    expect(find.text('Phone number'), findsOneWidget);
    expect(find.text('Send code'), findsOneWidget);
    expect(find.text('Verification code'), findsNothing);

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Send code'));
    await tester.pumpAndSettle();

    expect(find.text('Verification code'), findsOneWidget);
    expect(find.text('New password'), findsOneWidget);
    expect(find.text("We've sent a verification code to your phone."), findsWidgets);
  });

  testWidgets('failing to request a code keeps the farmer on the phone-number step with an error', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: false)), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Send code'));
    await tester.pumpAndSettle();

    expect(find.text('Verification code'), findsNothing);
    expect(find.byType(SnackBar), findsOneWidget);
  });

  testWidgets('successful reset with a valid code navigates to /home', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), {
      '/home': (_) => const Scaffold(body: Text('Home Screen Placeholder')),
    }));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Send code'));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextFormField, 'Verification code'), '123456');
    await tester.enterText(find.widgetWithText(TextFormField, 'New password'), 'NewPass1!');
    await tester.enterText(find.widgetWithText(TextFormField, 'Confirm new password'), 'NewPass1!');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Reset password'));
    await tester.pumpAndSettle();

    expect(find.text('Home Screen Placeholder'), findsOneWidget);
  });

  testWidgets('an invalid code on the reset step shows a friendly error and stays on that step', (tester) async {
    // OTP request succeeds (reveals the reset step), but the final reset
    // itself fails - e.g. the farmer typed the wrong code.
    final repository = FakeAuthRepository(shouldSucceed: true, resetPasswordSucceeds: false);
    await tester.pumpWidget(_wrap(AuthState(repository: repository), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Send code'));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextFormField, 'Verification code'), '000000');
    await tester.enterText(find.widgetWithText(TextFormField, 'New password'), 'NewPass1!');
    await tester.enterText(find.widgetWithText(TextFormField, 'Confirm new password'), 'NewPass1!');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Reset password'));
    await tester.pumpAndSettle();

    expect(find.byType(SnackBar), findsOneWidget);
    // Still on the reset step, not bounced back to the phone step.
    expect(find.text('Verification code'), findsOneWidget);
  });
}
