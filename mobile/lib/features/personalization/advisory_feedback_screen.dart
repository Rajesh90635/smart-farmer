import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
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

  Future<void> _submit(String feedbackType) async {
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
        _message = 'Thank you for your feedback.';
        _submitting = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _message = FriendlyError.from(e);
        _submitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Give Feedback')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Which feature is this feedback about?', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButton<String>(
              isExpanded: true,
              value: _sourceType,
              items: _sourceTypes.map((t) => DropdownMenuItem(value: t, child: Text(t.replaceAll('_', ' ')))).toList(),
              onChanged: (value) => setState(() => _sourceType = value ?? _sourceType),
            ),
            const SizedBox(height: 24),
            if (_submitting) const Center(child: CircularProgressIndicator()),
            if (!_submitting) ...[
              ElevatedButton(onPressed: () => _submit('helpful'), child: const Text('Helpful')),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('not_helpful'), child: const Text('Not Helpful')),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('wrong'), child: const Text('Wrong')),
              const SizedBox(height: 8),
              ElevatedButton(onPressed: () => _submit('need_expert'), child: const Text('Need Expert')),
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
