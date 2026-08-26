import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'crop_repository.dart';
import 'farm_models.dart';

/// Add Crop: farmer selects farm (implicit - already on this plot),
/// selects plot (implicit - passed in), selects crop via searchable list
/// (never free-text), enters sowing date, expected harvest date, and
/// starting status is always PLANNED (farmer advances it later from Crop
/// Details) - matches CultivationStatus starting state on the backend.
class AddCropScreen extends StatefulWidget {
  final String plotId;
  const AddCropScreen({super.key, required this.plotId});

  @override
  State<AddCropScreen> createState() => _AddCropScreenState();
}

class _AddCropScreenState extends State<AddCropScreen> {
  CropMaster? _selectedCrop;
  DateTime? _sowingDate;
  DateTime? _expectedHarvestDate;
  String? _season;
  bool _saving = false;

  List<CropVariety> _varieties = [];
  CropVariety? _selectedVariety;
  bool _loadingVarieties = false;

  static const _seasons = ['kharif', 'rabi', 'zaid', 'perennial', 'other'];

  Future<void> _pickCrop() async {
    final selected = await showModalBottomSheet<CropMaster>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _CropSearchSheet(cropRepository: context.read<CropRepository>()),
    );
    if (selected == null) return;
    setState(() {
      _selectedCrop = selected;
      _varieties = [];
      _selectedVariety = null;
    });
    await _loadVarieties(selected.id);
  }

  Future<void> _loadVarieties(String cropId) async {
    setState(() => _loadingVarieties = true);
    try {
      final varieties = await context.read<CropRepository>().listVarietiesForCrop(cropId);
      if (!mounted) return;
      setState(() {
        _varieties = varieties;
        _loadingVarieties = false;
      });
    } catch (_) {
      // Variety data is optional context, not required to add a crop -
      // fail silently into an empty list rather than blocking the form.
      if (!mounted) return;
      setState(() => _loadingVarieties = false);
    }
  }

  Future<void> _pickDate({required bool isSowing}) async {
    final initial = isSowing ? (_sowingDate ?? DateTime.now()) : (_expectedHarvestDate ?? DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked == null) return;
    setState(() {
      if (isSowing) {
        _sowingDate = picked;
      } else {
        _expectedHarvestDate = picked;
      }
    });
  }

  bool get _canSave => _selectedCrop != null && _sowingDate != null;

  Future<void> _save() async {
    if (!_canSave) return;
    setState(() => _saving = true);
    try {
      await context.read<CropRepository>().createCropCycle(
            widget.plotId,
            cropId: _selectedCrop!.id,
            season: _season,
            sowingDate: _isoDate(_sowingDate!),
            expectedHarvestDate: _expectedHarvestDate != null ? _isoDate(_expectedHarvestDate!) : null,
            varietyId: _selectedVariety?.id,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Crop added.')));
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Crop')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            ListTile(
              tileColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              title: Text(_selectedCrop?.name ?? 'Select a crop'),
              trailing: const Icon(Icons.search),
              onTap: _pickCrop,
            ),
            const SizedBox(height: 16),
            ListTile(
              tileColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              title: Text(_sowingDate == null ? 'Sowing date' : _isoDate(_sowingDate!)),
              trailing: const Icon(Icons.calendar_today),
              onTap: () => _pickDate(isSowing: true),
            ),
            const SizedBox(height: 16),
            ListTile(
              tileColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              title: Text(_expectedHarvestDate == null ? 'Expected harvest date (optional)' : _isoDate(_expectedHarvestDate!)),
              trailing: const Icon(Icons.calendar_today),
              onTap: () => _pickDate(isSowing: false),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _season,
              decoration: const InputDecoration(labelText: 'Season (optional)'),
              items: _seasons.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (v) => setState(() => _season = v),
            ),
            if (_loadingVarieties) ...[
              const SizedBox(height: 16),
              const Center(child: CircularProgressIndicator()),
            ] else if (_varieties.isNotEmpty) ...[
              const SizedBox(height: 16),
              DropdownButtonFormField<CropVariety>(
                value: _selectedVariety,
                decoration: const InputDecoration(labelText: 'Variety (optional)'),
                items: _varieties
                    .map((v) => DropdownMenuItem(
                          value: v,
                          child: Text(v.typicalDurationDays != null ? '${v.name} (~${v.typicalDurationDays}d)' : v.name),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => _selectedVariety = v),
              ),
            ],
            const SizedBox(height: 32),
            if (_saving)
              const Center(child: CircularProgressIndicator())
            else
              ElevatedButton(onPressed: _canSave ? _save : null, child: const Text('Add crop')),
          ],
        ),
      ),
    );
  }
}

class _CropSearchSheet extends StatefulWidget {
  final CropRepository cropRepository;
  const _CropSearchSheet({required this.cropRepository});

  @override
  State<_CropSearchSheet> createState() => _CropSearchSheetState();
}

class _CropSearchSheetState extends State<_CropSearchSheet> {
  final _controller = TextEditingController();
  List<CropMaster> _results = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _search('');
  }

  Future<void> _search(String query) async {
    setState(() => _loading = true);
    try {
      final results = await widget.cropRepository.searchCropMaster(query);
      setState(() {
        _results = results;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _controller,
                decoration: const InputDecoration(labelText: 'Search crop', prefixIcon: Icon(Icons.search)),
                onChanged: _search,
              ),
            ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView.builder(
                      itemCount: _results.length,
                      itemBuilder: (context, index) {
                        final crop = _results[index];
                        return ListTile(
                          title: Text(crop.name),
                          subtitle: crop.category != null ? Text(crop.category!) : null,
                          onTap: () => Navigator.of(context).pop(crop),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
