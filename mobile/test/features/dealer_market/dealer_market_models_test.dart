import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/dealer_market/dealer_market_models.dart';

void main() {
  group('Product.fromJson', () {
    test('parses a real product with active ingredients', () {
      final product = Product.fromJson({
        'id': 'p1',
        'name': 'NPK Fertilizer',
        'category': 'fertilizer',
        'manufacturer': 'AgriCo',
        'active_ingredients': ['N', 'P', 'K'],
        'pack_size_value': '50.00',
        'pack_size_unit': 'kg',
        'description': null,
        'usage_information': null,
        'status': 'approved',
      });
      expect(product.name, 'NPK Fertilizer');
      expect(product.activeIngredients, ['N', 'P', 'K']);
    });

    test('a null active_ingredients list becomes empty, never fabricated', () {
      final product = Product.fromJson({
        'id': 'p1',
        'name': 'Local Seed',
        'category': 'seed',
        'manufacturer': null,
        'active_ingredients': null,
        'pack_size_value': '1.00',
        'pack_size_unit': 'kg',
        'description': null,
        'usage_information': null,
        'status': 'approved',
      });
      expect(product.activeIngredients, isEmpty);
    });
  });

  group('DealerOffer.fromJson and PriceComparison.fromJson', () {
    test('parses real dealer offers, the only place dealer_product_id is surfaced', () {
      final comparison = PriceComparison.fromJson({
        'product_id': 'p1',
        'reference_price': '500.00',
        'reference_price_per_unit': '10.00',
        'reference_source': 'government',
        'offers': [
          {
            'dealer_product_id': 'dp1',
            'dealer_id': 'd1',
            'dealer_price': '520.00',
            'price_per_unit': '10.40',
            'unit': 'kg',
            'stock_quantity': 100,
            'is_available': true,
          },
        ],
      });
      expect(comparison.offers.length, 1);
      expect(comparison.offers.first.dealerProductId, 'dp1');
      expect(comparison.offers.first.isAvailable, isTrue);
    });

    test('no offers and no reference price parses honestly, never fabricated', () {
      final comparison = PriceComparison.fromJson({
        'product_id': 'p1',
        'reference_price': null,
        'reference_price_per_unit': null,
        'reference_source': null,
        'offers': [],
      });
      expect(comparison.offers, isEmpty);
      expect(comparison.referencePricePerUnit, isNull);
    });
  });

  group('DealerOrder.fromJson', () {
    test('a draft order (cart) has null money fields, never a fabricated total', () {
      final order = DealerOrder.fromJson({
        'id': 'o1',
        'dealer_id': 'd1',
        'status': 'draft',
        'subtotal_amount': null,
        'discount_amount': null,
        'delivery_fee_amount': null,
        'tax_amount': null,
        'final_amount': null,
        'rejection_reason': null,
        'items': [
          {'id': 'i1', 'dealer_product_id': 'dp1', 'product_name_snapshot': 'NPK Fertilizer', 'quantity': 2, 'unit_price': null, 'final_item_amount': null},
        ],
        'created_at': '2026-08-26T00:00:00Z',
      });
      expect(order.status, 'draft');
      expect(order.finalAmount, isNull);
      expect(order.items.first.unitPrice, isNull);
    });

    test('a confirmed order has real server-computed money fields', () {
      final order = DealerOrder.fromJson({
        'id': 'o1',
        'dealer_id': 'd1',
        'status': 'confirmed',
        'subtotal_amount': '1000.00',
        'discount_amount': '0.00',
        'delivery_fee_amount': '50.00',
        'tax_amount': '50.00',
        'final_amount': '1100.00',
        'rejection_reason': null,
        'items': [
          {'id': 'i1', 'dealer_product_id': 'dp1', 'product_name_snapshot': 'NPK Fertilizer', 'quantity': 2, 'unit_price': '500.00', 'final_item_amount': '1050.00'},
        ],
        'created_at': '2026-08-26T00:00:00Z',
      });
      expect(order.finalAmount, '1100.00');
      expect(order.items.first.finalItemAmount, '1050.00');
    });
  });

  group('cancellableOrderStatuses', () {
    test('mirrors ALLOWED_ORDER_TRANSITIONS cancel-eligible source statuses exactly', () {
      expect(cancellableOrderStatuses, {'draft', 'pending_confirmation', 'confirmed', 'payment_pending', 'accepted_by_dealer'});
    });

    test('a delivered order is never cancellable - it can only be disputed', () {
      expect(cancellableOrderStatuses.contains('delivered'), isFalse);
    });
  });

  group('orderDisputeReasons', () {
    test('matches the exact real backend DisputeReason enum values', () {
      expect(orderDisputeReasons, [
        'wrong_product',
        'missing_item',
        'damaged_product',
        'payment_issue',
        'delivery_issue',
        'unexpected_charge',
        'product_authenticity_concern',
      ]);
    });
  });
}
