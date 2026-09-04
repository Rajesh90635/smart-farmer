import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'weather_action_models.dart';
import 'weather_action_repository.dart';

/// Every status shown here is read directly from the backend's
/// deterministic classification - this screen never renders a confident
/// recommendation when the backend status is 'unknown'. Evidence values
/// are shown exactly as returned, never recalculated or reworded into a
/// percentage that wasn't there.
class WeatherActionScreen extends StatefulWidget {
  final String cropCycleId;
  const WeatherActionScreen({super.key, required this.cropCycleId});

  @override
  State<WeatherActionScreen> createState() => _WeatherActionScreenState();
}

class _WeatherActionScreenState extends State<WeatherActionScreen> {
  CropWeatherAction? _action;
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
      final action = await context.read<WeatherActionRepository>().getWeatherActions(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _action = action;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
  }

  Color _colorFor(String status) {
    switch (status) {
      case 'safe':
        return Colors.green;
      case 'caution':
        return Colors.orange;
      case 'unsafe':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _iconFor(String actionType) {
    switch (actionType) {
      case 'spray':
        return Icons.water_drop_outlined;
      case 'irrigation':
        return Icons.grass_outlined;
      case 'harvest':
        return Icons.agriculture_outlined;
      default:
        return Icons.circle_outlined;
    }
  }

  String _statusLabel(String status, AppLocalizations l10n) {
    switch (status) {
      case 'safe':
        return l10n.weatherActionSafeLabel;
      case 'caution':
        return l10n.weatherActionCautionLabel;
      case 'unsafe':
        return l10n.weatherActionUnsafeLabel;
      default:
        return l10n.weatherActionUnknownLabel;
    }
  }

  String _actionTypeLabel(String actionType, AppLocalizations l10n) {
    switch (actionType) {
      case 'spray':
        return l10n.weatherActionSprayLabel;
      case 'irrigation':
        return l10n.weatherActionIrrigationLabel;
      case 'harvest':
        return l10n.weatherActionHarvestLabel;
      default:
        return actionType;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.weatherActionAdvisorTitle)),
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
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
        ],
      );
    }

    final action = _action!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (!action.weatherAvailable)
          Card(
            color: Colors.grey.shade100,
            child: Padding(padding: const EdgeInsets.all(16), child: Text(l10n.weatherDataInsufficientMessage)),
          ),
        if (action.isStale)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(l10n.weatherStaleWarning, style: const TextStyle(color: Colors.orange, fontSize: 12)),
          ),
        ...action.assessments.map((a) => _buildAssessmentCard(a, l10n)),
        if (action.recommendedSprayWindow != null) ...[
          const SizedBox(height: 8),
          _buildWindowCard(action.recommendedSprayWindow!, l10n),
        ],
        if (action.dataCompletenessNotes.isNotEmpty) ...[
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: action.dataCompletenessNotes.map((n) => Text('• $n', style: const TextStyle(fontSize: 12))).toList(),
              ),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildAssessmentCard(ActionAssessment assessment, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_iconFor(assessment.actionType), color: _colorFor(assessment.status)),
                const SizedBox(width: 8),
                Expanded(child: Text(_actionTypeLabel(assessment.actionType, l10n), style: const TextStyle(fontWeight: FontWeight.bold))),
                Text(_statusLabel(assessment.status, l10n), style: TextStyle(color: _colorFor(assessment.status), fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 6),
            Text(assessment.reason),
            if (assessment.evidence.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                assessment.evidence.entries.map((e) => '${e.key}: ${e.value}').join(' · '),
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildWindowCard(WindowSuggestion window, AppLocalizations l10n) {
    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.recommendedSprayWindowLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(window.forecastDate),
            Text(window.reason, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
