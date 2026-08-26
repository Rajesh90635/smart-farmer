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
      expect(farm.stateId, isNull);
      expect(farm.stateName, isNull);
    });

    test('parses a full state/district/mandal/village chain, ids and names both', () {
      final farm = Farm.fromJson({
        'id': 'f1',
        'farm_name': 'Test Farm',
        'description': null,
        'latitude': '16.306000',
        'longitude': '80.436000',
        'state_id': 1,
        'district_id': 14,
        'mandal_id': 3,
        'village_id': 9,
        'state_name': 'Andhra Pradesh',
        'district_name': 'Guntur',
        'mandal_name': 'Tenali',
        'village_name': 'Angalakuduru',
        'area_value': '2.5000',
        'area_unit': 'acre',
        'status': 'active',
      });
      expect(farm.stateId, 1);
      expect(farm.districtId, 14);
      expect(farm.mandalId, 3);
      expect(farm.villageId, 9);
      expect(farm.stateName, 'Andhra Pradesh');
      expect(farm.districtName, 'Guntur');
      expect(farm.mandalName, 'Tenali');
      expect(farm.villageName, 'Angalakuduru');
    });

    test('a farm with only state/district picked leaves mandal/village null, not a fabricated value', () {
      final farm = Farm.fromJson({
        'id': 'f1',
        'farm_name': 'Test Farm',
        'description': null,
        'latitude': null,
        'longitude': null,
        'state_id': 1,
        'district_id': 14,
        'mandal_id': null,
        'village_id': null,
        'state_name': 'Andhra Pradesh',
        'district_name': 'Guntur',
        'mandal_name': null,
        'village_name': null,
        'area_value': '2.5000',
        'area_unit': 'acre',
        'status': 'active',
      });
      expect(farm.districtId, 14);
      expect(farm.mandalId, isNull);
      expect(farm.villageName, isNull);
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
      expect(cycle.varietyId, isNull);
    });

    test('parses a real variety_id when a structured variety was chosen', () {
      final cycle = CropCycle.fromJson({
        'id': 'c1',
        'plot_id': 'p1',
        'crop': {'id': 'crop1', 'name': 'Tomato', 'category': 'vegetable'},
        'season': 'kharif',
        'sowing_date': '2026-06-01',
        'expected_harvest_date': null,
        'actual_harvest_date': null,
        'cultivation_status': 'planned',
        'seed_variety': null,
        'variety_id': 'v1',
      });
      expect(cycle.varietyId, 'v1');
    });
  });

  group('CropVariety.fromJson', () {
    test('parses a variety with a typical duration', () {
      final variety = CropVariety.fromJson({
        'id': 'v1',
        'crop_id': 'crop1',
        'name': 'Pusa Ruby',
        'typical_duration_days': 75,
      });
      expect(variety.name, 'Pusa Ruby');
      expect(variety.typicalDurationDays, 75);
    });

    test('leaves typical duration null rather than fabricating one', () {
      final variety = CropVariety.fromJson({
        'id': 'v1',
        'crop_id': 'crop1',
        'name': 'Local',
        'typical_duration_days': null,
      });
      expect(variety.typicalDurationDays, isNull);
    });
  });
}
