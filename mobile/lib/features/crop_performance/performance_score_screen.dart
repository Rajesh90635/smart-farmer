import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_performance_models.dart';
import 'crop_performance_repository.dart';

/// Every component score shown here is read directly from the backend -
/// this screen never fills a missing component with a guessed value; a
/// null score is always rendered as "Not available", never hidden.
class PerformanceScoreScreen extends StatefulWidget {
  final String cropCycleId;
  const PerformanceScoreScreen({super.key, required this.cropCycleId});

  @override
  State<PerformanceScoreScreen> createState() => _PerformanceScoreScreenState();
}

class _PerformanceScoreScreenState extends State<PerformanceScoreScreen> {
  PerformanceScore? _score;
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
      final score = await context.read<CropPerformanceRepository>().getPerformanceScore(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _score = score;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.cropPerformanceTitle)),
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

    final score = _score!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: Colors.blue.shade50,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.performanceOverallScoreLabel, style: const TextStyle(fontSize: 14, color: Colors.grey)),
                const SizedBox(height: 4),
                Text(
                  score.insufficientData ? l10n.insufficientDataLabel : '${score.overallScore}/100',
                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(l10n.performanceDataCompletenessLabel(score.dataCompletenessPercent),
                    style: const TextStyle(fontSize: 12, color: Colors.grey)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        ...score.components.map((c) => _buildComponentCard(l10n, c)),
      ],
    );
  }

  Widget _buildComponentCard(AppLocalizations l10n, PerformanceComponent component) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: Text(component.name.replaceAll('_', ' '), style: const TextStyle(fontWeight: FontWeight.bold))),
                Text(
                  component.score != null ? '${component.score}' : l10n.notAvailableLabel,
                  style: TextStyle(color: component.score == null ? Colors.grey : null),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(component.explanation, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
