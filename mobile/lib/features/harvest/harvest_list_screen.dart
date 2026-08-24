import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'harvest_models.dart';
import 'harvest_repository.dart';

/// Records and tracks harvests for one crop cycle, against the existing
/// backend/app/api/v1/harvests.py contract - no new backend behavior.
/// Status/quantity/delivery-option values are always the backend's own
/// raw strings; nothing here recomputes a harvest's state independently.
class HarvestListScreen extends StatefulWidget {
  final String cropCycleId;
  const HarvestListScreen({super.key, required this.cropCycleId});

  @override
  State<HarvestListScreen> createState() => _HarvestListScreenState();
}

class _HarvestListScreenState extends State<HarvestListScreen> {
  List<HarvestRecord> _harvests = [];
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
      final harvests = await context.read<HarvestRepository>().listHarvestsForCropCycle(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _harvests = harvests;
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

  Future<void> _startHarvest() async {
    try {
      final repo = context.read<HarvestRepository>();
      if (_harvests.isEmpty) {
        await repo.getOrCreateHarvestForCropCycle(widget.cropCycleId);
      } else {
        await repo.createNewHarvestForCropCycle(widget.cropCycleId);
      }
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _markApproaching(HarvestRecord harvest) async {
    try {
      await context.read<HarvestRepository>().markApproaching(harvest.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _showConfirmReadySheet(HarvestRecord harvest, AppLocalizations l10n) async {
    DateTime? selectedDate;
    final quantityController = TextEditingController();

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
              Text(l10n.confirmReadyTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: sheetContext,
                    initialDate: DateTime.now(),
                    firstDate: DateTime.now().subtract(const Duration(days: 365)),
                    lastDate: DateTime.now().add(const Duration(days: 30)),
                  );
                  if (picked != null) setSheetState(() => selectedDate = picked);
                },
                child: Text(selectedDate == null ? l10n.actualHarvestDateOptionalLabel : selectedDate!.toIso8601String().split('T').first),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: quantityController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: l10n.estimatedQuantityOptionalLabel),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  final quantity = quantityController.text.trim();
                  try {
                    await context.read<HarvestRepository>().confirmReady(
                          harvestId: harvest.id,
                          actualHarvestDate: selectedDate?.toIso8601String().split('T').first,
                          estimatedQuantity: quantity.isEmpty ? null : quantity,
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                  }
                },
                child: Text(l10n.confirmReadyButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  static const _deliveryOptions = ['buyer_collection', 'farmer_delivery', 'third_party_logistics'];

  String _deliveryOptionLabel(String value, AppLocalizations l10n) {
    switch (value) {
      case 'farmer_delivery':
        return l10n.deliveryOptionFarmerDeliveryLabel;
      case 'third_party_logistics':
        return l10n.deliveryOptionThirdPartyLogisticsLabel;
      default:
        return l10n.deliveryOptionBuyerCollectionLabel;
    }
  }

  Future<void> _showCreateListingSheet(HarvestRecord harvest, AppLocalizations l10n, {bool confirmDuplicate = false}) async {
    final quantityController = TextEditingController(text: harvest.estimatedQuantity ?? harvest.actualQuantity ?? '');
    final unitController = TextEditingController(text: harvest.unit);
    final qualityController = TextEditingController(text: harvest.qualityGrade ?? '');
    final priceController = TextEditingController();
    final stateController = TextEditingController();
    final districtController = TextEditingController();
    final notesController = TextEditingController();
    String selectedDeliveryOption = _deliveryOptions.first;

    Future<void> submit() async {
      final serviceArea = <String, dynamic>{};
      if (stateController.text.trim().isNotEmpty) serviceArea['state'] = stateController.text.trim();
      if (districtController.text.trim().isNotEmpty) serviceArea['district'] = districtController.text.trim();

      try {
        await context.read<HarvestRepository>().createListing(
              harvestId: harvest.id,
              quantityAvailable: quantityController.text.trim(),
              unit: unitController.text.trim(),
              deliveryOption: selectedDeliveryOption,
              qualityGrade: qualityController.text.trim().isEmpty ? null : qualityController.text.trim(),
              serviceArea: serviceArea.isEmpty ? null : serviceArea,
              preferredPrice: priceController.text.trim().isEmpty ? null : priceController.text.trim(),
              notes: notesController.text.trim().isEmpty ? null : notesController.text.trim(),
              confirmDuplicate: confirmDuplicate,
            );
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.listingCreatedMessage)));
        await _load();
      } catch (e) {
        if (!mounted) return;
        if (e is ApiException && e.code == 'DUPLICATE_LISTING_WARNING' && !confirmDuplicate) {
          final createAnyway = await showDialog<bool>(
            context: context,
            builder: (dialogContext) => AlertDialog(
              title: Text(l10n.duplicateListingTitle),
              content: Text(l10n.duplicateListingMessage),
              actions: [
                TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
                TextButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: Text(l10n.createAnotherListingButton)),
              ],
            ),
          );
          if (createAnyway == true) {
            await _showCreateListingSheet(harvest, l10n, confirmDuplicate: true);
          }
          return;
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
      }
    }

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(l10n.createListingTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                const SizedBox(height: 12),
                TextField(
                  controller: quantityController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(labelText: l10n.quantityAvailableLabel),
                ),
                const SizedBox(height: 12),
                TextField(controller: unitController, decoration: InputDecoration(labelText: l10n.harvestUnitLabel)),
                const SizedBox(height: 12),
                TextField(controller: qualityController, decoration: InputDecoration(labelText: l10n.qualityGradeOptionalLabel)),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedDeliveryOption,
                  items: _deliveryOptions
                      .map((o) => DropdownMenuItem(value: o, child: Text(_deliveryOptionLabel(o, l10n))))
                      .toList(),
                  onChanged: (v) => setSheetState(() => selectedDeliveryOption = v ?? _deliveryOptions.first),
                  decoration: InputDecoration(labelText: l10n.deliveryOptionLabel),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: priceController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(labelText: l10n.preferredPriceOptionalLabel),
                ),
                const SizedBox(height: 12),
                TextField(controller: stateController, decoration: InputDecoration(labelText: l10n.serviceAreaStateOptionalLabel)),
                const SizedBox(height: 12),
                TextField(controller: districtController, decoration: InputDecoration(labelText: l10n.serviceAreaDistrictOptionalLabel)),
                const SizedBox(height: 12),
                TextField(controller: notesController, decoration: InputDecoration(labelText: l10n.listingNotesOptionalLabel)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () async {
                    Navigator.of(sheetContext).pop();
                    await submit();
                  },
                  child: Text(l10n.createListingButton),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'approaching':
        return Colors.orange;
      case 'ready':
        return Colors.blue;
      case 'harvested':
        return Colors.teal;
      case 'listed':
        return Colors.purple;
      case 'partially_sold':
        return Colors.amber;
      case 'sold':
        return Colors.green;
      case 'cancelled':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _statusLabel(String status, AppLocalizations l10n) {
    switch (status) {
      case 'approaching':
        return l10n.harvestStatusApproachingLabel;
      case 'ready':
        return l10n.harvestStatusReadyLabel;
      case 'harvested':
        return l10n.harvestStatusHarvestedLabel;
      case 'listed':
        return l10n.harvestStatusListedLabel;
      case 'partially_sold':
        return l10n.harvestStatusPartiallySoldLabel;
      case 'sold':
        return l10n.harvestStatusSoldLabel;
      case 'cancelled':
        return l10n.harvestStatusCancelledLabel;
      default:
        return l10n.harvestStatusPlannedLabel;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.harvestsTitle)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _startHarvest,
        icon: const Icon(Icons.add),
        label: Text(_harvests.isEmpty ? l10n.recordHarvestButton : l10n.startAdditionalHarvestButton),
      ),
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
    if (_harvests.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noHarvestsYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _harvests.map((h) => _buildHarvestCard(h, l10n)).toList(),
    );
  }

  Widget _buildHarvestCard(HarvestRecord harvest, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(width: 10, height: 10, decoration: BoxDecoration(color: _statusColor(harvest.status), shape: BoxShape.circle)),
                const SizedBox(width: 8),
                Text(_statusLabel(harvest.status, l10n), style: TextStyle(color: _statusColor(harvest.status), fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            if (harvest.estimatedQuantity != null) Text('${l10n.estimatedQuantityOptionalLabel}: ${harvest.estimatedQuantity} ${harvest.unit}'),
            if (harvest.actualQuantity != null) Text('${l10n.quantityAvailableLabel}: ${harvest.actualQuantity} ${harvest.unit}'),
            if (harvest.qualityGrade != null) Text('${l10n.qualityGradeOptionalLabel}: ${harvest.qualityGrade}'),
            if (harvest.expectedHarvestDate != null) Text('${l10n.actualHarvestDateOptionalLabel}: ${harvest.expectedHarvestDate}'),
            if (harvest.actualHarvestDate != null) Text(harvest.actualHarvestDate!),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (harvest.status == 'planned')
                  OutlinedButton(onPressed: () => _markApproaching(harvest), child: Text(l10n.markApproachingButton)),
                if (harvest.status == 'planned' || harvest.status == 'approaching')
                  OutlinedButton(onPressed: () => _showConfirmReadySheet(harvest, l10n), child: Text(l10n.confirmReadyButton)),
                if (harvest.status == 'ready')
                  OutlinedButton(onPressed: () => _showCreateListingSheet(harvest, l10n), child: Text(l10n.createListingButton)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
