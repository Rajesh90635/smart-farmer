/// Mirrors backend/app/schemas/ledger.py exactly. `totalExpense`,
/// `totalRevenue`, and `net` are all backend-COMPUTED via a real SQL
/// aggregate over actual entries - this Flutter model never recomputes
/// them independently, so the displayed totals can never drift from
/// what the backend's own database aggregate says.
library;

class LedgerEntry {
  final String id;
  final String cropCycleId;
  final String entryType;
  final String category;
  final String amount;
  final String entryDate;
  final String? description;
  final String source;
  final String? linkedSaleId;
  final String createdAt;

  LedgerEntry({
    required this.id,
    required this.cropCycleId,
    required this.entryType,
    required this.category,
    required this.amount,
    required this.entryDate,
    this.description,
    required this.source,
    this.linkedSaleId,
    required this.createdAt,
  });

  bool get isExpense => entryType == 'expense';
  bool get isRevenue => entryType == 'revenue';
  bool get isDeletable => source == 'manual';

  factory LedgerEntry.fromJson(Map<String, dynamic> json) => LedgerEntry(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        entryType: json['entry_type'] as String,
        category: json['category'] as String,
        amount: json['amount'] as String,
        entryDate: json['entry_date'] as String,
        description: json['description'] as String?,
        source: json['source'] as String,
        linkedSaleId: json['linked_sale_id'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class LedgerSummary {
  final String cropCycleId;
  final String totalExpense;
  final String totalRevenue;
  final String net;
  final List<LedgerEntry> entries;

  LedgerSummary({
    required this.cropCycleId,
    required this.totalExpense,
    required this.totalRevenue,
    required this.net,
    required this.entries,
  });

  factory LedgerSummary.fromJson(Map<String, dynamic> json) => LedgerSummary(
        cropCycleId: json['crop_cycle_id'] as String,
        totalExpense: json['total_expense'] as String,
        totalRevenue: json['total_revenue'] as String,
        net: json['net'] as String,
        entries: (json['entries'] as List).map((e) => LedgerEntry.fromJson(e as Map<String, dynamic>)).toList(),
      );
}

const List<String> expenseCategoryOptions = ['seed', 'fertilizer', 'pesticide', 'labor', 'equipment', 'irrigation', 'land_rent', 'transport', 'other'];
const List<String> revenueCategoryOptions = ['harvest_sale', 'other'];
