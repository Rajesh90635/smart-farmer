import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/voice_service.dart';
import '../../l10n/app_localizations.dart';
import '../farm/farm_repository.dart';
import 'weather_models.dart';

/// Every field on screen is read directly from FarmWeather - this screen
/// never computes, guesses, or supplements a weather value. Loading,
/// unavailable, and stale states are all distinct and honestly labeled -
/// never silently blank or fabricated.
class WeatherScreen extends StatefulWidget {
  final String farmId;
  const WeatherScreen({super.key, required this.farmId});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  FarmWeather? _weather;
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
      final weather = await context.read<FarmRepository>().getWeather(widget.farmId);
      if (!mounted) return;
      setState(() {
        _weather = weather;
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

  String _lookupCropActionMessage(AppLocalizations l10n, String messageKey) {
    switch (messageKey) {
      case 'sprayConditionWarning':
        return l10n.sprayConditionWarning;
      default:
        return messageKey;
    }
  }

  Future<void> _speak(AppLocalizations l10n) async {
    final weather = _weather;
    if (weather == null || !weather.available) return;

    final parts = <String>[];
    if (weather.current?.temperatureC != null) {
      parts.add('${weather.current!.temperatureC!.round()} degrees Celsius.');
    }
    if (weather.current?.rainProbabilityPercent != null) {
      parts.add('${weather.current!.rainProbabilityPercent!.round()} percent chance of rain.');
    }
    final advisory = weather.cropAction;
    if (advisory != null) {
      final key = cropActionMessageKeys[advisory.reasonMessageKey] ?? advisory.reasonMessageKey;
      parts.add(_lookupCropActionMessage(l10n, key));
    }
    if (parts.isEmpty) return;

    final voice = context.read<VoiceService>();
    final started = await voice.speak(parts.join(' '), languageCode: 'en');
    if (!mounted) return;
    if (!started) setState(() => _voiceUnavailableMessageShown = true);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.weatherTitle)),
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

    final weather = _weather!;
    if (!weather.available) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(child: Text(weather.unavailableReason ?? l10n.weatherUnavailable, textAlign: TextAlign.center)),
        ],
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (weather.isStale)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(l10n.weatherStale, style: const TextStyle(color: Colors.orange, fontStyle: FontStyle.italic)),
          ),
        if (weather.current != null) _buildCurrentCard(weather.current!),
        const SizedBox(height: 16),
        if (weather.forecast.isNotEmpty) ...[
          Text(l10n.forecastLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          ...weather.forecast.map((day) => Card(
                child: ListTile(
                  title: Text(day.forecastDate),
                  subtitle: Text(day.reading.rainProbabilityPercent != null ? '${day.reading.rainProbabilityPercent!.round()}% chance of rain' : ''),
                ),
              )),
        ],
        if (weather.cropAction != null) ...[
          const Divider(height: 32),
          Text(l10n.cropActionsLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          Card(
            color: Colors.orange.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber, color: Colors.orange),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(_lookupCropActionMessage(l10n, cropActionMessageKeys[weather.cropAction!.reasonMessageKey] ?? weather.cropAction!.reasonMessageKey)),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 16),
        OutlinedButton.icon(onPressed: () => _speak(l10n), icon: const Icon(Icons.volume_up), label: Text(l10n.listenButton)),
        if (_voiceUnavailableMessageShown)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(l10n.voiceUnavailable, style: const TextStyle(fontSize: 12, color: Colors.grey))),
      ],
    );
  }

  Widget _buildCurrentCard(WeatherReading current) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (current.temperatureC != null) Text('${current.temperatureC!.round()}°C', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
            if (current.humidityPercent != null) Text('Humidity: ${current.humidityPercent!.round()}%'),
            if (current.windSpeedKmh != null) Text('Wind: ${current.windSpeedKmh!.round()} km/h'),
          ],
        ),
      ),
    );
  }
}
