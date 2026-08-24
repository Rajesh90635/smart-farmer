import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/features/auth/auth_repository.dart';
import 'package:smart_farmer_mobile/features/auth/consent_screen.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

/// Pushes ConsentScreen on tap and stores whatever value it pops with, so
/// tests can assert on the exact List<ConsentInput> returned - mirroring
/// how RegisterScreen itself awaits this screen's result.
class _Harness extends StatefulWidget {
  const _Harness();

  @override
  State<_Harness> createState() => _HarnessState();
}

class _HarnessState extends State<_Harness> {
  List<ConsentInput>? result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ElevatedButton(
        onPressed: () async {
          final popped = await Navigator.of(context).push<List<ConsentInput>>(
            MaterialPageRoute(builder: (_) => const ConsentScreen()),
          );
          setState(() => result = popped);
        },
        child: const Text('open'),
      ),
    );
  }
}

Widget _wrap() {
  return const MaterialApp(
    localizationsDelegates: [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: [Locale('en')],
    home: _Harness(),
  );
}

void main() {
  testWidgets('Continue is disabled until both boxes are checked', (tester) async {
    await tester.pumpWidget(_wrap());
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    final continueButton = tester.widget<ElevatedButton>(find.widgetWithText(ElevatedButton, 'Continue'));
    expect(continueButton.onPressed, isNull);

    await tester.tap(find.text('I agree to the Terms of Service'));
    await tester.pump();
    final stillDisabled = tester.widget<ElevatedButton>(find.widgetWithText(ElevatedButton, 'Continue'));
    expect(stillDisabled.onPressed, isNull);

    await tester.tap(find.text('I agree to the Privacy Policy'));
    await tester.pump();
    final enabled = tester.widget<ElevatedButton>(find.widgetWithText(ElevatedButton, 'Continue'));
    expect(enabled.onPressed, isNotNull);
  });

  testWidgets('tapping Continue pops the two required consents', (tester) async {
    await tester.pumpWidget(_wrap());
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('I agree to the Terms of Service'));
    await tester.tap(find.text('I agree to the Privacy Policy'));
    await tester.pump();
    await tester.tap(find.widgetWithText(ElevatedButton, 'Continue'));
    await tester.pumpAndSettle();

    final state = tester.state<_HarnessState>(find.byType(_Harness));
    // ConsentInput has no == override, so compare via toJson() rather than
    // list identity equality.
    expect(state.result?.map((c) => c.toJson()).toList(), [
      {'consent_type': 'terms_of_service', 'version': '1.0'},
      {'consent_type': 'privacy_policy', 'version': '1.0'},
    ]);
  });
}
