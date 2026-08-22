import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
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
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  String _verdictLabel(String comparison) {
    switch (comparison) {
      case 'a_higher':
        return 'This crop — higher (based on available data)';
      case 'b_higher':
        return 'Other crop — higher (based on available data)';
      case 'equal':
        return 'Equal';
      case 'not_directly_comparable':
        return 'Not directly comparable';
      default:
        return 'Insufficient data';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Compare Crops')),
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
                    decoration: const InputDecoration(labelText: 'Other crop cycle ID', border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(onPressed: _compare, child: const Text('Compare')),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!));
    if (_comparison == null) return const Center(child: Text('Enter another crop cycle ID to compare.'));

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
                      Text('This crop: ${m.valueA ?? 'Not available'}    Other crop: ${m.valueB ?? 'Not available'}'),
                      const SizedBox(height: 4),
                      Text(_verdictLabel(m.comparison), style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 12)),
                    ],
                  ),
                ),
              ))
          .toList(),
    );
  }
}
