import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'treatment_models.dart';
import 'treatment_repository.dart';

/// Every effectiveness result shown here is read directly from the
/// backend's own deterministic comparison - this screen never derives
/// "improved"/"worsened" from farmer notes or presents an uncertain
/// result as a confirmed success. 'insufficient_evidence' is always
/// rendered distinctly from a real outcome, never hidden or upgraded.
class TreatmentListScreen extends StatefulWidget {
  final String cropCycleId;
  const TreatmentListScreen({super.key, required this.cropCycleId});

  @override
  State<TreatmentListScreen> createState() => _TreatmentListScreenState();
}

class _TreatmentListScreenState extends State<TreatmentListScreen> {
  List<TreatmentRecord> _treatments = [];
  final Map<String, TreatmentEffectiveness> _effectiveness = {};
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
      final repo = context.read<TreatmentRepository>();
      final treatments = await repo.listTreatments(widget.cropCycleId);
      final effectivenessResults = <String, TreatmentEffectiveness>{};
      for (final t in treatments) {
        effectivenessResults[t.id] = await repo.getEffectiveness(t.id);
      }
      if (!mounted) return;
      setState(() {
        _treatments = treatments;
        _effectiveness
          ..clear()
          ..addAll(effectivenessResults);
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

  Future<void> _showAddTreatmentSheet(AppLocalizations l10n) async {
    DateTime selectedDate = DateTime.now();
    final notesController = TextEditingController();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.recordTreatmentTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: sheetContext,
                    initialDate: selectedDate,
                    firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) setSheetState(() => selectedDate = picked);
                },
                child: Text(selectedDate.toIso8601String().split('T').first),
              ),
              const SizedBox(height: 12),
              TextField(controller: notesController, decoration: InputDecoration(labelText: l10n.notesOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<TreatmentRepository>().createTreatment(
                          cropCycleId: widget.cropCycleId,
                          applicationDate: selectedDate.toIso8601String().split('T').first,
                          notes: notesController.text.trim().isEmpty ? null : notesController.text.trim(),
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                  }
                },
                child: Text(l10n.saveTreatmentButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showAddFollowUpSheet(TreatmentRecord treatment, AppLocalizations l10n) async {
    DateTime selectedDate = DateTime.now();
    final notesController = TextEditingController();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.recordFollowUpTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 4),
              Text(l10n.recordFollowUpHint, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: sheetContext,
                    initialDate: selectedDate,
                    firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) setSheetState(() => selectedDate = picked);
                },
                child: Text(selectedDate.toIso8601String().split('T').first),
              ),
              const SizedBox(height: 12),
              TextField(controller: notesController, decoration: InputDecoration(labelText: l10n.notesOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<TreatmentRepository>().createFollowUp(
                          treatmentId: treatment.id,
                          observationDate: selectedDate.toIso8601String().split('T').first,
                          notes: notesController.text.trim().isEmpty ? null : notesController.text.trim(),
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                  }
                },
                child: Text(l10n.saveFollowUpButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _colorFor(String result) {
    switch (result) {
      case 'improved':
        return Colors.green;
      case 'worsened':
        return Colors.red;
      case 'no_significant_change':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _labelFor(String result, AppLocalizations l10n) {
    switch (result) {
      case 'improved':
        return l10n.effectivenessImprovedLabel;
      case 'worsened':
        return l10n.effectivenessWorsenedLabel;
      case 'no_significant_change':
        return l10n.effectivenessNoChangeLabel;
      default:
        return l10n.effectivenessInsufficientEvidenceLabel;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.treatmentsTitle)),
      floatingActionButton: FloatingActionButton(onPressed: () => _showAddTreatmentSheet(l10n), child: const Icon(Icons.add)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(child: Text(_error!)),
          const SizedBox(height: 12),
          Center(child: ElevatedButton(onPressed: _load, child: const Text('Try again'))),
        ],
      );
    }
    if (_treatments.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noTreatmentsYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _treatments.map((t) => _buildTreatmentCard(t, l10n)).toList(),
    );
  }

  Widget _buildTreatmentCard(TreatmentRecord treatment, AppLocalizations l10n) {
    final effectiveness = _effectiveness[treatment.id];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text('${l10n.appliedOnLabel}: ${treatment.applicationDate}', style: const TextStyle(fontWeight: FontWeight.bold))),
              ],
            ),
            if (treatment.notes != null) Text(treatment.notes!, style: const TextStyle(fontSize: 13)),
            const SizedBox(height: 8),
            if (effectiveness != null) ...[
              Row(
                children: [
                  Container(width: 10, height: 10, decoration: BoxDecoration(color: _colorFor(effectiveness.result), shape: BoxShape.circle)),
                  const SizedBox(width: 8),
                  Text(_labelFor(effectiveness.result, l10n), style: TextStyle(color: _colorFor(effectiveness.result), fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 4),
              Text(effectiveness.basis, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => _showAddFollowUpSheet(treatment, l10n),
              icon: const Icon(Icons.camera_alt, size: 16),
              label: Text(l10n.recordFollowUpButton),
            ),
          ],
        ),
      ),
    );
  }
}
