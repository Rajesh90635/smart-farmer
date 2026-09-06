import '../../core/api_client.dart';
import '../../core/offline/pending_write_queue.dart';
import '../crop_photo/network_status_checker.dart';
import 'ledger_models.dart';

class LedgerRepository {
  final ApiClient _apiClient;
  LedgerRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// D81-06 (docs/audit/FINAL_CANONICAL_group_D.md): same optional-param
  /// offline-queueing shape as FarmRepository.createFarm (D81-01).
  Future<LedgerEntry> createEntry({
    required String cropCycleId,
    required String entryType,
    required String category,
    required String amount,
    required String entryDate,
    String? description,
    NetworkStatusChecker? networkChecker,
    PendingWriteQueue? writeQueue,
  }) async {
    final body = {
      'entry_type': entryType,
      'category': category,
      'amount': amount,
      'entry_date': entryDate,
      if (description != null) 'description': description,
    };

    if (networkChecker != null && writeQueue != null && !(await networkChecker.isOnline())) {
      await writeQueue.enqueue(
        PendingWrite(clientRequestId: generateClientRequestId(), method: 'POST', path: '/crop-cycles/$cropCycleId/ledger/entries', body: body),
      );
      throw const QueuedForSyncException();
    }

    final response = await _apiClient.post('/crop-cycles/$cropCycleId/ledger/entries', body: body);
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
