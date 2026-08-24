import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/friendly_error.dart';
import '../features/auth/farmer_repository.dart';
import '../features/daily_briefing/daily_briefing_screen.dart';
import '../features/farm/my_farms_screen.dart';
import '../features/harvest/harvest_history_screen.dart';
import '../l10n/app_localizations.dart';

/// Farmer Home: a simple farm/plot/crop summary only. No disease, weather,
/// or market data - those modules don't exist yet (see PROJECT_STATUS.md).
/// Deliberately not a "complicated dashboard" per the UX rule - four
/// numbers and a shortcut, nothing more.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  FarmerDashboard? _dashboard;
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
      final dashboard = await context.read<FarmerRepository>().getDashboard();
      setState(() {
        _dashboard = dashboard;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    final l10n = AppLocalizations.of(context)!;
    if (_loading) return const Center(child: CircularProgressIndicator());
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

    final dashboard = _dashboard!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const DailyBriefingScreen()),
          ),
          icon: const Icon(Icons.wb_sunny_outlined),
          label: const Text("Today's Briefing"),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _SummaryCard(label: 'Farms', value: dashboard.farmCount)),
            const SizedBox(width: 12),
            Expanded(child: _SummaryCard(label: 'Plots', value: dashboard.plotCount)),
          ],
        ),
        const SizedBox(height: 12),
        _SummaryCard(label: 'Active crops', value: dashboard.activeCropCycleCount, wide: true),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const HarvestHistoryScreen()),
          ),
          icon: const Icon(Icons.agriculture),
          label: Text(l10n.viewHarvestHistoryButton),
        ),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const MyFarmsScreen()),
          ),
          icon: const Icon(Icons.grass),
          label: const Text('Go to My Farms'),
        ),
      ],
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final String label;
  final int value;
  final bool wide;
  const _SummaryCard({required this.label, required this.value, this.wide = false});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: wide ? CrossAxisAlignment.start : CrossAxisAlignment.center,
          children: [
            Text('$value', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 4),
            Text(label, style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }
}
