import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';
import 'package:smart_farmer_mobile/core/location_language_resolver.dart';
import 'package:smart_farmer_mobile/core/nominatim_reverse_geocoder.dart';
import 'package:smart_farmer_mobile/features/farm/location_models.dart';

class _FakePositionSource implements DevicePositionSource {
  final Position? position;
  final Object? error;
  _FakePositionSource({this.position, this.error});

  @override
  Future<Position?> getCurrentPosition() async {
    if (error != null) throw error!;
    return position;
  }
}

class _FakeGeocoder extends NominatimReverseGeocoder {
  final ReverseGeocodeGuess? guess;
  final Object? error;
  _FakeGeocoder({this.guess, this.error});

  @override
  Future<ReverseGeocodeGuess?> reverseGeocode({required double latitude, required double longitude}) async {
    if (error != null) throw error!;
    return guess;
  }
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
  group('LocationLanguageResolver', () {
    test('maps a recognized state name to its language code', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: _position()),
        geocoder: _FakeGeocoder(guess: ReverseGeocodeGuess(stateName: 'Andhra Pradesh')),
      );
      expect(await resolver.resolveLanguageCode(), 'te');
    });

    test('is case/whitespace-insensitive on the state name', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: _position()),
        geocoder: _FakeGeocoder(guess: ReverseGeocodeGuess(stateName: '  TAMIL NADU  ')),
      );
      expect(await resolver.resolveLanguageCode(), 'ta');
    });

    test('returns null for a state this app has no supported-language mapping for', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: _position()),
        geocoder: _FakeGeocoder(guess: ReverseGeocodeGuess(stateName: 'West Bengal')),
      );
      expect(await resolver.resolveLanguageCode(), isNull);
    });

    test('returns null, never throws, when location permission/service is unavailable', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: null),
        geocoder: _FakeGeocoder(),
      );
      expect(await resolver.resolveLanguageCode(), isNull);
    });

    test('returns null, never throws, when getting the position itself throws', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(error: Exception('GPS hardware error')),
        geocoder: _FakeGeocoder(),
      );
      expect(await resolver.resolveLanguageCode(), isNull);
    });

    test('returns null, never throws, when the reverse-geocode call fails (offline)', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: _position()),
        geocoder: _FakeGeocoder(error: Exception('No internet')),
      );
      expect(await resolver.resolveLanguageCode(), isNull);
    });

    test('returns null when the reverse-geocode result has no state name at all', () async {
      final resolver = LocationLanguageResolver(
        positionSource: _FakePositionSource(position: _position()),
        geocoder: _FakeGeocoder(guess: ReverseGeocodeGuess()),
      );
      expect(await resolver.resolveLanguageCode(), isNull);
    });
  });
}
