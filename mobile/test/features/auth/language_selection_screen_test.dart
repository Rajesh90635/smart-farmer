import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';

import 'package:smart_farmer_mobile/core/location_language_resolver.dart';
import 'package:smart_farmer_mobile/core/nominatim_reverse_geocoder.dart';
import 'package:smart_farmer_mobile/features/auth/language_selection_screen.dart';
import 'package:smart_farmer_mobile/features/farm/location_models.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

/// Pushes LanguageSelectionScreen on tap and stores whatever code it pops
/// with, mirroring how RegisterScreen itself awaits this screen's result.
class _Harness extends StatefulWidget {
  const _Harness({this.locationResolver});

  final LocationLanguageResolver? locationResolver;

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
            MaterialPageRoute(builder: (_) => LanguageSelectionScreen(locationResolver: widget.locationResolver)),
          );
          setState(() => result = popped);
        },
        child: const Text('open'),
      ),
    );
  }
}

Widget _wrap({LocationLanguageResolver? locationResolver}) {
  return MaterialApp(
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: const [Locale('en')],
    home: _Harness(locationResolver: locationResolver),
  );
}

/// D41-02 (docs/audit/FINAL_CANONICAL_group_A.md): fakes mirroring
/// location_language_resolver_test.dart's own doubles.
class _FakePositionSource implements DevicePositionSource {
  final Position? position;
  _FakePositionSource({this.position});

  @override
  Future<Position?> getCurrentPosition() async => position;
}

class _FakeGeocoder extends NominatimReverseGeocoder {
  final ReverseGeocodeGuess? guess;
  _FakeGeocoder({this.guess});

  @override
  Future<ReverseGeocodeGuess?> reverseGeocode({required double latitude, required double longitude}) async => guess;
}

Position _position() => Position(
      latitude: 16.5,
      longitude: 80.6,
      timestamp: DateTime(2026, 1, 1),
      accuracy: 10,
      altitude: 0,
      altitudeAccuracy: 0,
      heading: 0,
      headingAccuracy: 0,
      speed: 0,
      speedAccuracy: 0,
    );

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

  testWidgets('detecting a recognized location pops with the resolved language code', (tester) async {
    final resolver = LocationLanguageResolver(
      positionSource: _FakePositionSource(position: _position()),
      geocoder: _FakeGeocoder(guess: ReverseGeocodeGuess(stateName: 'Tamil Nadu')),
    );
    await tester.pumpWidget(_wrap(locationResolver: resolver));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Detect from my location'));
    await tester.pumpAndSettle();

    final state = tester.state<_HarnessState>(find.byType(_Harness));
    expect(state.result, 'ta');
  });

  testWidgets('detection failure shows an error and keeps the screen open for manual selection', (tester) async {
    final resolver = LocationLanguageResolver(
      positionSource: _FakePositionSource(position: null),
      geocoder: _FakeGeocoder(),
    );
    await tester.pumpWidget(_wrap(locationResolver: resolver));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Detect from my location'));
    await tester.pumpAndSettle();

    // The screen never popped (still visible with the full manual list) -
    // this is itself the evidence the harness stayed open; _Harness below
    // it in the Navigator stack is offstage and not meaningfully queryable.
    expect(find.text('Could not detect a language for your location. Please choose one below.'), findsOneWidget);
    expect(find.text('English'), findsOneWidget);
  });
}
