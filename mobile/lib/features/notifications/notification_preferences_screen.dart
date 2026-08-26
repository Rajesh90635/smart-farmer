import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'notification_models.dart';
import 'notification_repository.dart';

/// Toggles only - quiet_hours_start/end exist on the backend but have no
/// editor here yet (disclosed scope trim, not silently dropped): the
/// backend's `time` type needs a dedicated time-range picker this pass
/// didn't build. Every toggle reflects the backend's own current value,
/// never a client-side default guess.
class NotificationPreferencesScreen extends StatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  State<NotificationPreferencesScreen> createState() => _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState extends State<NotificationPreferencesScreen> {
  NotificationPreferences? _preferences;
  bool _loading = true;
  bool _saving = false;
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
      final preferences = await context.read<NotificationRepository>().getPreferences();
      if (!mounted) return;
      setState(() {
        _preferences = preferences;
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

  Future<void> _toggle(String field, bool value) async {
    setState(() => _saving = true);
    try {
      final repository = context.read<NotificationRepository>();
      final updated = await repository.updatePreferences(
        weatherAlertsEnabled: field == 'weather' ? value : null,
        rainAlertsEnabled: field == 'rain' ? value : null,
        cropAlertsEnabled: field == 'crop' ? value : null,
        diseaseAlertsEnabled: field == 'disease' ? value : null,
        audioAlertsEnabled: field == 'audio' ? value : null,
        generalNotificationsEnabled: field == 'general' ? value : null,
      );
      if (!mounted) return;
      setState(() {
        _preferences = updated;
        _saving = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notification Preferences')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: const Text('Try again'))],
        ),
      );
    }

    final preferences = _preferences!;
    return ListView(
      children: [
        SwitchListTile(
          title: const Text('Weather alerts'),
          value: preferences.weatherAlertsEnabled,
          onChanged: _saving ? null : (v) => _toggle('weather', v),
        ),
        SwitchListTile(
          title: const Text('Rain alerts'),
          value: preferences.rainAlertsEnabled,
          onChanged: _saving ? null : (v) => _toggle('rain', v),
        ),
        SwitchListTile(
          title: const Text('Crop alerts'),
          value: preferences.cropAlertsEnabled,
          onChanged: _saving ? null : (v) => _toggle('crop', v),
        ),
        SwitchListTile(
          title: const Text('Disease alerts'),
          value: preferences.diseaseAlertsEnabled,
          onChanged: _saving ? null : (v) => _toggle('disease', v),
        ),
        SwitchListTile(
          title: const Text('Audio alerts'),
          subtitle: const Text('Off by default - opt in to have alerts read aloud'),
          value: preferences.audioAlertsEnabled,
          onChanged: _saving ? null : (v) => _toggle('audio', v),
        ),
        SwitchListTile(
          title: const Text('General notifications'),
          value: preferences.generalNotificationsEnabled,
          onChanged: _saving ? null : (v) => _toggle('general', v),
        ),
      ],
    );
  }
}
