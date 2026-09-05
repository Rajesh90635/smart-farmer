import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../ledger/ledger_models.dart';
import 'crop_cost_estimates_screen.dart';
import 'crop_financial_models.dart';
import 'crop_financial_repository.dart';

/// Every figure here is read directly from the backend's own
/// CropFinancialSummary - estimated and actual are computed from
/// entirely separate sources server-side and this screen never mixes
/// them or recomputes anything. `null` fields are always rendered as an
/// explicit "Not available" label - never as a blank space that could
/// be mistaken for zero.
class CropFinancialSummaryScreen extends StatefulWidget {
  final String cropCycleId;
  const CropFinancialSummaryScreen({super.key, required this.cropCycleId});

  @override
  State<CropFinancialSummaryScreen> createState() => _CropFinancialSummaryScreenState();
}

class _CropFinancialSummaryScreenState extends State<CropFinancialSummaryScreen> {
  CropFinancialSummary? _summary;
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
      final summary = await context.read<CropFinancialRepository>().getFinancialSummary(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _summary = summary;
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

  Future<void> _showAddEstimateSheet(AppLocalizations l10n) async {
    final amountController = TextEditingController();
    String selectedCategory = expenseCategoryOptions.first;

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
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
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
      appBar: AppBar(
        title: Text(l10n.financialSummaryTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.format_list_bulleted),
            tooltip: l10n.myEstimatesTitle,
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CropCostEstimatesScreen(cropCycleId: widget.cropCycleId)),
              );
              _load();
            },
          ),
        ],
      ),
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
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
        ],
      );
    }

    final s = _summary!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildCostSection(s, l10n),
        const SizedBox(height: 16),
        _buildRevenueProfitSection(s, l10n),
        if (s.stageSummaries.isNotEmpty) ...[
          const SizedBox(height: 24),
          Text(l10n.stageWiseBreakdownTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          _buildStageTable(s.stageSummaries, l10n),
        ],
      ],
    );
  }

  Widget _buildCostSection(CropFinancialSummary s, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.costAnalysisLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _metricRow(l10n.estimatedCostLabel, s.estimatedCost, l10n),
            _metricRow(l10n.actualCostLabel, s.actualCost, l10n),
            _metricRow(l10n.costVarianceLabel, s.costVariance, l10n, highlightSign: true),
            _metricRow(l10n.costPerAcreLabel, s.costPerAcre, l10n),
          ],
        ),
      ),
    );
  }

  Widget _buildRevenueProfitSection(CropFinancialSummary s, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.revenueAndProfitLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _metricRow(l10n.expectedRevenueLabel, s.expectedRevenue, l10n),
            _metricRow(l10n.actualRevenueLabel, s.actualRevenue, l10n),
            _metricRow(l10n.estimatedProfitLabel, s.estimatedProfit, l10n),
            _metricRow(l10n.actualProfitLossLabel, s.actualProfitLoss, l10n, highlightSign: true),
            _metricRow(l10n.revenuePerAcreLabel, s.revenuePerAcre, l10n),
            _metricRow(l10n.profitLossPerAcreLabel, s.profitLossPerAcre, l10n, highlightSign: true),
            if (!s.hasAnyActualRevenue)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(l10n.noRevenueYetHint, style: const TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _metricRow(String label, String? value, AppLocalizations l10n, {bool highlightSign = false}) {
    final isNegative = highlightSign && value != null && value.startsWith('-');
    final isPositive = highlightSign && value != null && !value.startsWith('-') && value != '0' && value != '0.00';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value ?? l10n.notAvailableLabel,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: value == null ? Colors.grey : (isNegative ? Colors.red : (isPositive ? Colors.green : null)),
              fontStyle: value == null ? FontStyle.italic : FontStyle.normal,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStageTable(List<StageFinancialSummary> stages, AppLocalizations l10n) {
    return Card(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(flex: 2, child: Text(l10n.stageLabel, style: const TextStyle(fontWeight: FontWeight.bold))),
                Expanded(child: Text(l10n.estimatedShortLabel, style: const TextStyle(fontWeight: FontWeight.bold), textAlign: TextAlign.right)),
                Expanded(child: Text(l10n.actualShortLabel, style: const TextStyle(fontWeight: FontWeight.bold), textAlign: TextAlign.right)),
                Expanded(child: Text(l10n.varianceShortLabel, style: const TextStyle(fontWeight: FontWeight.bold), textAlign: TextAlign.right)),
              ],
            ),
          ),
          const Divider(height: 1),
          ...stages.map(
            (stage) => Padding(
              padding: const EdgeInsets.all(8),
              child: Row(
                children: [
                  Expanded(flex: 2, child: Text(stage.stageDisplayName)),
                  Expanded(child: Text(stage.estimatedAmount ?? l10n.notAvailableLabel, textAlign: TextAlign.right)),
                  Expanded(child: Text(stage.actualAmount ?? l10n.notAvailableLabel, textAlign: TextAlign.right)),
                  Expanded(child: Text(stage.variance ?? l10n.notAvailableLabel, textAlign: TextAlign.right)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
