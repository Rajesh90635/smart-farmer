import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';
import 'package:smart_farmer_mobile/screens/login_screen.dart';

import '../features/auth/auth_state_test.dart' show FakeAuthRepository;

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
      home: const LoginScreen(),
      routes: routes,
    ),
  );
}

void main() {
  testWidgets('renders phone and password fields', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), const {}));

    expect(find.text('Phone number'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Log in'), findsWidgets);
  });

  testWidgets('shows validation error when password is empty', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.text('Please enter your password.'), findsOneWidget);
  });

  testWidgets('successful login navigates to /home', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), {
      '/home': (_) => const Scaffold(body: Text('Home Screen Placeholder')),
    }));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'Str0ngPass');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.text('Home Screen Placeholder'), findsOneWidget);
  });

  testWidgets('failed login shows a snackbar with the friendly error', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: false)), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'wrong');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.byType(SnackBar), findsOneWidget);
  });
}
