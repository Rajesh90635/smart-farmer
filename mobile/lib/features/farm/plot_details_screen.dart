import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'add_crop_screen.dart';
import 'crop_details_screen.dart';
import 'crop_repository.dart';
import 'farm_models.dart';
import 'plot_repository.dart';

class PlotDetailsScreen extends StatefulWidget {
  final String plotId;
  const PlotDetailsScreen({super.key, required this.plotId});

  @override
  State<PlotDetailsScreen> createState() => _PlotDetailsScreenState();
}

class _PlotDetailsScreenState extends State<PlotDetailsScreen> {
  Plot? _plot;
  List<CropCycle> _cycles = [];
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
      final plot = await context.read<PlotRepository>().getPlot(widget.plotId);
      final cycles = await context.read<CropRepository>().listCropCyclesForPlot(widget.plotId);
      setState(() {
        _plot = plot;
        _cycles = cycles;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_plot?.plotName ?? 'Plot')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => AddCropScreen(plotId: widget.plotId)),
          );
          if (created == true) _load();
        },
        icon: const Icon(Icons.add),
        label: const Text('Add Crop'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: const Text('Try again'))],
        ),
      );
    }

    final plot = _plot!;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        children: [
          ListTile(title: const Text('Area'), subtitle: Text('${plot.areaValue} ${plot.areaUnit}')),
          if (plot.soilType != null) ListTile(title: const Text('Soil'), subtitle: Text(plot.soilType!)),
          if (plot.irrigationType != null) ListTile(title: const Text('Irrigation'), subtitle: Text(plot.irrigationType!)),
          const Divider(),
          Padding(padding: const EdgeInsets.all(16), child: Text('Crops', style: Theme.of(context).textTheme.titleMedium)),
          if (_cycles.isEmpty)
            const Padding(padding: EdgeInsets.all(16), child: Text('No crops yet. Tap "Add Crop" to start one.'))
          else
            ..._cycles.map(
              (cycle) => ListTile(
                leading: const Icon(Icons.eco),
                title: Text(cycle.crop.name, style: const TextStyle(fontSize: 18)),
                subtitle: Text('${_statusLabel(cycle.cultivationStatus)} · sown ${cycle.sowingDate}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => CropDetailsScreen(cropCycleId: cycle.id)),
                  );
                  _load();
                },
              ),
            ),
        ],
      ),
    );
  }

  String _statusLabel(String status) => status.replaceAll('_', ' ');
}
