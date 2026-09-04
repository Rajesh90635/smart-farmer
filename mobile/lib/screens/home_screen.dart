import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/friendly_error.dart';
import '../features/auth/farmer_repository.dart';
import '../features/daily_briefing/daily_briefing_screen.dart';
import '../features/dealer_market/product_list_screen.dart';
import '../features/farm/my_farms_screen.dart';
import '../features/harvest/harvest_history_screen.dart';
import '../features/notifications/notification_list_screen.dart';
import '../features/notifications/notification_repository.dart';
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
  int _unreadNotifications = 0;

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
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
    _loadUnreadNotificationCount();
  }

  /// Best-effort only, matching the dashboard's own pattern of not
  /// blocking Home on a secondary data source - an unread badge that
  /// fails to load just stays hidden rather than surfacing a second error.
  Future<void> _loadUnreadNotificationCount() async {
    try {
      final page = await context.read<NotificationRepository>().listNotifications(unreadOnly: true, limit: 1);
      if (!mounted) return;
      setState(() => _unreadNotifications = page.unreadCount);
    } catch (_) {
      // See method doc.
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.navHome),
        actions: [
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                icon: const Icon(Icons.notifications_outlined),
                tooltip: l10n.notificationListTitle,
                onPressed: () async {
                  await Navigator.of(context).push(MaterialPageRoute(builder: (_) => const NotificationListScreen()));
                  _loadUnreadNotificationCount();
                },
              ),
              if (_unreadNotifications > 0)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    padding: const EdgeInsets.all(2),
                    decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                    constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                    child: Text(
                      '$_unreadNotifications',
                      style: const TextStyle(color: Colors.white, fontSize: 10),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
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
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
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
          label: Text(l10n.dailyBriefingTitle),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _SummaryCard(label: l10n.homeFarmsSummaryLabel, value: dashboard.farmCount)),
            const SizedBox(width: 12),
            Expanded(child: _SummaryCard(label: l10n.farmDetailsPlotsSectionLabel, value: dashboard.plotCount)),
          ],
        ),
        const SizedBox(height: 12),
        _SummaryCard(label: l10n.homeActiveCropsSummaryLabel, value: dashboard.activeCropCycleCount, wide: true),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const HarvestHistoryScreen()),
          ),
          icon: const Icon(Icons.agriculture),
          label: Text(l10n.viewHarvestHistoryButton),
        ),
        const SizedBox(height: 12),
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const ProductListScreen()),
          ),
          icon: const Icon(Icons.shopping_cart_outlined),
          label: Text(l10n.homeBuyInputsButton),
        ),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const MyFarmsScreen()),
          ),
          icon: const Icon(Icons.grass),
          label: Text(l10n.homeGoToMyFarmsButton),
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
