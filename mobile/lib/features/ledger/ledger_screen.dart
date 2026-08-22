import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../invoice/invoice_list_screen.dart';
import 'ledger_models.dart';
import 'ledger_repository.dart';

/// Every figure on this screen is read directly from the backend's own
/// LedgerSummary - total_expense/total_revenue/net are all real SQL
/// aggregates computed server-side, never recalculated here. Sale-linked
/// entries (imported from a completed harvest sale) are visually marked
/// and cannot be deleted through this screen, matching the backend's own
/// rule exactly.
class LedgerScreen extends StatefulWidget {
  final String cropCycleId;
  const LedgerScreen({super.key, required this.cropCycleId});

  @override
  State<LedgerScreen> createState() => _LedgerScreenState();
}

class _LedgerScreenState extends State<LedgerScreen> {
  LedgerSummary? _summary;
  bool _loading = true;
  String? _error;
  bool _importing = false;

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
      final summary = await context.read<LedgerRepository>().getSummary(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _summary = summary;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  Future<void> _importSales(AppLocalizations l10n) async {
    setState(() => _importing = true);
    try {
      final count = await context.read<LedgerRepository>().importCompletedSales(widget.cropCycleId);
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(count > 0 ? '${l10n.salesImportedMessage} ($count)' : l10n.noNewSalesToImport)),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  Future<void> _deleteEntry(LedgerEntry entry) async {
    try {
      await context.read<LedgerRepository>().deleteEntry(entry.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _showAddEntrySheet(AppLocalizations l10n) async {
    String selectedEntryType = 'expense';
    String selectedCategory = expenseCategoryOptions.first;
    final amountController = TextEditingController();
    final descriptionController = TextEditingController();
    DateTime selectedDate = DateTime.now();

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
              Text(l10n.addLedgerEntryTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              SegmentedButton<String>(
                segments: [
                  ButtonSegment(value: 'expense', label: Text(l10n.expenseLabel)),
                  ButtonSegment(value: 'revenue', label: Text(l10n.revenueLabel)),
                ],
                selected: {selectedEntryType},
                onSelectionChanged: (selection) {
                  setSheetState(() {
                    selectedEntryType = selection.first;
                    selectedCategory = selectedEntryType == 'expense' ? expenseCategoryOptions.first : revenueCategoryOptions.first;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedCategory,
                items: (selectedEntryType == 'expense' ? expenseCategoryOptions : revenueCategoryOptions)
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (v) => setSheetState(() => selectedCategory = v ?? selectedCategory),
                decoration: InputDecoration(labelText: l10n.categoryLabel),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: amountController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: l10n.amountLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: descriptionController, decoration: InputDecoration(labelText: l10n.descriptionOptionalLabel)),
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
                    await context.read<LedgerRepository>().createEntry(
                          cropCycleId: widget.cropCycleId,
                          entryType: selectedEntryType,
                          category: selectedCategory,
                          amount: amountText,
                          entryDate: selectedDate.toIso8601String().split('T').first,
                          description: descriptionController.text.trim().isEmpty ? null : descriptionController.text.trim(),
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                  }
                },
                child: Text(l10n.saveEntryButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.ledgerTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.receipt_long),
            tooltip: l10n.invoicesTitle,
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => InvoiceListScreen(cropCycleId: widget.cropCycleId)),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(onPressed: () => _showAddEntrySheet(l10n), child: const Icon(Icons.add)),
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
          Center(child: ElevatedButton(onPressed: _load, child: const Text('Try again'))),
        ],
      );
    }

    final summary = _summary!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildTotalsCard(summary, l10n),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: _importing ? null : () => _importSales(l10n),
          icon: _importing ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.sync),
          label: Text(l10n.importSalesButton),
        ),
        const SizedBox(height: 16),
        if (summary.entries.isEmpty)
          Padding(padding: const EdgeInsets.only(top: 40), child: Center(child: Text(l10n.noLedgerEntriesYet)))
        else
          ...summary.entries.map((entry) => _buildEntryCard(entry, l10n)),
      ],
    );
  }

  Widget _buildTotalsCard(LedgerSummary summary, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _totalsRow(l10n.totalExpenseLabel, summary.totalExpense, Colors.red),
            _totalsRow(l10n.totalRevenueLabel, summary.totalRevenue, Colors.green),
            const Divider(),
            _totalsRow(l10n.netLabel, summary.net, null, bold: true),
          ],
        ),
      ),
    );
  }

  Widget _totalsRow(String label, String amount, Color? color, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
          Text(amount, style: TextStyle(color: color, fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
        ],
      ),
    );
  }

  Widget _buildEntryCard(LedgerEntry entry, AppLocalizations l10n) {
    return Card(
      child: ListTile(
        leading: Icon(entry.isExpense ? Icons.arrow_upward : Icons.arrow_downward, color: entry.isExpense ? Colors.red : Colors.green),
        title: Text('${entry.category} - ${entry.amount}'),
        subtitle: Text(entry.description ?? entry.entryDate),
        trailing: entry.isDeletable
            ? IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _deleteEntry(entry))
            : Tooltip(message: l10n.linkedFromSaleTooltip, child: const Icon(Icons.link, color: Colors.grey)),
      ),
    );
  }
}
