import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../crop_photo/crop_photo_list_screen.dart';
import '../task/task_list_screen.dart';
import 'crop_repository.dart';
import 'farm_models.dart';

/// Crop Details: shows the cultivation status and lets the farmer advance
/// it one step at a time (never an arbitrary jump - only the single "next"
/// status per cultivationStatusOrder is offered as a button), plus a
/// separate Cancel action and a Close/Harvest action once
/// ready_for_harvest is reached. The backend is still the actual
/// enforcement point - this UI just avoids offering an invalid choice in
/// the first place.
class CropDetailsScreen extends StatefulWidget {
  final String cropCycleId;
  const CropDetailsScreen({super.key, required this.cropCycleId});

  @override
  State<CropDetailsScreen> createState() => _CropDetailsScreenState();
}

class _CropDetailsScreenState extends State<CropDetailsScreen> {
  CropCycle? _cycle;
  bool _loading = true;
  bool _updating = false;
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
      final cycle = await context.read<CropRepository>().getCropCycle(widget.cropCycleId);
      setState(() {
        _cycle = cycle;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  Future<void> _advanceStatus(String newStatus) async {
    setState(() => _updating = true);
    try {
      final updated = await context.read<CropRepository>().updateCropCycleStatus(widget.cropCycleId, newStatus);
      setState(() => _cycle = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }

  Future<void> _closeHarvest() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked == null) return;

    final isoDate =
        '${picked.year.toString().padLeft(4, '0')}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';

    setState(() => _updating = true);
    try {
      final updated = await context.read<CropRepository>().closeCropCycle(widget.cropCycleId, isoDate);
      setState(() => _cycle = updated);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Crop marked as harvested.')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }

  Future<void> _cancelCropCycle() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Cancel this crop?'),
        content: const Text('This marks the crop cycle as cancelled. This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('No')),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Yes, cancel')),
        ],
      ),
    );
    if (confirmed == true) _advanceStatus('cancelled');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_cycle?.crop.name ?? 'Crop'),
        actions: [
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.checklist),
              tooltip: 'Tasks',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => TaskListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.camera_alt),
              tooltip: 'Check Crop',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CropPhotoListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
        ],
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

    final cycle = _cycle!;
    final next = nextStatusAfter(cycle.cultivationStatus);
    final isTerminal = cycle.cultivationStatus == 'harvested' || cycle.cultivationStatus == 'cancelled';

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Center(
          child: Chip(
            label: Text(cycle.cultivationStatus.replaceAll('_', ' ').toUpperCase()),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
        ),
        const SizedBox(height: 24),
        ListTile(title: const Text('Sowing date'), subtitle: Text(cycle.sowingDate)),
        if (cycle.expectedHarvestDate != null)
          ListTile(title: const Text('Expected harvest'), subtitle: Text(cycle.expectedHarvestDate!)),
        if (cycle.actualHarvestDate != null)
          ListTile(title: const Text('Harvested on'), subtitle: Text(cycle.actualHarvestDate!)),
        if (cycle.season != null) ListTile(title: const Text('Season'), subtitle: Text(cycle.season!)),
        if (cycle.seedVariety != null) ListTile(title: const Text('Seed variety'), subtitle: Text(cycle.seedVariety!)),
        const SizedBox(height: 32),
        if (_updating)
          const Center(child: CircularProgressIndicator())
        else if (!isTerminal) ...[
          if (cycle.cultivationStatus == 'ready_for_harvest')
            ElevatedButton.icon(
              onPressed: _closeHarvest,
              icon: const Icon(Icons.agriculture),
              label: const Text('Mark as harvested'),
            )
          else if (next != null)
            ElevatedButton(
              onPressed: () => _advanceStatus(next),
              child: Text('Advance to ${next.replaceAll('_', ' ')}'),
            ),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: _cancelCropCycle, child: const Text('Cancel this crop')),
        ],
      ],
    );
  }
}
