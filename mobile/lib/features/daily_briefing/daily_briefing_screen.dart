import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/voice_language_controller.dart';
import '../../core/voice_service.dart';
import '../../l10n/app_localizations.dart';
import 'daily_briefing_models.dart';
import 'daily_briefing_repository.dart';

/// Today's Briefing: every line comes verbatim from the backend's
/// GET /assistant/daily-summary (already real, tool-composed data). This
/// screen adds NO content of its own - not even the "No new updates"
/// fallback text, which is itself backend-provided (the honest empty
/// state is the backend's own line, not a Flutter-side placeholder
/// standing in for missing data).
class DailyBriefingScreen extends StatefulWidget {
  const DailyBriefingScreen({super.key});

  @override
  State<DailyBriefingScreen> createState() => _DailyBriefingScreenState();
}

class _DailyBriefingScreenState extends State<DailyBriefingScreen> {
  DailyBriefing? _briefing;
  bool _loading = true;
  String? _error;
  bool _voiceUnavailableMessageShown = false;

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
      final briefing = await context.read<DailyBriefingRepository>().getDailyBriefing();
      if (!mounted) return;
      setState(() {
        _briefing = briefing;
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

  /// Speaks EXACTLY the lines already on screen (DailyBriefing.audioText
  /// is just those same lines joined) - never a separately-generated
  /// voice summary, so screen and audio can never disagree. This is the
  /// ONE screen where "location" audio-language mode also re-fetches the
  /// CONTENT itself in the detected language (via the backend's
  /// `language_code` override), not just the voice locale - every other
  /// voice call site in the app can only switch locale, since it has no
  /// way to re-render its own already-backend-composed or already-l10n
  /// text in a different language on demand.
  Future<void> _speak() async {
    final initialBriefing = _briefing;
    if (initialBriefing == null) return;
    var current = initialBriefing;

    final voiceLanguageController = context.read<VoiceLanguageController>();
    if (voiceLanguageController.mode == VoiceLanguageMode.location) {
      final detected = await voiceLanguageController.resolveLanguageCode(contentLanguageCode: current.languageCode);
      if (!mounted) return;
      if (detected != current.languageCode) {
        try {
          final relocalized = await context.read<DailyBriefingRepository>().getDailyBriefing(languageCodeOverride: detected);
          if (!mounted) return;
          setState(() => _briefing = relocalized);
          current = relocalized;
        } catch (_) {
          // Best-effort only - if the re-fetch fails (offline, backend
          // error), fall through and speak the already-loaded briefing
          // in its existing language rather than blocking Listen entirely.
        }
      }
    }

    final voice = context.read<VoiceService>();
    final started = await voice.speak(current.audioText, languageCode: current.languageCode);
    if (!mounted) return;
    setState(() => _voiceUnavailableMessageShown = !started);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.dailyBriefingTitle)),
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

    final briefing = _briefing!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final line in briefing.lines)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(line, style: const TextStyle(fontSize: 16)),
            ),
          ),
        const SizedBox(height: 16),
        OutlinedButton.icon(onPressed: _speak, icon: const Icon(Icons.volume_up), label: Text(l10n.listenButton)),
        if (_voiceUnavailableMessageShown)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(l10n.voiceUnavailable, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ),
      ],
    );
  }
}
