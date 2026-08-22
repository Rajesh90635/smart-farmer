import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'personalization_repository.dart';

/// mlTrainingJustified is always false in this system - this screen
/// always shows the readiness note prominently, never presents the
/// feature snapshot as if it were a real prediction.
class LearningSummaryScreen extends StatefulWidget {
  final String cropCycleId;
  const LearningSummaryScreen({super.key, required this.cropCycleId});

  @override
  State<LearningSummaryScreen> createState() => _LearningSummaryScreenState();
}

class _LearningSummaryScreenState extends State<LearningSummaryScreen> {
  dynamic _summary;
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
      final summary = await context.read<PersonalizationRepository>().getLearningSummary(widget.cropCycleId);
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Learning Summary')),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(children: [const SizedBox(height: 80), Center(child: Text(_error!))]);
    }

    final summary = _summary;
    final snapshot = summary.featureSnapshot;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: Colors.orange.shade50,
          child: Padding(padding: const EdgeInsets.all(12), child: Text(summary.mlReadinessNote, style: const TextStyle(fontSize: 12))),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Feature version: ${snapshot.featureVersion}', style: const TextStyle(fontSize: 12)),
                const SizedBox(height: 8),
                const Text('Available data', style: TextStyle(fontWeight: FontWeight.bold)),
                ...snapshot.availableAtTime.entries.map((e) => Text('${e.key}: ${e.value}', style: const TextStyle(fontSize: 12))),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Outcome', style: TextStyle(fontWeight: FontWeight.bold)),
                Text(
                  snapshot.outcomeLabel != null
                      ? snapshot.outcomeLabel.entries.map((e) => '${e.key}: ${e.value}').join(', ')
                      : 'Not available yet - this crop has not reached a completed harvest outcome.',
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
