import 'dart:convert';

import 'package:http/http.dart' as http;

import '../features/farm/location_models.dart';

/// Best-effort GPS -> place-name lookup via the free public OpenStreetMap
/// Nominatim API, used only for the "Use current location" button on Add
/// Farm. This is a real, disclosed trade-off: unlike every other farm
/// field (which never leaves the device except to this app's own
/// backend), the coordinates passed here go to a third-party public
/// service - only on the farmer's explicit tap, never automatically.
///
/// India has no standard OSM tagging for "mandal/taluk" - Nominatim's
/// `address.county` is the closest approximation in some regions and is
/// used as a guess, but it commonly comes back missing or not matching
/// this app's own mandal master data. The caller (add_edit_farm_screen)
/// treats every field here as a hint to try to match against real
/// dropdown options, never as a value to store directly.
///
/// Usage-policy note: Nominatim's public instance asks for a maximum of
/// ~1 request/second and a real identifying User-Agent - both honored
/// here. This is not appropriate for bulk/automatic lookups, only for
/// this one on-demand, farmer-initiated call.
class NominatimReverseGeocoder {
  final http.Client _client;
  NominatimReverseGeocoder({http.Client? client}) : _client = client ?? http.Client();

  Future<ReverseGeocodeGuess?> reverseGeocode({required double latitude, required double longitude}) async {
    final uri = Uri.https('nominatim.openstreetmap.org', '/reverse', {
      'format': 'jsonv2',
      'lat': latitude.toString(),
      'lon': longitude.toString(),
      'addressdetails': '1',
      'accept-language': 'en',
    });

    final response = await _client.get(
      uri,
      headers: const {'User-Agent': 'SmartFarmerApp/1.0 (offline-first farmer platform; add-farm location lookup)'},
    );
    if (response.statusCode < 200 || response.statusCode >= 300) return null;

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final address = decoded['address'] as Map<String, dynamic>?;
    if (address == null) return null;

    return ReverseGeocodeGuess(
      stateName: address['state'] as String?,
      districtName: (address['state_district'] ?? address['district']) as String?,
      mandalName: address['county'] as String?,
      villageName: (address['village'] ?? address['hamlet'] ?? address['town'] ?? address['suburb']) as String?,
    );
  }
}
