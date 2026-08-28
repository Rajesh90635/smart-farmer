import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_performance_models.dart';
import 'crop_performance_repository.dart';

/// The limitation note is always shown prominently - this screen never
/// renders an roiPercent (it's always null) as if a real ROI figure
/// existed.
class InputRoiScreen extends StatefulWidget {
  final String cropCycleId;
  const InputRoiScreen({super.key, required this.cropCycleId});

  @override
  State<InputRoiScreen> createState() => _InputRoiScreenState();
}

class _InputRoiScreenState extends State<InputRoiScreen> {
  InputRoi? _roi;
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
      final roi = await context.read<CropPerformanceRepository>().getInputRoi(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _roi = roi;
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
      appBar: AppBar(title: Text(l10n.inputRoiTitle)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(children: [const SizedBox(height: 80), Center(child: Text(_error!))]);
    }

    final roi = _roi!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: Colors.orange.shade50,
          child: Padding(padding: const EdgeInsets.all(12), child: Text(roi.limitationNote, style: const TextStyle(fontSize: 12))),
        ),
        const SizedBox(height: 12),
        Text(l10n.inputRoiTotalActualCostLabel(roi.totalActualCost), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 12),
        if (roi.categories.isEmpty) Text(l10n.inputRoiNoExpensesMessage),
        ...roi.categories.map((c) => _buildCategoryCard(l10n, c)),
      ],
    );
  }

  Widget _buildCategoryCard(AppLocalizations l10n, InputCategoryBreakdown category) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(category.category, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text('${category.percentOfTotalCost}%'),
              ],
            ),
            Text(l10n.inputRoiActualLabel(category.actualCost)),
            if (category.estimatedCost != null)
              Text(l10n.inputRoiEstimatedVarianceLabel(category.estimatedCost!, category.variance!)),
          ],
        ),
      ),
    );
  }
}
