import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'harvest_models.dart';
import 'harvest_repository.dart';

/// Farmer-wide harvest and listing history, across every crop cycle -
/// read-only. Recording/status actions live on HarvestListScreen
/// (crop-cycle-scoped), reached from Crop Details.
class HarvestHistoryScreen extends StatefulWidget {
  const HarvestHistoryScreen({super.key});

  @override
  State<HarvestHistoryScreen> createState() => _HarvestHistoryScreenState();
}

class _HarvestHistoryScreenState extends State<HarvestHistoryScreen> {
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.harvestHistoryTitle),
          bottom: TabBar(tabs: [Tab(text: l10n.myHarvestsTabLabel), Tab(text: l10n.myListingsTabLabel)]),
        ),
        body: TabBarView(children: [_MyHarvestsTab(l10n: l10n), _MyListingsTab(l10n: l10n)]),
      ),
    );
  }
}

class _MyHarvestsTab extends StatefulWidget {
  final AppLocalizations l10n;
  const _MyHarvestsTab({required this.l10n});

  @override
  State<_MyHarvestsTab> createState() => _MyHarvestsTabState();
}

class _MyHarvestsTabState extends State<_MyHarvestsTab> {
  List<HarvestRecord> _harvests = [];
  bool _loading = true;
  String? _error;

  Color _statusColor(String status) {
    switch (status) {
      case 'approaching':
        return Colors.orange;
      case 'ready':
        return Colors.blue;
      case 'harvested':
        return Colors.teal;
      case 'listed':
        return Colors.purple;
      case 'partially_sold':
        return Colors.amber;
      case 'sold':
        return Colors.green;
      case 'cancelled':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _statusLabel(String status, AppLocalizations l10n) {
    switch (status) {
      case 'approaching':
        return l10n.harvestStatusApproachingLabel;
      case 'ready':
        return l10n.harvestStatusReadyLabel;
      case 'harvested':
        return l10n.harvestStatusHarvestedLabel;
      case 'listed':
        return l10n.harvestStatusListedLabel;
      case 'partially_sold':
        return l10n.harvestStatusPartiallySoldLabel;
      case 'sold':
        return l10n.harvestStatusSoldLabel;
      case 'cancelled':
        return l10n.harvestStatusCancelledLabel;
      default:
        return l10n.harvestStatusPlannedLabel;
    }
  }

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
      final harvests = await context.read<HarvestRepository>().listMyHarvests();
      if (!mounted) return;
      setState(() {
        _harvests = harvests;
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

  @override
  Widget build(BuildContext context) {
    final l10n = widget.l10n;
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
    if (_harvests.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noHarvestHistoryYet))]);
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: _harvests.map((h) => Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(width: 10, height: 10, decoration: BoxDecoration(color: _statusColor(h.status), shape: BoxShape.circle)),
                        const SizedBox(width: 8),
                        Text(_statusLabel(h.status, l10n), style: TextStyle(color: _statusColor(h.status), fontWeight: FontWeight.bold)),
                      ],
                    ),
                    if (h.estimatedQuantity != null) Text('${h.estimatedQuantity} ${h.unit}'),
                    if (h.actualHarvestDate != null) Text(h.actualHarvestDate!),
                  ],
                ),
              ),
            ))
            .toList(),
      ),
    );
  }
}

class _MyListingsTab extends StatefulWidget {
  final AppLocalizations l10n;
  const _MyListingsTab({required this.l10n});

  @override
  State<_MyListingsTab> createState() => _MyListingsTabState();
}

class _MyListingsTabState extends State<_MyListingsTab> {
  List<HarvestListing> _listings = [];
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
      final listings = await context.read<HarvestRepository>().listMyListings();
      if (!mounted) return;
      setState(() {
        _listings = listings;
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

  @override
  Widget build(BuildContext context) {
    final l10n = widget.l10n;
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
    if (_listings.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noListingsYet))]);
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: _listings.map((listing) => Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${listing.quantityAvailable} ${listing.unit}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    if (listing.qualityGrade != null) Text(listing.qualityGrade!),
                    if (listing.preferredPrice != null) Text(listing.preferredPrice!),
                    Text(listing.isActive ? l10n.listingActiveLabel : l10n.listingInactiveLabel),
                  ],
                ),
              ),
            ))
            .toList(),
      ),
    );
  }
}
