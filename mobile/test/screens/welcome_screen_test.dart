import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/l10n/app_localizations.dart';
import 'package:smart_farmer_mobile/screens/welcome_screen.dart';

Widget _wrap(Widget home, Map<String, WidgetBuilder> routes) {
  return MaterialApp(
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: const [Locale('en')],
    home: home,
    routes: routes,
  );
}

void main() {
  testWidgets('renders title, tagline, and both buttons', (tester) async {
    await tester.pumpWidget(_wrap(const WelcomeScreen(), const {}));

    expect(find.text('Smart Farmer'), findsOneWidget);
    expect(find.text('Your farm, understood.'), findsOneWidget);
    expect(find.text('Get started'), findsOneWidget);
    expect(find.text('I already have an account'), findsOneWidget);
  });

  testWidgets('Get started navigates to /register', (tester) async {
    await tester.pumpWidget(_wrap(const WelcomeScreen(), {
      '/register': (_) => const Scaffold(body: Text('Register Screen Placeholder')),
    }));

    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();

    expect(find.text('Register Screen Placeholder'), findsOneWidget);
  });

  testWidgets('I already have an account navigates to /login', (tester) async {
    await tester.pumpWidget(_wrap(const WelcomeScreen(), {
      '/login': (_) => const Scaffold(body: Text('Login Screen Placeholder')),
    }));

    await tester.tap(find.text('I already have an account'));
    await tester.pumpAndSettle();

    expect(find.text('Login Screen Placeholder'), findsOneWidget);
  });
}
