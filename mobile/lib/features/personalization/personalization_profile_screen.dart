import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'personalization_models.dart';
import 'personalization_repository.dart';

/// Every preference shown here is read directly from the backend - this
/// screen never states a preference when confidence is null (insufficient
/// evidence); it always shows the real evidence count and explanation
/// instead, never hiding the "not enough data yet" state.
class PersonalizationProfileScreen extends StatefulWidget {
  const PersonalizationProfileScreen({super.key});

  @override
  State<PersonalizationProfileScreen> createState() => _PersonalizationProfileScreenState();
}

class _PersonalizationProfileScreenState extends State<PersonalizationProfileScreen> {
  PersonalizationProfile? _profile;
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
      final profile = await context.read<PersonalizationRepository>().getProfile();
      if (!mounted) return;
      setState(() {
        _profile = profile;
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

  Color _colorForConfidence(String? confidence) {
    switch (confidence) {
      case 'high':
        return Colors.green;
      case 'medium':
        return Colors.blue;
      case 'low':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _friendlySignalName(String name) => name.replaceAll('_', ' ');

  String _confidenceLabel(String confidence, AppLocalizations l10n) {
    switch (confidence) {
      case 'high':
        return l10n.personalizationConfidenceHighLabel;
      case 'medium':
        return l10n.personalizationConfidenceMediumLabel;
      case 'low':
        return l10n.personalizationConfidenceLowLabel;
      default:
        return confidence.toUpperCase();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.personalizationProfileTitle)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(children: [const SizedBox(height: 80), Center(child: Text(_error!))]);
    }

    final profile = _profile!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: profile.preferences.map((preference) => _buildPreferenceCard(preference, l10n)).toList(),
    );
  }

  Widget _buildPreferenceCard(LearnedPreference preference, AppLocalizations l10n) {
    final hasEvidence = preference.confidence != null;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: Text(_friendlySignalName(preference.signalName), style: const TextStyle(fontWeight: FontWeight.bold))),
                if (hasEvidence)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: _colorForConfidence(preference.confidence).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _confidenceLabel(preference.confidence!, l10n),
                      style: TextStyle(color: _colorForConfidence(preference.confidence), fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              preference.observation ?? l10n.personalizationProfileNoDataMessage,
              style: TextStyle(fontStyle: hasEvidence ? FontStyle.normal : FontStyle.italic, color: hasEvidence ? null : Colors.grey),
            ),
            const SizedBox(height: 4),
            Text(preference.explanation, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
