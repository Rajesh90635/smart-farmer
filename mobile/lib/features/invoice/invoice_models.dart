/// Mirrors backend/app/schemas/invoice.py:InvoiceResponse exactly.
/// `extracted*` fields are OCR BEST GUESSES - this Flutter model has no
/// method that could confuse them with `confirmed*` fields or use them
/// to construct a ledger entry; only the backend's confirm() call does
/// that, from the farmer's own typed-in values.
library;

class Invoice {
  final String id;
  final String cropCycleId;
  final String ocrStatus;
  final String? ocrConfidence;
  final String? ocrUnavailableReason;
  final String? extractedAmount;
  final String? extractedDate;
  final String? extractedVendorName;
  final bool isConfirmed;
  final String? confirmedAmount;
  final String? confirmedDate;
  final String? confirmedVendorName;
  final String? confirmedCategory;
  final String? linkedLedgerEntryId;
  final String createdAt;

  Invoice({
    required this.id,
    required this.cropCycleId,
    required this.ocrStatus,
    this.ocrConfidence,
    this.ocrUnavailableReason,
    this.extractedAmount,
    this.extractedDate,
    this.extractedVendorName,
    required this.isConfirmed,
    this.confirmedAmount,
    this.confirmedDate,
    this.confirmedVendorName,
    this.confirmedCategory,
    this.linkedLedgerEntryId,
    required this.createdAt,
  });

  bool get ocrSucceeded => ocrStatus == 'completed';
  bool get ocrFailed => ocrStatus == 'failed';

  factory Invoice.fromJson(Map<String, dynamic> json) => Invoice(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        ocrStatus: json['ocr_status'] as String,
        ocrConfidence: json['ocr_confidence'] as String?,
        ocrUnavailableReason: json['ocr_unavailable_reason'] as String?,
        extractedAmount: json['extracted_amount'] as String?,
        extractedDate: json['extracted_date'] as String?,
        extractedVendorName: json['extracted_vendor_name'] as String?,
        isConfirmed: json['is_confirmed'] as bool,
        confirmedAmount: json['confirmed_amount'] as String?,
        confirmedDate: json['confirmed_date'] as String?,
        confirmedVendorName: json['confirmed_vendor_name'] as String?,
        confirmedCategory: json['confirmed_category'] as String?,
        linkedLedgerEntryId: json['linked_ledger_entry_id'] as String?,
        createdAt: json['created_at'] as String,
      );
}
