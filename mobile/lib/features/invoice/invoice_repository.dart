import '../../core/api_client.dart';
import 'invoice_models.dart';

class InvoiceRepository {
  final ApiClient _apiClient;
  InvoiceRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<Invoice> uploadInvoice({
    required String cropCycleId,
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
  }) async {
    final response = await _apiClient.uploadMultipart(
      '/crop-cycles/$cropCycleId/invoices',
      fileBytes: fileBytes,
      fileName: fileName,
      mimeType: mimeType,
      fields: const {},
    );
    return Invoice.fromJson(response);
  }

  Future<List<Invoice>> listInvoices(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/invoices');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Invoice.fromJson).toList();
  }

  Future<Invoice> getInvoice(String invoiceId) async {
    final response = await _apiClient.get('/invoices/$invoiceId');
    return Invoice.fromJson(response);
  }

  /// The ONLY call that creates a real ledger entry from an invoice -
  /// always with the farmer's own reviewed/typed values, never the raw
  /// extracted_* fields sent back silently without the farmer having
  /// actually looked at them.
  Future<Invoice> confirmInvoice({
    required String invoiceId,
    required String amount,
    required String entryDate,
    String? vendorName,
    required String category,
  }) async {
    final response = await _apiClient.post('/invoices/$invoiceId/confirm', body: {
      'amount': amount,
      'entry_date': entryDate,
      if (vendorName != null) 'vendor_name': vendorName,
      'category': category,
    });
    return Invoice.fromJson(response);
  }

  Future<void> deleteInvoice(String invoiceId) async {
    await _apiClient.delete('/invoices/$invoiceId');
  }
}
