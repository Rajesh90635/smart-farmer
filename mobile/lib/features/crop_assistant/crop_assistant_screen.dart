import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_assistant_models.dart';
import 'crop_assistant_repository.dart';

/// The answer text shown here is exactly what the backend returned -
/// this screen never edits, upgrades, or reinterprets it. contextUsed
/// and limitations are always shown as clearly separate sections from
/// the answer itself.
class CropAssistantScreen extends StatefulWidget {
  final String cropCycleId;
  const CropAssistantScreen({super.key, required this.cropCycleId});

  @override
  State<CropAssistantScreen> createState() => _CropAssistantScreenState();
}

class _CropAssistantScreenState extends State<CropAssistantScreen> {
  final TextEditingController _questionController = TextEditingController();
  CropAssistantResponse? _response;
  bool _loading = false;
  String? _error;

  List<String> _suggestedQuestions(AppLocalizations l10n) => [
        l10n.assistantSuggestionCropStatus,
        l10n.assistantSuggestionDisease,
        l10n.assistantSuggestionTreatment,
        l10n.assistantSuggestionFinancial,
      ];

  Future<void> _ask(String question) async {
    if (question.trim().isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await context.read<CropAssistantRepository>().askQuestion(widget.cropCycleId, question.trim());
      if (!mounted) return;
      setState(() {
        _response = response;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.cropAssistantTitle)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.askAboutYourCropLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            if (_response == null && !_loading) _buildSuggestedQuestions(l10n),
            Expanded(
              child: SingleChildScrollView(
                child: _loading
                    ? const Padding(padding: EdgeInsets.only(top: 40), child: Center(child: CircularProgressIndicator()))
                    : _error != null
                        ? Padding(padding: const EdgeInsets.only(top: 20), child: Text(_error!))
                        : _response != null
                            ? _buildAnswer(_response!, l10n)
                            : const SizedBox.shrink(),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _questionController,
                    decoration: InputDecoration(hintText: l10n.typeYourQuestionHint, border: const OutlineInputBorder()),
                    onSubmitted: _ask,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(icon: const Icon(Icons.send), onPressed: () => _ask(_questionController.text)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestedQuestions(AppLocalizations l10n) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _suggestedQuestions(l10n)
          .map((q) => ActionChip(label: Text(q), onPressed: () {
                _questionController.text = q;
                _ask(q);
              }))
          .toList(),
    );
  }

  Widget _buildAnswer(CropAssistantResponse response, AppLocalizations l10n) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Text(response.answer),
          ),
        ),
        if (response.contextUsed.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(l10n.basedOnYourCropRecordsLabel, style: const TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic)),
          Text(response.contextUsed.join(', '), style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
        if (response.limitations.isNotEmpty) ...[
          const SizedBox(height: 8),
          Card(
            color: Colors.orange.shade50,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: response.limitations.map((l) => Text('• $l', style: const TextStyle(fontSize: 12))).toList(),
              ),
            ),
          ),
        ],
      ],
    );
  }
}
