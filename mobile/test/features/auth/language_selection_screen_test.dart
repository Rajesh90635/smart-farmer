import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_farmer_mobile/features/auth/language_selection_screen.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

/// Pushes LanguageSelectionScreen on tap and stores whatever code it pops
/// with, mirroring how RegisterScreen itself awaits this screen's result.
class _Harness extends StatefulWidget {
  const _Harness();

  @override
  State<_Harness> createState() => _HarnessState();
}

class _HarnessState extends State<_Harness> {
  String? result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ElevatedButton(
        onPressed: () async {
          final popped = await Navigator.of(context).push<String>(
            MaterialPageRoute(builder: (_) => const LanguageSelectionScreen()),
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
  testWidgets('renders all 7 supported languages', (tester) async {
    await tester.pumpWidget(_wrap());
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('English'), findsOneWidget);
    expect(find.text('हिन्दी (Hindi)'), findsOneWidget);
    expect(find.text('ಕನ್ನಡ (Kannada)'), findsOneWidget);
    expect(find.text('తెలుగు (Telugu)'), findsOneWidget);
    expect(find.text('தமிழ் (Tamil)'), findsOneWidget);
    expect(find.text('മലയാളം (Malayalam)'), findsOneWidget);
    expect(find.text('मराठी (Marathi)'), findsOneWidget);
  });

  testWidgets('tapping a language pops its code', (tester) async {
    await tester.pumpWidget(_wrap());
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('हिन्दी (Hindi)'));
    await tester.pumpAndSettle();

    final state = tester.state<_HarnessState>(find.byType(_Harness));
    expect(state.result, 'hi');
  });
}
