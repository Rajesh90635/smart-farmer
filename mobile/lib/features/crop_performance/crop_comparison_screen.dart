import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_performance_models.dart';
import 'crop_performance_repository.dart';

/// Comparison verdicts are read directly from the backend - this screen
/// never claims one crop is "better" when the underlying comparison is
/// 'insufficient_data' or 'not_directly_comparable'.
class CropComparisonScreen extends StatefulWidget {
  final String cropCycleId;
  const CropComparisonScreen({super.key, required this.cropCycleId});

  @override
  State<CropComparisonScreen> createState() => _CropComparisonScreenState();
}

class _CropComparisonScreenState extends State<CropComparisonScreen> {
  final TextEditingController _otherIdController = TextEditingController();
  CropComparison? _comparison;
  bool _loading = false;
  String? _error;

  Future<void> _compare() async {
    final otherId = _otherIdController.text.trim();
    if (otherId.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final comparison = await context.read<CropPerformanceRepository>().compareCropCycles(widget.cropCycleId, otherId);
      if (!mounted) return;
      setState(() {
        _comparison = comparison;
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

  String _verdictLabel(AppLocalizations l10n, String comparison) {
    switch (comparison) {
      case 'a_higher':
        return l10n.cropComparisonVerdictAHigher;
      case 'b_higher':
        return l10n.cropComparisonVerdictBHigher;
      case 'equal':
        return l10n.cropComparisonVerdictEqual;
      case 'not_directly_comparable':
        return l10n.cropComparisonVerdictNotComparable;
      default:
        return l10n.insufficientDataLabel;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.cropComparisonTitle)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _otherIdController,
                    decoration: InputDecoration(labelText: l10n.otherCropCycleIdLabel, border: const OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(onPressed: _compare, child: Text(l10n.compareButton)),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(child: _buildBody(l10n)),
          ],
        ),
      ),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!));
    if (_comparison == null) return Center(child: Text(l10n.cropComparisonEmptyMessage));

    return ListView(
      children: _comparison!.metrics
          .map((m) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(m.metricName.replaceAll('_', ' '), style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(l10n.cropComparisonMetricRow(m.valueA ?? l10n.notAvailableLabel, m.valueB ?? l10n.notAvailableLabel)),
                      const SizedBox(height: 4),
                      Text(_verdictLabel(l10n, m.comparison), style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 12)),
                    ],
                  ),
                ),
              ))
          .toList(),
    );
  }
}
