import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'health_timeline_models.dart';
import 'health_timeline_repository.dart';

/// Every event shown here is a real, dated fact read directly from the
/// backend - this screen never converts a health_status into a
/// percentage or interprets notes as a diagnosis. Farmer-facing labels
/// replace raw backend terms like "ai_analysis" or "disease_detected",
/// but only ever for a value the backend actually returned - nothing is
/// guessed when a field is absent.
class HealthTimelineScreen extends StatefulWidget {
  final String cropCycleId;
  const HealthTimelineScreen({super.key, required this.cropCycleId});

  @override
  State<HealthTimelineScreen> createState() => _HealthTimelineScreenState();
}

class _HealthTimelineScreenState extends State<HealthTimelineScreen> {
  CropHealthTimeline? _timeline;
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
      final timeline = await context.read<HealthTimelineRepository>().getTimeline(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _timeline = timeline;
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

  IconData _iconFor(String eventType) {
    switch (eventType) {
      case 'crop_cycle_started':
        return Icons.flag_outlined;
      case 'stage_changed':
        return Icons.timeline;
      case 'photo_captured':
        return Icons.photo_camera_outlined;
      case 'ai_analysis':
        return Icons.biotech_outlined;
      case 'health_case_created':
        return Icons.support_agent_outlined;
      case 'case_reviewed':
        return Icons.fact_check_outlined;
      case 'treatment_applied':
        return Icons.medical_services_outlined;
      case 'treatment_follow_up':
        return Icons.visibility_outlined;
      case 'harvested':
        return Icons.agriculture_outlined;
      default:
        return Icons.circle_outlined;
    }
  }

  Color _colorForHealthStatus(String? status) {
    switch (status) {
      case 'healthy':
        return Colors.green;
      case 'disease_detected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _friendlyTitle(TimelineEvent event, AppLocalizations l10n) {
    switch (event.eventType) {
      case 'crop_cycle_started':
        return l10n.timelineCropStartedLabel;
      case 'stage_changed':
        return l10n.timelineStageChangedLabel;
      case 'photo_captured':
        return l10n.timelinePhotoCapturedLabel;
      case 'ai_analysis':
        return l10n.timelineHealthCheckLabel;
      case 'health_case_created':
        return l10n.timelineExpertReviewRequestedLabel;
      case 'case_reviewed':
        return l10n.timelineExpertReviewCompletedLabel;
      case 'treatment_applied':
        return l10n.timelineTreatmentAppliedLabel;
      case 'treatment_follow_up':
        return l10n.timelineFollowUpRecordedLabel;
      case 'harvested':
        return l10n.timelineHarvestedLabel;
      default:
        return event.title;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.healthTimelineTitle)),
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
          Center(child: ElevatedButton(onPressed: _load, child: const Text('Try again'))),
        ],
      );
    }

    final events = _timeline!.events;
    if (events.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noHealthObservationsYet))]);
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: events.length,
      itemBuilder: (context, index) => _buildEventTile(events[index], l10n),
    );
  }

  Widget _buildEventTile(TimelineEvent event, AppLocalizations l10n) {
    return Card(
      child: ListTile(
        leading: Icon(_iconFor(event.eventType), color: _colorForHealthStatus(event.healthStatus)),
        title: Text(_friendlyTitle(event, l10n), style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(event.description),
            const SizedBox(height: 2),
            Text(event.eventDatetime.split('T').first, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }
}
