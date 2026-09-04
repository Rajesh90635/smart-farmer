import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../ledger/ledger_models.dart';
import 'invoice_models.dart';
import 'invoice_repository.dart';

/// Every extracted field shown here is clearly labeled as OCR's BEST
/// GUESS - the confirm form is pre-filled with these values purely for
/// farmer convenience, but the farmer can edit every field before
/// submitting, and the actual ledger entry is only ever created from
/// whatever the farmer submits, never silently from the raw OCR output.
class InvoiceListScreen extends StatefulWidget {
  final String cropCycleId;
  const InvoiceListScreen({super.key, required this.cropCycleId});

  @override
  State<InvoiceListScreen> createState() => _InvoiceListScreenState();
}

class _InvoiceListScreenState extends State<InvoiceListScreen> {
  List<Invoice> _invoices = [];
  bool _loading = true;
  bool _uploading = false;
  String? _error;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final invoices = await context.read<InvoiceRepository>().listInvoices(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _invoices = invoices;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
  }

  Future<void> _pickAndUpload(ImageSource source, AppLocalizations l10n) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 95);
    if (picked == null) return;

    setState(() => _uploading = true);
    try {
      final bytes = await picked.readAsBytes();
      final invoice = await context.read<InvoiceRepository>().uploadInvoice(
            cropCycleId: widget.cropCycleId,
            fileBytes: bytes,
            fileName: picked.name,
            mimeType: 'image/jpeg',
          );
      await _load();
      if (!mounted) return;
      if (invoice.ocrFailed) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(invoice.ocrUnavailableReason ?? l10n.ocrFailedMessage)));
      } else {
        _showConfirmSheet(invoice, l10n);
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _showConfirmSheet(Invoice invoice, AppLocalizations l10n) async {
    final amountController = TextEditingController(text: invoice.extractedAmount ?? '');
    final vendorController = TextEditingController(text: invoice.extractedVendorName ?? '');
    String selectedCategory = expenseCategoryOptions.first;
    DateTime selectedDate = invoice.extractedDate != null ? DateTime.tryParse(invoice.extractedDate!) ?? DateTime.now() : DateTime.now();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.reviewInvoiceTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 4),
              Text(l10n.reviewInvoiceHint, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              if (invoice.ocrConfidence != null) ...[
                const SizedBox(height: 4),
                Text('${l10n.ocrConfidenceLabel}: ${invoice.ocrConfidence}', style: const TextStyle(fontSize: 12)),
              ],
              const SizedBox(height: 12),
              TextField(
                controller: amountController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: l10n.amountLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: vendorController, decoration: InputDecoration(labelText: l10n.vendorNameOptionalLabel)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedCategory,
                items: expenseCategoryOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setSheetState(() => selectedCategory = v ?? selectedCategory),
                decoration: InputDecoration(labelText: l10n.categoryLabel),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: sheetContext,
                    initialDate: selectedDate,
                    firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) setSheetState(() => selectedDate = picked);
                },
                child: Text(selectedDate.toIso8601String().split('T').first),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  final amountText = amountController.text.trim();
                  if (amountText.isEmpty || double.tryParse(amountText) == null) return;
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<InvoiceRepository>().confirmInvoice(
                          invoiceId: invoice.id,
                          amount: amountText,
                          entryDate: selectedDate.toIso8601String().split('T').first,
                          vendorName: vendorController.text.trim().isEmpty ? null : vendorController.text.trim(),
                          category: selectedCategory,
                        );
                    await _load();
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.invoiceConfirmedMessage)));
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  }
                },
                child: Text(l10n.confirmAndAddToLedgerButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _deleteInvoice(Invoice invoice) async {
    try {
      await context.read<InvoiceRepository>().deleteInvoice(invoice.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.invoicesTitle)),
      floatingActionButton: _uploading
          ? const FloatingActionButton(onPressed: null, child: CircularProgressIndicator(color: Colors.white))
          : FloatingActionButton(
              onPressed: () => showModalBottomSheet(
                context: context,
                builder: (sheetContext) => SafeArea(
                  child: Wrap(children: [
                    ListTile(
                      leading: const Icon(Icons.camera_alt),
                      title: Text(l10n.takePhotoOption),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        _pickAndUpload(ImageSource.camera, l10n);
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.photo_library),
                      title: Text(l10n.chooseFromGalleryOption),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        _pickAndUpload(ImageSource.gallery, l10n);
                      },
                    ),
                  ]),
                ),
              ),
              child: const Icon(Icons.add_a_photo),
            ),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(child: Text(_error!)),
          const SizedBox(height: 12),
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
        ],
      );
    }
    if (_invoices.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noInvoicesYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _invoices.map((invoice) => _buildInvoiceCard(invoice, l10n)).toList(),
    );
  }

  Widget _buildInvoiceCard(Invoice invoice, AppLocalizations l10n) {
    return Card(
      child: ListTile(
        leading: Icon(
          invoice.isConfirmed ? Icons.check_circle : (invoice.ocrFailed ? Icons.error_outline : Icons.hourglass_empty),
          color: invoice.isConfirmed ? Colors.green : (invoice.ocrFailed ? Colors.red : Colors.orange),
        ),
        title: Text(invoice.isConfirmed ? '${l10n.confirmedLabel}: ${invoice.confirmedAmount}' : (invoice.extractedAmount ?? l10n.noAmountFoundLabel)),
        subtitle: Text(invoice.isConfirmed ? (invoice.confirmedVendorName ?? '') : l10n.notYetConfirmedLabel),
        trailing: invoice.isConfirmed
            ? null
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (invoice.ocrSucceeded) IconButton(icon: const Icon(Icons.edit), onPressed: () => _showConfirmSheet(invoice, l10n)),
                  IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _deleteInvoice(invoice)),
                ],
              ),
      ),
    );
  }
}
