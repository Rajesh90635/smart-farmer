import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
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
        _error = FriendlyError.from(e);
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your Personalization Profile')),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(children: [const SizedBox(height: 80), Center(child: Text(_error!))]);
    }

    final profile = _profile!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: profile.preferences.map(_buildPreferenceCard).toList(),
    );
  }

  Widget _buildPreferenceCard(LearnedPreference preference) {
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
                      preference.confidence!.toUpperCase(),
                      style: TextStyle(color: _colorForConfidence(preference.confidence), fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              preference.observation ?? 'Not enough data yet to identify a pattern.',
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
