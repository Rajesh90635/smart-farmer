import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../weather/weather_screen.dart';
import 'add_edit_farm_screen.dart';
import 'add_edit_plot_screen.dart';
import 'farm_models.dart';
import 'farm_repository.dart';
import 'plot_details_screen.dart';
import 'plot_repository.dart';

class FarmDetailsScreen extends StatefulWidget {
  final String farmId;
  const FarmDetailsScreen({super.key, required this.farmId});

  @override
  State<FarmDetailsScreen> createState() => _FarmDetailsScreenState();
}

class _FarmDetailsScreenState extends State<FarmDetailsScreen> {
  Farm? _farm;
  List<Plot> _plots = [];
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
      final farm = await context.read<FarmRepository>().getFarm(widget.farmId);
      final plots = await context.read<PlotRepository>().listPlotsForFarm(widget.farmId);
      setState(() {
        _farm = farm;
        _plots = plots;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  Future<void> _deactivateFarm(AppLocalizations l10n) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(l10n.farmDetailsRemoveConfirmTitle),
        content: Text(l10n.farmDetailsRemoveConfirmMessage),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(l10n.farmDetailsRemoveConfirmCancelButton)),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: Text(l10n.farmDetailsRemoveConfirmRemoveButton)),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await context.read<FarmRepository>().deactivateFarm(widget.farmId);
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(_farm?.farmName ?? l10n.farmDetailsFallbackTitle),
        actions: [
          if (_farm != null)
            IconButton(
              icon: const Icon(Icons.wb_cloudy_outlined),
              tooltip: l10n.farmDetailsWeatherTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => WeatherScreen(farmId: _farm!.id)),
              ),
            ),
          if (_farm != null)
            PopupMenuButton<String>(
              onSelected: (value) async {
                if (value == 'edit') {
                  final updated = await Navigator.of(context).push<bool>(
                    MaterialPageRoute(builder: (_) => AddEditFarmScreen(existingFarm: _farm)),
                  );
                  if (updated == true) _load();
                } else if (value == 'deactivate') {
                  _deactivateFarm(l10n);
                }
              },
              itemBuilder: (_) => [
                PopupMenuItem(value: 'edit', child: Text(l10n.farmDetailsEditFarmMenuItem)),
                PopupMenuItem(value: 'deactivate', child: Text(l10n.farmDetailsRemoveFarmMenuItem)),
              ],
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => AddEditPlotScreen(farmId: widget.farmId)),
          );
          if (created == true) _load();
        },
        icon: const Icon(Icons.add),
        label: Text(l10n.farmDetailsAddPlotButton),
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: const Text('Try again'))],
        ),
      );
    }

    final farm = _farm!;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        children: [
          ListTile(
            title: Text(l10n.farmDetailsTotalAreaLabel),
            subtitle: Text('${farm.areaValue} ${farm.areaUnit}'),
          ),
          if (farm.description != null && farm.description!.isNotEmpty)
            ListTile(title: Text(l10n.farmDetailsNotesLabel), subtitle: Text(farm.description!)),
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(l10n.farmDetailsPlotsSectionLabel, style: Theme.of(context).textTheme.titleMedium),
          ),
          if (_plots.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(l10n.farmDetailsNoPlotsYetMessage),
            )
          else
            ..._plots.map(
              (plot) => ListTile(
                leading: const Icon(Icons.crop_square),
                title: Text(plot.plotName, style: const TextStyle(fontSize: 18)),
                subtitle: Text('${plot.areaValue} ${plot.areaUnit}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => PlotDetailsScreen(plotId: plot.id)),
                  );
                  _load();
                },
              ),
            ),
        ],
      ),
    );
  }
}
