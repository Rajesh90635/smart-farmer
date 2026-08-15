import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/farm/farm_models.dart';

void main() {
  group('nextStatusAfter', () {
    test('returns the next status in the forward path', () {
      expect(nextStatusAfter('planned'), 'sown');
      expect(nextStatusAfter('sown'), 'growing');
      expect(nextStatusAfter('growing'), 'flowering');
      expect(nextStatusAfter('flowering'), 'fruiting');
      expect(nextStatusAfter('fruiting'), 'ready_for_harvest');
      expect(nextStatusAfter('ready_for_harvest'), 'harvested');
    });

    test('returns null for a terminal status', () {
      expect(nextStatusAfter('harvested'), isNull);
    });

    test('returns null for an unrecognized status (e.g. cancelled)', () {
      expect(nextStatusAfter('cancelled'), isNull);
    });
  });

  group('Farm.fromJson', () {
    test('parses numeric strings and nullable location fields', () {
      final farm = Farm.fromJson({
        'id': 'f1',
        'farm_name': 'Test Farm',
        'description': null,
        'latitude': null,
        'longitude': null,
        'area_value': '2.5000',
        'area_unit': 'acre',
        'status': 'active',
      });
      expect(farm.farmName, 'Test Farm');
      expect(farm.areaValue, 2.5);
      expect(farm.latitude, isNull);
    });
  });

  group('CropCycle.fromJson', () {
    test('parses a nested crop object', () {
      final cycle = CropCycle.fromJson({
        'id': 'c1',
        'plot_id': 'p1',
        'crop': {'id': 'crop1', 'name': 'Tomato', 'category': 'vegetable'},
        'season': 'kharif',
        'sowing_date': '2026-06-01',
        'expected_harvest_date': '2026-09-01',
        'actual_harvest_date': null,
        'cultivation_status': 'planned',
        'seed_variety': null,
      });
      expect(cycle.crop.name, 'Tomato');
      expect(cycle.cultivationStatus, 'planned');
    });
  });
}
