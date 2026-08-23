import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/farm/location_models.dart';

void main() {
  group('LocationOption.fromJson', () {
    test('parses id and name for any of the four hierarchy levels', () {
      final option = LocationOption.fromJson({'id': 14, 'name': 'Guntur'});
      expect(option.id, 14);
      expect(option.name, 'Guntur');
    });
  });

  group('ReverseGeocodeGuess', () {
    test('every field is independently nullable - a partial Nominatim response is not an error', () {
      final guess = ReverseGeocodeGuess(stateName: 'Andhra Pradesh');
      expect(guess.stateName, 'Andhra Pradesh');
      expect(guess.districtName, isNull);
      expect(guess.mandalName, isNull);
      expect(guess.villageName, isNull);
    });
  });
}
