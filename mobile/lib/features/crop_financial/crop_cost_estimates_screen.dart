import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../ledger/ledger_models.dart';
import 'crop_financial_models.dart';
import 'crop_financial_repository.dart';

/// The itemized list behind Financial Summary's single `Estimated Cost`
/// figure. That figure is a real backend SUM over every CropCostEstimate
/// row for the crop cycle - entering "seed: 500" and later "seed: 700"
/// does not overwrite the first estimate, it adds a second row and the
/// total becomes 1200. Until this screen existed, a farmer had no way to
/// see that two rows were behind that total, or to remove one of them;
/// `CropFinancialRepository.listEstimates`/`deleteEstimate` already
/// called the real backend endpoints but were never used anywhere. This
/// screen finally uses them - no backend or repository change needed.
class CropCostEstimatesScreen extends StatefulWidget {
  final String cropCycleId;
  const CropCostEstimatesScreen({super.key, required this.cropCycleId});

  @override
  State<CropCostEstimatesScreen> createState() => _CropCostEstimatesScreenState();
}

class _CropCostEstimatesScreenState extends State<CropCostEstimatesScreen> {
  List<CropCostEstimate>? _estimates;
  bool _loading = true;
  String? _error;

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
      final estimates = await context.read<CropFinancialRepository>().listEstimates(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _estimates = estimates;
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

  Future<void> _deleteEstimate(CropCostEstimate estimate) async {
    try {
      await context.read<CropFinancialRepository>().deleteEstimate(estimate.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _showAddEstimateSheet(AppLocalizations l10n) async {
    String selectedCategory = expenseCategoryOptions.first;
    final amountController = TextEditingController();
    final descriptionController = TextEditingController();

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
              Text(l10n.addEstimateTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 4),
              Text(l10n.addEstimateHint, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedCategory,
                items: expenseCategoryOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setSheetState(() => selectedCategory = v ?? selectedCategory),
                decoration: InputDecoration(labelText: l10n.categoryLabel),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: amountController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: l10n.estimatedAmountLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: descriptionController, decoration: InputDecoration(labelText: l10n.descriptionOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  final amountText = amountController.text.trim();
                  if (amountText.isEmpty || double.tryParse(amountText) == null) return;
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<CropFinancialRepository>().createEstimate(
                          cropCycleId: widget.cropCycleId,
                          category: selectedCategory,
                          estimatedAmount: amountText,
                          description: descriptionController.text.trim().isEmpty ? null : descriptionController.text.trim(),
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                  }
                },
                child: Text(l10n.saveEstimateButton),
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
      appBar: AppBar(title: Text(l10n.myEstimatesTitle)),
      floatingActionButton: FloatingActionButton(onPressed: () => _showAddEstimateSheet(l10n), child: const Icon(Icons.add)),
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

    final estimates = _estimates!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (estimates.isEmpty)
          Padding(padding: const EdgeInsets.only(top: 40), child: Center(child: Text(l10n.noEstimatesYet)))
        else
          ...estimates.map((estimate) => _buildEstimateCard(estimate)),
      ],
    );
  }

  Widget _buildEstimateCard(CropCostEstimate estimate) {
    return Card(
      child: ListTile(
        title: Text('${estimate.category} - ${estimate.estimatedAmount}'),
        subtitle: estimate.description != null ? Text(estimate.description!) : null,
        trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _deleteEstimate(estimate)),
      ),
    );
  }
}
