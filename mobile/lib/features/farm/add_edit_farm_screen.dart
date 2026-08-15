import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'farm_models.dart';
import 'farm_repository.dart';

/// Add or edit a farm. Location capture uses the device's raw GPS
/// coordinates entered/confirmed by the farmer - no paid map SDK. A real
/// "Use Current Location" button (device geolocation) is not wired in
/// this phase since that requires a location-plugin dependency decision
/// not yet made; manual lat/lng entry is the fallback the spec explicitly
/// allows ("if map integration is not yet available, allow manual...
/// coordinate capture").
class AddEditFarmScreen extends StatefulWidget {
  final Farm? existingFarm;
  const AddEditFarmScreen({super.key, this.existingFarm});

  @override
  State<AddEditFarmScreen> createState() => _AddEditFarmScreenState();
}

class _AddEditFarmScreenState extends State<AddEditFarmScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _areaController;
  late final TextEditingController _latController;
  late final TextEditingController _lngController;
  String _areaUnit = 'acre';
  bool _saving = false;

  static const _areaUnits = ['acre', 'hectare', 'gunta', 'cent', 'square_meter'];

  bool get _isEditing => widget.existingFarm != null;

  @override
  void initState() {
    super.initState();
    final farm = widget.existingFarm;
    _nameController = TextEditingController(text: farm?.farmName ?? '');
    _areaController = TextEditingController(text: farm?.areaValue.toString() ?? '');
    _latController = TextEditingController(text: farm?.latitude?.toString() ?? '');
    _lngController = TextEditingController(text: farm?.longitude?.toString() ?? '');
    if (farm != null) _areaUnit = farm.areaUnit;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _areaController.dispose();
    _latController.dispose();
    _lngController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final repo = context.read<FarmRepository>();
    try {
      final areaValue = double.parse(_areaController.text.trim());
      final lat = _latController.text.trim().isEmpty ? null : double.parse(_latController.text.trim());
      final lng = _lngController.text.trim().isEmpty ? null : double.parse(_lngController.text.trim());

      if (_isEditing) {
        await repo.updateFarm(
          widget.existingFarm!.id,
          farmName: _nameController.text.trim(),
          areaValue: areaValue,
          areaUnit: _areaUnit,
        );
      } else {
        await repo.createFarm(
          farmName: _nameController.text.trim(),
          areaValue: areaValue,
          areaUnit: _areaUnit,
          latitude: lat,
          longitude: lng,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_isEditing ? 'Farm updated.' : 'Farm added.')),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? 'Edit Farm' : 'Add Farm')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: 'Farm name'),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Please enter a farm name.' : null,
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextFormField(
                        controller: _areaController,
                        decoration: const InputDecoration(labelText: 'Area'),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        validator: (v) {
                          final value = double.tryParse(v?.trim() ?? '');
                          if (value == null || value <= 0) return 'Enter a valid area.';
                          return null;
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _areaUnit,
                        decoration: const InputDecoration(labelText: 'Unit'),
                        items: _areaUnits
                            .map((u) => DropdownMenuItem(value: u, child: Text(u.replaceAll('_', ' '))))
                            .toList(),
                        onChanged: (v) => setState(() => _areaUnit = v ?? _areaUnit),
                      ),
                    ),
                  ],
                ),
                if (!_isEditing) ...[
                  const SizedBox(height: 24),
                  const Text('Location (optional)', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _latController,
                          decoration: const InputDecoration(labelText: 'Latitude'),
                          keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextFormField(
                          controller: _lngController,
                          decoration: const InputDecoration(labelText: 'Longitude'),
                          keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                        ),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 32),
                if (_saving)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: _save, child: Text(_isEditing ? 'Save changes' : 'Add farm')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
