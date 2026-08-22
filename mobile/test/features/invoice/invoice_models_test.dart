import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/invoice/invoice_models.dart';

Map<String, dynamic> _invoiceJson({
  required String ocrStatus,
  required bool isConfirmed,
  String? ocrConfidence,
  String? extractedAmount,
  String? confirmedAmount,
}) =>
    {
      'id': 'invoice-1',
      'crop_cycle_id': 'cycle-1',
      'ocr_status': ocrStatus,
      'ocr_confidence': ocrConfidence,
      'ocr_unavailable_reason': null,
      'extracted_amount': extractedAmount,
      'extracted_date': null,
      'extracted_vendor_name': null,
      'is_confirmed': isConfirmed,
      'confirmed_amount': confirmedAmount,
      'confirmed_date': null,
      'confirmed_vendor_name': null,
      'confirmed_category': null,
      'linked_ledger_entry_id': null,
      'created_at': '2026-01-01T00:00:00Z',
    };

void main() {
  group('Invoice (Phase 30)', () {
    test('completed OCR status is recognized', () {
      final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'completed', isConfirmed: false, extractedAmount: '2450.00'));
      expect(invoice.ocrSucceeded, isTrue);
      expect(invoice.ocrFailed, isFalse);
    });

    test('failed OCR status is recognized', () {
      final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'failed', isConfirmed: false));
      expect(invoice.ocrFailed, isTrue);
      expect(invoice.ocrSucceeded, isFalse);
    });

    test('unconfirmed invoice carries extracted (best-guess) fields, not confirmed fields', () {
      final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'completed', isConfirmed: false, extractedAmount: '2450.00'));
      expect(invoice.extractedAmount, '2450.00');
      expect(invoice.confirmedAmount, isNull);
      expect(invoice.isConfirmed, isFalse);
    });

    test('confirmed invoice carries confirmed fields - the farmer-approved values', () {
      final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'completed', isConfirmed: true, extractedAmount: '2450.00', confirmedAmount: '2500.00'));
      expect(invoice.isConfirmed, isTrue);
      expect(invoice.confirmedAmount, '2500.00');
      expect(invoice.extractedAmount, '2450.00');
    });

    test('missing optional fields do not crash parsing', () {
      final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'pending', isConfirmed: false));
      expect(invoice.ocrConfidence, isNull);
      expect(invoice.extractedAmount, isNull);
      expect(invoice.confirmedAmount, isNull);
    });

    test('confidence is parsed as one of the three real backend values when present', () {
      for (final level in ['high', 'medium', 'low']) {
        final invoice = Invoice.fromJson(_invoiceJson(ocrStatus: 'completed', isConfirmed: false, ocrConfidence: level));
        expect(invoice.ocrConfidence, level);
      }
    });
  });
}
