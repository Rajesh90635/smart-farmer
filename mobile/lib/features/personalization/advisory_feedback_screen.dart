import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'personalization_repository.dart';

/// Only submits feedback actions actually supported by the backend
/// (helpful/not_helpful/wrong/need_expert) - no decorative UI beyond
/// what the API accepts.
class AdvisoryFeedbackScreen extends StatefulWidget {
  final String cropCycleId;
  const AdvisoryFeedbackScreen({super.key, required this.cropCycleId});

  @override
  State<AdvisoryFeedbackScreen> createState() => _AdvisoryFeedbackScreenState();
}

class _AdvisoryFeedbackScreenState extends State<AdvisoryFeedbackScreen> {
  String _sourceType = 'crop_assistant';
  bool _submitting = false;
  String? _message;

  static const _sourceTypes = ['crop_assistant', 'risk_score', 'weather_action', 'irrigation_intelligence', 'treatment_recommendation'];

  String _sourceTypeLabel(String sourceType, AppLocalizations l10n) {
    switch (sourceType) {
      case 'crop_assistant':
        return l10n.advisorySourceCropAssistantLabel;
      case 'risk_score':
        return l10n.advisorySourceRiskScoreLabel;
      case 'weather_action':
        return l10n.advisorySourceWeatherActionLabel;
      case 'irrigation_intelligence':
        return l10n.advisorySourceIrrigationIntelligenceLabel;
      case 'treatment_recommendation':
        return l10n.advisorySourceTreatmentRecommendationLabel;
      default:
        return sourceType.replaceAll('_', ' ');
    }
  }

  Future<void> _submit(String feedbackType, AppLocalizations l10n) async {
    setState(() {
      _submitting = true;
      _message = null;
    });
    try {
      await context.read<PersonalizationRepository>().submitFeedback(
            cropCycleId: widget.cropCycleId,
            sourceType: _sourceType,
            feedbackType: feedbackType,
          );
      if (!mounted) return;
      setState(() {
        _message = l10n.advisoryFeedbackThanksMessage;
        _submitting = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _message = FriendlyError.from(e, AppLocalizations.of(context)!);
        _submitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.advisoryFeedbackTitle)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.advisoryFeedbackSourcePrompt, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButton<String>(
              isExpanded: true,
              value: _sourceType,
              items: _sourceTypes.map((t) => DropdownMenuItem(value: t, child: Text(_sourceTypeLabel(t, l10n)))).toList(),
              onChanged: (value) => setState(() => _sourceType = value ?? _sourceType),
            ),
            const SizedBox(height: 24),
            if (_submitting) const Center(child: CircularProgressIndicator()),
            if (!_submitting) ...[
              ElevatedButton(onPressed: () => _submit('helpful', l10n), child: Text(l10n.advisoryFeedbackHelpfulButton)),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('not_helpful', l10n), child: Text(l10n.advisoryFeedbackNotHelpfulButton)),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('wrong', l10n), child: Text(l10n.advisoryFeedbackWrongButton)),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('need_expert', l10n), child: Text(l10n.advisoryFeedbackNeedExpertButton)),
            ],
            if (_message != null) ...[
              const SizedBox(height: 16),
              Text(_message!, textAlign: TextAlign.center),
            ],
          ],
        ),
      ),
    );
  }
}
