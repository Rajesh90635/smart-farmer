import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_risk_models.dart';
import 'crop_risk_repository.dart';

/// Every factor is rendered with its source and explanation - never a
/// bare "HIGH"/"LOW" label alone. `recommendation` (when present) is
/// shown in a visually distinct section from the observed factors, since
/// it is a suggestion, never a confirmed fact.
class RiskScoreScreen extends StatefulWidget {
  final String cropCycleId;
  const RiskScoreScreen({super.key, required this.cropCycleId});

  @override
  State<RiskScoreScreen> createState() => _RiskScoreScreenState();
}

class _RiskScoreScreenState extends State<RiskScoreScreen> {
  CropRiskScore? _risk;
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
      final risk = await context.read<CropRiskRepository>().getRiskScore(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _risk = risk;
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

  Color _colorFor(String value) {
    switch (value) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String _labelFor(String value, AppLocalizations l10n) {
    switch (value) {
      case 'high':
        return l10n.riskHighLabel;
      case 'medium':
        return l10n.riskMediumLabel;
      case 'low':
        return l10n.riskLowLabel;
      case 'insufficient_data':
        return l10n.riskInsufficientDataLabel;
      default:
        return l10n.riskUnknownLabel;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.cropRiskTitle)),
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

    final risk = _risk!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildOverallCard(risk, l10n),
        const SizedBox(height: 16),
        Text(l10n.contributingFactorsLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        ...risk.factors.map((f) => _buildFactorCard(f, l10n)),
        if (risk.recommendation != null) ...[
          const SizedBox(height: 16),
          _buildRecommendationCard(risk.recommendation!, l10n),
        ],
      ],
    );
  }

  Widget _buildOverallCard(CropRiskScore risk, AppLocalizations l10n) {
    return Card(
      color: _colorFor(risk.overallRisk).withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.overallRiskLabel, style: const TextStyle(fontSize: 14, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(
              _labelFor(risk.overallRisk, l10n),
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: _colorFor(risk.overallRisk)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFactorCard(RiskFactor factor, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(width: 10, height: 10, decoration: BoxDecoration(color: _colorFor(factor.value), shape: BoxShape.circle)),
                const SizedBox(width: 8),
                Expanded(child: Text(factor.factorName, style: const TextStyle(fontWeight: FontWeight.bold))),
                Text(_labelFor(factor.value, l10n), style: TextStyle(color: _colorFor(factor.value), fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 4),
            Text(factor.explanation, style: const TextStyle(fontSize: 13)),
            const SizedBox(height: 2),
            Text('${l10n.sourceLabel}: ${factor.source}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationCard(String recommendation, AppLocalizations l10n) {
    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.lightbulb_outline, size: 18, color: Colors.blueGrey),
                const SizedBox(width: 6),
                Text(l10n.suggestionLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Text(recommendation),
          ],
        ),
      ),
    );
  }
}
