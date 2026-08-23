/// A single state/district/mandal/village row - all four levels share this
/// exact (id, name) shape, mirroring backend/app/schemas/location.py's
/// StateResponse/DistrictResponse/MandalResponse/VillageResponse.
class LocationOption {
  final int id;
  final String name;

  LocationOption({required this.id, required this.name});

  factory LocationOption.fromJson(Map<String, dynamic> json) =>
      LocationOption(id: json['id'] as int, name: json['name'] as String);
}

/// A best-effort guess of state/district/mandal/village NAMES (not ids)
/// from a GPS reverse-geocode lookup - see NominatimReverseGeocoder. Never
/// treated as authoritative: the caller must still match these names
/// against the real dropdown lists before it can set an actual selection.
class ReverseGeocodeGuess {
  final String? stateName;
  final String? districtName;
  final String? mandalName;
  final String? villageName;

  ReverseGeocodeGuess({this.stateName, this.districtName, this.mandalName, this.villageName});
}
