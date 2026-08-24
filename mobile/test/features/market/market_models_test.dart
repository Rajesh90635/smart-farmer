import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/market/market_models.dart';

void main() {
  group('Offer', () {
    Map<String, dynamic> offerJson({String status = 'active'}) => {
          'id': 'offer-1',
          'harvest_listing_id': 'listing-1',
          'buyer_id': 'buyer-1',
          'quantity': '500.00',
          'unit': 'kg',
          'price_per_unit': '30.00',
          'status': status,
          'created_at': '2026-01-01T00:00:00Z',
        };

    test('parses a full offer, decimal fields kept as strings', () {
      final offer = Offer.fromJson(offerJson());
      expect(offer.quantity, '500.00');
      expect(offer.pricePerUnit, '30.00');
      expect(offer.status, 'active');
    });

    test('all 6 real OfferStatus values parse verbatim, none fabricated', () {
      const statuses = ['active', 'expired', 'accepted', 'rejected', 'cancelled', 'completed'];
      for (final status in statuses) {
        expect(Offer.fromJson(offerJson(status: status)).status, status);
      }
    });
  });

  group('CounterOffer', () {
    Map<String, dynamic> counterJson({String proposedBy = 'farmer', String? message}) => {
          'id': 'counter-1',
          'buyer_offer_id': 'offer-1',
          'proposed_by': proposedBy,
          'price_per_unit': '34.00',
          'quantity': '500.00',
          'message': message,
          'created_at': '2026-01-01T00:00:00Z',
        };

    test('parses a farmer counter-offer with a message', () {
      final counter = CounterOffer.fromJson(counterJson(message: 'Best I can do'));
      expect(counter.proposedBy, 'farmer');
      expect(counter.message, 'Best I can do');
    });

    test('parses a buyer counter-offer with no message', () {
      final counter = CounterOffer.fromJson(counterJson(proposedBy: 'buyer'));
      expect(counter.proposedBy, 'buyer');
      expect(counter.message, isNull);
    });
  });

  group('SaleOrder', () {
    Map<String, dynamic> saleJson({String status = 'pending', String? cancellationReason}) => {
          'id': 'sale-1',
          'harvest_listing_id': 'listing-1',
          'buyer_id': 'buyer-1',
          'crop_id': 'crop-1',
          'quantity': '500.00',
          'unit': 'kg',
          'price_per_unit': '32.00',
          'gross_value': '16000.00',
          'charges': '200.00',
          'net_value': '15800.00',
          'collection_method': 'buyer_collection',
          'status': status,
          'cancellation_reason': cancellationReason,
          'created_at': '2026-01-01T00:00:00Z',
        };

    test('parses a full sale order', () {
      final sale = SaleOrder.fromJson(saleJson());
      expect(sale.grossValue, '16000.00');
      expect(sale.charges, '200.00');
      expect(sale.netValue, '15800.00');
      expect(sale.cancellationReason, isNull);
    });

    test('all 11 real SaleOrderStatus values parse verbatim, none fabricated', () {
      const statuses = [
        'pending',
        'accepted',
        'preparing',
        'ready_for_collection',
        'collected',
        'in_transit',
        'delivered',
        'payment_pending',
        'paid',
        'cancelled',
        'disputed',
      ];
      for (final status in statuses) {
        expect(SaleOrder.fromJson(saleJson(status: status)).status, status);
      }
    });

    test('parses a cancelled sale with its reason', () {
      final sale = SaleOrder.fromJson(saleJson(status: 'cancelled', cancellationReason: 'weather'));
      expect(sale.status, 'cancelled');
      expect(sale.cancellationReason, 'weather');
    });
  });
}
