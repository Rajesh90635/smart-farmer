import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/harvest/harvest_models.dart';

Map<String, dynamic> _harvestJson({
  String status = 'planned',
  String? estimatedQuantity,
  String? actualQuantity,
  String? expectedHarvestDate,
  String? actualHarvestDate,
  String? qualityGrade,
}) => {
      'id': 'harvest-1',
      'crop_cycle_id': 'cycle-1',
      'crop_id': 'crop-1',
      'expected_harvest_date': expectedHarvestDate,
      'actual_harvest_date': actualHarvestDate,
      'estimated_quantity': estimatedQuantity,
      'actual_quantity': actualQuantity,
      'unit': 'kg',
      'quality_grade': qualityGrade,
      'status': status,
      'created_at': '2026-01-01T00:00:00Z',
    };

void main() {
  group('HarvestRecord', () {
    test('parses a freshly created harvest with all optional fields null', () {
      final harvest = HarvestRecord.fromJson(_harvestJson());
      expect(harvest.id, 'harvest-1');
      expect(harvest.cropCycleId, 'cycle-1');
      expect(harvest.status, 'planned');
      expect(harvest.estimatedQuantity, isNull);
      expect(harvest.actualQuantity, isNull);
      expect(harvest.qualityGrade, isNull);
    });

    test('keeps decimal quantity fields as strings, never parsed to double', () {
      final harvest = HarvestRecord.fromJson(_harvestJson(estimatedQuantity: '1000.00', actualQuantity: '950.50'));
      expect(harvest.estimatedQuantity, '1000.00');
      expect(harvest.actualQuantity, '950.50');
    });

    test('all 8 real HarvestStatus values parse verbatim, none fabricated', () {
      const statuses = [
        'planned',
        'approaching',
        'ready',
        'harvested',
        'listed',
        'partially_sold',
        'sold',
        'cancelled',
      ];
      for (final status in statuses) {
        final harvest = HarvestRecord.fromJson(_harvestJson(status: status));
        expect(harvest.status, status);
      }
    });

    test('parses dates when present', () {
      final harvest = HarvestRecord.fromJson(_harvestJson(
        expectedHarvestDate: '2026-03-01',
        actualHarvestDate: '2026-03-05',
      ));
      expect(harvest.expectedHarvestDate, '2026-03-01');
      expect(harvest.actualHarvestDate, '2026-03-05');
    });
  });

  group('HarvestListing', () {
    Map<String, dynamic> listingJson({String deliveryOption = 'buyer_collection', Map<String, dynamic>? serviceArea, String? preferredPrice, bool isActive = true}) => {
          'id': 'listing-1',
          'harvest_record_id': 'harvest-1',
          'crop_id': 'crop-1',
          'quantity_available': '1000.00',
          'unit': 'kg',
          'quality_grade': 'Grade A',
          'expected_availability_date': '2026-03-10',
          'service_area': serviceArea,
          'preferred_price': preferredPrice,
          'delivery_option': deliveryOption,
          'is_active': isActive,
          'created_at': '2026-01-01T00:00:00Z',
        };

    test('parses a full listing', () {
      final listing = HarvestListing.fromJson(listingJson(
        serviceArea: {'state': 'Kerala', 'district': 'Thrissur'},
        preferredPrice: '25.00',
      ));
      expect(listing.quantityAvailable, '1000.00');
      expect(listing.serviceArea, {'state': 'Kerala', 'district': 'Thrissur'});
      expect(listing.preferredPrice, '25.00');
      expect(listing.isActive, isTrue);
    });

    test('all 3 real CollectionOption values parse verbatim', () {
      const options = ['buyer_collection', 'farmer_delivery', 'third_party_logistics'];
      for (final option in options) {
        final listing = HarvestListing.fromJson(listingJson(deliveryOption: option));
        expect(listing.deliveryOption, option);
      }
    });

    test('null service_area and preferred_price parse without error', () {
      final listing = HarvestListing.fromJson(listingJson());
      expect(listing.serviceArea, isNull);
      expect(listing.preferredPrice, isNull);
    });

    test('inactive listing parses is_active as false', () {
      final listing = HarvestListing.fromJson(listingJson(isActive: false));
      expect(listing.isActive, isFalse);
    });
  });
}
