import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_financial_models.dart';
import 'crop_financial_repository.dart';

/// Every figure here is read directly from the backend's own
/// CropProfitForecast - "actual", "committed", and "potential" revenue
/// are kept visually and structurally distinct, never merged into one
/// ambiguous number. Any nullable field is rendered as an explicit
/// "Not available" label, and dataCompletenessNotes are always shown so
/// the farmer understands exactly why a figure might be missing.
class ProfitForecastScreen extends StatefulWidget {
  final String cropCycleId;
  const ProfitForecastScreen({super.key, required this.cropCycleId});

  @override
  State<ProfitForecastScreen> createState() => _ProfitForecastScreenState();
}

class _ProfitForecastScreenState extends State<ProfitForecastScreen> {
  CropProfitForecast? _forecast;
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
      final forecast = await context.read<CropFinancialRepository>().getProfitForecast(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _forecast = forecast;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.profitForecastTitle)),
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

    final f = _forecast!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildCostProjectionCard(f, l10n),
        const SizedBox(height: 16),
        _buildRevenueProjectionCard(f, l10n),
        const SizedBox(height: 16),
        _buildProfitProjectionCard(f, l10n),
        if (f.dataCompletenessNotes.isNotEmpty) ...[
          const SizedBox(height: 16),
          _buildNotesCard(f, l10n),
        ],
      ],
    );
  }

  Widget _buildCostProjectionCard(CropProfitForecast f, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.costProjectionLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _row(l10n.actualCostSoFarLabel, f.actualCost, l10n),
            _row(l10n.remainingEstimatedCostLabel, f.remainingEstimatedCost, l10n),
            const Divider(),
            _row(l10n.projectedTotalCostLabel, f.projectedTotalCost, l10n, bold: true),
          ],
        ),
      ),
    );
  }

  Widget _buildRevenueProjectionCard(CropProfitForecast f, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.revenueProjectionLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _row(l10n.actualRevenueReceivedLabel, f.actualRevenue, l10n),
            _row(l10n.committedRevenueLabel, f.committedRevenue, l10n),
            _row(l10n.potentialAdditionalRevenueLabel, f.potentialAdditionalRevenue, l10n),
            if (f.potentialAdditionalRevenueBasis != null)
              Padding(
                padding: const EdgeInsets.only(top: 2, bottom: 4),
                child: Text(f.potentialAdditionalRevenueBasis!, style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ),
            const Divider(),
            _row(l10n.projectedTotalRevenueLabel, f.projectedTotalRevenue, l10n, bold: true),
            if (f.revenueProjectionIsPartial)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(l10n.partialRevenueProjectionHint, style: const TextStyle(fontSize: 12, color: Colors.orange, fontStyle: FontStyle.italic)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfitProjectionCard(CropProfitForecast f, AppLocalizations l10n) {
    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.projectedProfitLossLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _row(l10n.projectedProfitLossLabel, f.projectedProfitLoss, l10n, bold: true, highlightSign: true),
            _row(l10n.projectedProfitLossPercentLabel, f.projectedProfitLossPercent, l10n),
          ],
        ),
      ),
    );
  }

  Widget _buildNotesCard(CropProfitForecast f, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.info_outline, size: 18, color: Colors.grey),
                const SizedBox(width: 6),
                Text(l10n.whatsMissingLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            ...f.dataCompletenessNotes.map(
              (note) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text('• $note', style: const TextStyle(fontSize: 13)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String? value, AppLocalizations l10n, {bool bold = false, bool highlightSign = false}) {
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
              fontWeight: bold ? FontWeight.bold : FontWeight.normal,
              color: value == null ? Colors.grey : (isNegative ? Colors.red : (isPositive ? Colors.green : null)),
              fontStyle: value == null ? FontStyle.italic : FontStyle.normal,
            ),
          ),
        ],
      ),
    );
  }
}
