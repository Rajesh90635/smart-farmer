import '../../core/api_client.dart';
import 'ledger_models.dart';

class LedgerRepository {
  final ApiClient _apiClient;
  LedgerRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<LedgerEntry> createEntry({
    required String cropCycleId,
    required String entryType,
    required String category,
    required String amount,
    required String entryDate,
    String? description,
  }) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/ledger/entries', body: {
      'entry_type': entryType,
      'category': category,
      'amount': amount,
      'entry_date': entryDate,
      if (description != null) 'description': description,
    });
    return LedgerEntry.fromJson(response);
  }

  Future<LedgerSummary> getSummary(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/ledger');
    return LedgerSummary.fromJson(response);
  }

  Future<int> importCompletedSales(String cropCycleId) async {
    final response = await _apiClient.post('/crop-cycles/$cropCycleId/ledger/import-sales');
    return response['imported_count'] as int;
  }

  Future<void> deleteEntry(String entryId) async {
    await _apiClient.delete('/ledger/entries/$entryId');
  }
}
