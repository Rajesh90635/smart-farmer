import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../crop_assistant/crop_assistant_screen.dart';
import '../crop_financial/crop_financial_summary_screen.dart';
import '../crop_financial/profit_forecast_screen.dart';
import '../crop_performance/crop_comparison_screen.dart';
import '../crop_performance/input_roi_screen.dart';
import '../crop_performance/irrigation_intelligence_screen.dart';
import '../crop_performance/performance_score_screen.dart';
import '../crop_photo/crop_photo_list_screen.dart';
import '../crop_risk/risk_score_screen.dart';
import '../harvest/harvest_list_screen.dart';
import '../health_timeline/health_timeline_screen.dart';
import '../ledger/ledger_screen.dart';
import '../personalization/advisory_feedback_screen.dart';
import '../personalization/learning_summary_screen.dart';
import '../personalization/personalization_profile_screen.dart';
import '../task/task_list_screen.dart';
import '../treatment/treatment_list_screen.dart';
import '../weather_action/weather_action_screen.dart';
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
  String? _varietyName;

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
      final repository = context.read<CropRepository>();
      final cycle = await repository.getCropCycle(widget.cropCycleId);
      setState(() {
        _cycle = cycle;
        _loading = false;
      });
      if (cycle.varietyId != null) await _loadVarietyName(repository, cycle.crop.id, cycle.varietyId!);
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
  }

  /// CropCycleResponse only carries variety_id, not the variety's name - so
  /// the name is resolved from the same crop-scoped variety list the add
  /// form already uses. Best-effort: an unresolved name just means the
  /// "Variety" row is omitted, never a fabricated label.
  Future<void> _loadVarietyName(CropRepository repository, String cropId, String varietyId) async {
    try {
      final varieties = await repository.listVarietiesForCrop(cropId);
      final match = varieties.where((v) => v.id == varietyId).toList();
      if (!mounted || match.isEmpty) return;
      setState(() => _varietyName = match.first.name);
    } catch (_) {
      // Best-effort only - see method doc.
    }
  }

  Future<void> _advanceStatus(String newStatus, AppLocalizations l10n) async {
    setState(() => _updating = true);
    try {
      final updated = await context.read<CropRepository>().updateCropCycleStatus(widget.cropCycleId, newStatus);
      setState(() => _cycle = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }

  Future<void> _closeHarvest(AppLocalizations l10n) async {
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
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.cropDetailsMarkedHarvestedMessage)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }

  Future<void> _cancelCropCycle(AppLocalizations l10n) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(l10n.cropDetailsCancelConfirmTitle),
        content: Text(l10n.cropDetailsCancelConfirmMessage),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(l10n.cropDetailsCancelConfirmNoButton)),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: Text(l10n.cropDetailsCancelConfirmYesButton)),
        ],
      ),
    );
    if (confirmed == true) _advanceStatus('cancelled', l10n);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(_cycle?.crop.name ?? l10n.cropDetailsFallbackTitle),
        actions: [
          if (_cycle != null)
            PopupMenuButton<String>(
              tooltip: l10n.cropDetailsInsightsTooltip,
              icon: const Icon(Icons.insights_outlined),
              onSelected: (value) {
                final cycleId = _cycle!.id;
                switch (value) {
                  case 'performance':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => PerformanceScoreScreen(cropCycleId: cycleId)));
                    break;
                  case 'comparison':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => CropComparisonScreen(cropCycleId: cycleId)));
                    break;
                  case 'input_roi':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => InputRoiScreen(cropCycleId: cycleId)));
                    break;
                  case 'irrigation':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => IrrigationIntelligenceScreen(cropCycleId: cycleId)));
                    break;
                  case 'personalization':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const PersonalizationProfileScreen()));
                    break;
                  case 'learning_summary':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => LearningSummaryScreen(cropCycleId: cycleId)));
                    break;
                  case 'feedback':
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => AdvisoryFeedbackScreen(cropCycleId: cycleId)));
                    break;
                }
              },
              itemBuilder: (context) => [
                PopupMenuItem(value: 'performance', child: Text(l10n.cropDetailsPerformanceScoreMenuItem)),
                PopupMenuItem(value: 'comparison', child: Text(l10n.cropDetailsCompareCropsMenuItem)),
                PopupMenuItem(value: 'input_roi', child: Text(l10n.cropDetailsInputSpendBreakdownMenuItem)),
                PopupMenuItem(value: 'irrigation', child: Text(l10n.cropDetailsIrrigationIntelligenceMenuItem)),
                PopupMenuItem(value: 'personalization', child: Text(l10n.cropDetailsPersonalizationProfileMenuItem)),
                PopupMenuItem(value: 'learning_summary', child: Text(l10n.cropDetailsLearningSummaryMenuItem)),
                PopupMenuItem(value: 'feedback', child: Text(l10n.cropDetailsGiveFeedbackMenuItem)),
              ],
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.cloudy_snowing),
              tooltip: l10n.cropDetailsWeatherActionTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => WeatherActionScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.chat_outlined),
              tooltip: l10n.cropDetailsAiAssistantTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CropAssistantScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.history),
              tooltip: l10n.cropDetailsHealthTimelineTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => HealthTimelineScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.medical_services_outlined),
              tooltip: l10n.cropDetailsTreatmentsTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => TreatmentListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.health_and_safety_outlined),
              tooltip: l10n.cropDetailsCropRiskTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => RiskScoreScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.trending_up),
              tooltip: l10n.cropDetailsProfitForecastTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => ProfitForecastScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.assessment_outlined),
              tooltip: l10n.cropDetailsFinancialSummaryTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CropFinancialSummaryScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.account_balance_wallet_outlined),
              tooltip: l10n.cropDetailsFinancialLedgerTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => LedgerScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.checklist),
              tooltip: l10n.cropDetailsTasksTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => TaskListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.camera_alt),
              tooltip: l10n.cropDetailsCheckCropTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CropPhotoListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
          if (_cycle != null)
            IconButton(
              icon: const Icon(Icons.agriculture),
              tooltip: l10n.cropDetailsHarvestTooltip,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => HarvestListScreen(cropCycleId: _cycle!.id)),
              ),
            ),
        ],
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
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))],
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
        ListTile(title: Text(l10n.cropDetailsSowingDateLabel), subtitle: Text(cycle.sowingDate)),
        if (cycle.expectedHarvestDate != null)
          ListTile(title: Text(l10n.cropDetailsExpectedHarvestLabel), subtitle: Text(cycle.expectedHarvestDate!)),
        if (cycle.actualHarvestDate != null)
          ListTile(title: Text(l10n.cropDetailsHarvestedOnLabel), subtitle: Text(cycle.actualHarvestDate!)),
        if (cycle.season != null) ListTile(title: Text(l10n.cropDetailsSeasonLabel), subtitle: Text(cycle.season!)),
        if (_varietyName != null) ListTile(title: Text(l10n.cropDetailsVarietyLabel), subtitle: Text(_varietyName!)),
        if (cycle.seedVariety != null) ListTile(title: Text(l10n.cropDetailsSeedVarietyLabel), subtitle: Text(cycle.seedVariety!)),
        const SizedBox(height: 32),
        if (_updating)
          const Center(child: CircularProgressIndicator())
        else if (!isTerminal) ...[
          if (cycle.cultivationStatus == 'ready_for_harvest')
            ElevatedButton.icon(
              onPressed: () => _closeHarvest(l10n),
              icon: const Icon(Icons.agriculture),
              label: Text(l10n.cropDetailsMarkAsHarvestedButton),
            )
          else if (next != null)
            ElevatedButton(
              onPressed: () => _advanceStatus(next, l10n),
              child: Text(l10n.cropDetailsAdvanceToButton(next.replaceAll('_', ' '))),
            ),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: () => _cancelCropCycle(l10n), child: Text(l10n.cropDetailsCancelCropButton)),
        ],
      ],
    );
  }
}
