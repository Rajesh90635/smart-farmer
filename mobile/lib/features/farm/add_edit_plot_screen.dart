import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'farm_models.dart';
import 'plot_repository.dart';

class AddEditPlotScreen extends StatefulWidget {
  final String farmId;
  final Plot? existingPlot;
  const AddEditPlotScreen({super.key, required this.farmId, this.existingPlot});

  @override
  State<AddEditPlotScreen> createState() => _AddEditPlotScreenState();
}

class _AddEditPlotScreenState extends State<AddEditPlotScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _areaController;
  late final TextEditingController _irrigationController;
  String _areaUnit = 'acre';
  bool _saving = false;

  static const _areaUnits = ['acre', 'hectare', 'gunta', 'cent', 'square_meter'];

  bool get _isEditing => widget.existingPlot != null;

  @override
  void initState() {
    super.initState();
    final plot = widget.existingPlot;
    _nameController = TextEditingController(text: plot?.plotName ?? '');
    _areaController = TextEditingController(text: plot?.areaValue.toString() ?? '');
    _irrigationController = TextEditingController(text: plot?.irrigationType ?? '');
    if (plot != null) _areaUnit = plot.areaUnit;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _areaController.dispose();
    _irrigationController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final repo = context.read<PlotRepository>();
    try {
      final areaValue = double.parse(_areaController.text.trim());
      final irrigation = _irrigationController.text.trim().isEmpty ? null : _irrigationController.text.trim();

      if (_isEditing) {
        await repo.updatePlot(widget.existingPlot!.id, plotName: _nameController.text.trim(), areaValue: areaValue, areaUnit: _areaUnit);
      } else {
        await repo.createPlot(
          widget.farmId,
          plotName: _nameController.text.trim(),
          areaValue: areaValue,
          areaUnit: _areaUnit,
          irrigationType: irrigation,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_isEditing ? 'Plot updated.' : 'Plot added.')));
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
      appBar: AppBar(title: Text(_isEditing ? 'Edit Plot' : 'Add Plot')),
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
                  decoration: const InputDecoration(labelText: 'Plot name'),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Please enter a plot name.' : null,
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
                        items: _areaUnits.map((u) => DropdownMenuItem(value: u, child: Text(u.replaceAll('_', ' ')))).toList(),
                        onChanged: (v) => setState(() => _areaUnit = v ?? _areaUnit),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _irrigationController,
                  decoration: const InputDecoration(labelText: 'Irrigation (optional)'),
                ),
                const SizedBox(height: 32),
                if (_saving)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: _save, child: Text(_isEditing ? 'Save changes' : 'Add plot')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
