import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import '../harvest/harvest_models.dart';
import '../harvest/harvest_repository.dart';
import 'offers_screen.dart';
import 'sales_screen.dart';

/// Farmer-side market surface only - reuses HarvestRepository.listMyListings()
/// (built for the Harvest feature) rather than duplicating that fetch. A
/// farmer cannot "discover" buyers in this backend (GET /marketplace/listings
/// is buyer-role-only) - this screen shows the farmer's own listings and
/// lets them react to offers already made on them, which is the entire
/// farmer-facing surface of the marketplace.
class MarketScreen extends StatefulWidget {
  const MarketScreen({super.key});

  @override
  State<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends State<MarketScreen> {
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
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.marketTitle),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SalesScreen())),
            child: Text(l10n.mySalesButton, style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
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
    if (_listings.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noListingsYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _listings.map((listing) => _buildListingCard(listing, l10n)).toList(),
    );
  }

  Widget _buildListingCard(HarvestListing listing, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${listing.quantityAvailable} ${listing.unit}', style: const TextStyle(fontWeight: FontWeight.bold)),
            if (listing.qualityGrade != null) Text(listing.qualityGrade!),
            if (listing.preferredPrice != null) Text(listing.preferredPrice!),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => OffersScreen(listingId: listing.id)),
              ),
              child: Text(l10n.viewOffersButton),
            ),
          ],
        ),
      ),
    );
  }
}
