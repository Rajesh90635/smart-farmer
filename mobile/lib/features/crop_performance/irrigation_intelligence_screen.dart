import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'crop_performance_repository.dart';

/// soilMoistureAvailable is ALWAYS false in this system - this screen
/// always shows that disclosure prominently, never hides it.
class IrrigationIntelligenceScreen extends StatefulWidget {
  final String cropCycleId;
  const IrrigationIntelligenceScreen({super.key, required this.cropCycleId});

  @override
  State<IrrigationIntelligenceScreen> createState() => _IrrigationIntelligenceScreenState();
}

class _IrrigationIntelligenceScreenState extends State<IrrigationIntelligenceScreen> {
  dynamic _intelligence;
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
      final intelligence = await context.read<CropPerformanceRepository>().getIrrigationIntelligence(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _intelligence = intelligence;
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

  Color _colorFor(String recommendation) {
    switch (recommendation) {
      case 'irrigate_now':
        return Colors.blue;
      case 'delay':
        return Colors.red;
      case 'monitor':
        return Colors.orange;
      case 'no_action':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String _label(String recommendation) {
    switch (recommendation) {
      case 'irrigate_now':
        return 'IRRIGATE NOW';
      case 'delay':
        return 'DELAY';
      case 'monitor':
        return 'MONITOR';
      case 'no_action':
        return 'NO ACTION NEEDED';
      default:
        return 'UNKNOWN';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Irrigation Intelligence')),
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

    final intelligence = _intelligence;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: _colorFor(intelligence.recommendation).withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _label(intelligence.recommendation),
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: _colorFor(intelligence.recommendation)),
                ),
                const SizedBox(height: 8),
                Text(intelligence.reason),
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
                Text('Weather signal: ${intelligence.weatherStatus}'),
                if (intelligence.pendingIrrigationTaskId != null) const Text('A pending irrigation task exists for this crop.'),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          color: Colors.grey.shade100,
          child: const Padding(
            padding: EdgeInsets.all(12),
            child: Text(
              'Soil moisture data is unavailable. This recommendation is based on weather forecast and task status only.',
              style: TextStyle(fontSize: 12),
            ),
          ),
        ),
      ],
    );
  }
}
