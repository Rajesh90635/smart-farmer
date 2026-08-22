import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/ledger/ledger_models.dart';

Map<String, dynamic> _entryJson({
  required String entryType,
  required String source,
  String? linkedSaleId,
}) =>
    {
      'id': 'entry-1',
      'crop_cycle_id': 'cycle-1',
      'entry_type': entryType,
      'category': 'seed',
      'amount': '500.00',
      'entry_date': '2026-01-01',
      'description': null,
      'source': source,
      'linked_sale_id': linkedSaleId,
      'created_at': '2026-01-01T00:00:00Z',
    };

void main() {
  group('LedgerEntry (Phase 29)', () {
    test('expense entry is recognized correctly', () {
      final entry = LedgerEntry.fromJson(_entryJson(entryType: 'expense', source: 'manual'));
      expect(entry.isExpense, isTrue);
      expect(entry.isRevenue, isFalse);
    });

    test('revenue entry is recognized correctly', () {
      final entry = LedgerEntry.fromJson(_entryJson(entryType: 'revenue', source: 'manual'));
      expect(entry.isRevenue, isTrue);
      expect(entry.isExpense, isFalse);
    });

    test('manual entry is deletable', () {
      final entry = LedgerEntry.fromJson(_entryJson(entryType: 'expense', source: 'manual'));
      expect(entry.isDeletable, isTrue);
    });

    test('sale-linked entry is NOT deletable - reflects a real transaction that already happened', () {
      final entry = LedgerEntry.fromJson(_entryJson(entryType: 'revenue', source: 'sale_linked', linkedSaleId: 'sale-1'));
      expect(entry.isDeletable, isFalse);
      expect(entry.linkedSaleId, 'sale-1');
    });

    test('missing optional fields do not crash parsing', () {
      final entry = LedgerEntry.fromJson(_entryJson(entryType: 'expense', source: 'manual'));
      expect(entry.description, isNull);
      expect(entry.linkedSaleId, isNull);
    });
  });

  group('LedgerSummary (Phase 29)', () {
    test('totals are read directly from the backend, never recomputed client-side', () {
      final json = {
        'crop_cycle_id': 'cycle-1',
        'total_expense': '800.00',
        'total_revenue': '1200.00',
        'net': '400.00',
        'entries': [
          _entryJson(entryType: 'expense', source: 'manual'),
          _entryJson(entryType: 'revenue', source: 'sale_linked', linkedSaleId: 'sale-1'),
        ],
      };
      final summary = LedgerSummary.fromJson(json);
      expect(summary.totalExpense, '800.00');
      expect(summary.totalRevenue, '1200.00');
      expect(summary.net, '400.00');
      expect(summary.entries.length, 2);
    });

    test('empty ledger parses with zero totals and no entries, not a crash', () {
      final json = {
        'crop_cycle_id': 'cycle-1',
        'total_expense': '0',
        'total_revenue': '0',
        'net': '0',
        'entries': [],
      };
      final summary = LedgerSummary.fromJson(json);
      expect(summary.entries, isEmpty);
    });
  });

  group('Category options (Phase 29)', () {
    test('expense categories match the exact real backend LedgerCategory values used for expenses', () {
      expect(expenseCategoryOptions, ['seed', 'fertilizer', 'pesticide', 'labor', 'equipment', 'irrigation', 'land_rent', 'transport', 'other']);
    });

    test('revenue categories are a distinct, smaller set', () {
      expect(revenueCategoryOptions, ['harvest_sale', 'other']);
    });
  });
}
