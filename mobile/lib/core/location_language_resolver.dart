import 'package:geolocator/geolocator.dart';

import 'nominatim_reverse_geocoder.dart';

/// Thin wrapper around Geolocator's static calls so
/// LocationLanguageResolver can be unit-tested with a fake position
/// source, matching this codebase's usual DI-behind-an-interface pattern
/// (VoiceService, WeatherProvider, AIProvider) rather than depending on a
/// static platform API directly.
abstract class DevicePositionSource {
  Future<Position?> getCurrentPosition();
}

class GeolocatorPositionSource implements DevicePositionSource {
  @override
  Future<Position?> getCurrentPosition() async {
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) return null;
    if (!await Geolocator.isLocationServiceEnabled()) return null;

    return Geolocator.getCurrentPosition(locationSettings: const LocationSettings(accuracy: LocationAccuracy.low));
  }
}

/// Best-effort mapping from an Indian state's name (as returned by
/// Nominatim's reverse geocode - see NominatimReverseGeocoder) to one of
/// this app's 7 supported language codes (LocaleController.supportedLanguageCodes).
/// A deliberate simplification: real language use varies within a state
/// (districts, individuals), and several major Indian languages aren't
/// among the 7 this app supports at all (e.g. Bengali, Punjabi, Odia,
/// Gujarati) - for those, and for any unrecognized state name, this
/// returns null so the caller falls back to the farmer's own chosen
/// language rather than guessing wrong.
const Map<String, String> _stateNameToLanguageCode = {
  'andhra pradesh': 'te',
  'telangana': 'te',
  'tamil nadu': 'ta',
  'karnataka': 'kn',
  'kerala': 'ml',
  'maharashtra': 'mr',
  'uttar pradesh': 'hi',
  'madhya pradesh': 'hi',
  'bihar': 'hi',
  'rajasthan': 'hi',
  'haryana': 'hi',
  'delhi': 'hi',
  'nct of delhi': 'hi',
  'uttarakhand': 'hi',
  'himachal pradesh': 'hi',
  'jharkhand': 'hi',
  'chhattisgarh': 'hi',
};

/// Resolves an audio-language code from the farmer's CURRENT device
/// location - used only when the farmer has explicitly chosen the
/// "detect from my location" audio-language mode (see
/// VoiceLanguageController). Never blocks or throws: any failure
/// (permission denied, location services off, no network, an
/// unrecognized region) resolves to null, and every caller treats null as
/// "keep using the farmer's manually chosen language" - the same
/// best-effort, never-crash contract already established for
/// NominatimReverseGeocoder's use on the Add Farm screen.
class LocationLanguageResolver {
  final DevicePositionSource _positionSource;
  final NominatimReverseGeocoder _geocoder;

  LocationLanguageResolver({DevicePositionSource? positionSource, NominatimReverseGeocoder? geocoder})
      : _positionSource = positionSource ?? GeolocatorPositionSource(),
        _geocoder = geocoder ?? NominatimReverseGeocoder();

  Future<String?> resolveLanguageCode() async {
    try {
      final position = await _positionSource.getCurrentPosition();
      if (position == null) return null;

      final guess = await _geocoder.reverseGeocode(latitude: position.latitude, longitude: position.longitude);
      final stateName = guess?.stateName?.trim().toLowerCase();
      if (stateName == null || stateName.isEmpty) return null;

      return _stateNameToLanguageCode[stateName];
    } catch (_) {
      return null;
    }
  }
}
