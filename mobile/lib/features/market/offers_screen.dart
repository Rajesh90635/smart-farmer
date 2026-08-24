import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'market_models.dart';
import 'market_repository.dart';

/// Offers received on one of the farmer's own harvest listings. There is
/// no backend endpoint to list counter-offer history for an offer - only
/// the current Offer (price/quantity/status) is shown, matching what the
/// contract actually provides rather than fabricating a negotiation
/// history view.
class OffersScreen extends StatefulWidget {
  final String listingId;
  const OffersScreen({super.key, required this.listingId});

  @override
  State<OffersScreen> createState() => _OffersScreenState();
}

class _OffersScreenState extends State<OffersScreen> {
  List<Offer> _offers = [];
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
      final offers = await context.read<MarketRepository>().listOffersForListing(widget.listingId);
      if (!mounted) return;
      setState(() {
        _offers = offers;
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

  Future<void> _acceptOffer(Offer offer, AppLocalizations l10n) async {
    try {
      await context.read<MarketRepository>().acceptOffer(offer.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.offerAcceptedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _rejectOffer(Offer offer, AppLocalizations l10n) async {
    try {
      await context.read<MarketRepository>().rejectOffer(offer.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.offerRejectedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _showCounterSheet(Offer offer, AppLocalizations l10n) async {
    final priceController = TextEditingController(text: offer.pricePerUnit);
    final quantityController = TextEditingController(text: offer.quantity);
    final messageController = TextEditingController();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.counterOfferTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 12),
            TextField(
              controller: priceController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: l10n.pricePerUnitLabel),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: quantityController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: l10n.offerQuantityLabel),
            ),
            const SizedBox(height: 12),
            TextField(controller: messageController, decoration: InputDecoration(labelText: l10n.counterMessageOptionalLabel)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () async {
                Navigator.of(sheetContext).pop();
                try {
                  await context.read<MarketRepository>().counterOffer(
                        offerId: offer.id,
                        pricePerUnit: priceController.text.trim(),
                        quantity: quantityController.text.trim(),
                        message: messageController.text.trim().isEmpty ? null : messageController.text.trim(),
                      );
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.counterSentMessage)));
                  await _load();
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
                }
              },
              child: Text(l10n.sendCounterButton),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'accepted':
        return Colors.green;
      case 'rejected':
        return Colors.red;
      case 'cancelled':
        return Colors.grey;
      case 'expired':
        return Colors.grey;
      case 'completed':
        return Colors.blue;
      default:
        return Colors.orange;
    }
  }

  String _statusLabel(String status, AppLocalizations l10n) {
    switch (status) {
      case 'accepted':
        return l10n.offerStatusAcceptedLabel;
      case 'rejected':
        return l10n.offerStatusRejectedLabel;
      case 'cancelled':
        return l10n.offerStatusCancelledLabel;
      case 'expired':
        return l10n.offerStatusExpiredLabel;
      case 'completed':
        return l10n.offerStatusCompletedLabel;
      default:
        return l10n.offerStatusActiveLabel;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.offersTitle)),
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
    if (_offers.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noOffersYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _offers.map((offer) => _buildOfferCard(offer, l10n)).toList(),
    );
  }

  Widget _buildOfferCard(Offer offer, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(width: 10, height: 10, decoration: BoxDecoration(color: _statusColor(offer.status), shape: BoxShape.circle)),
                const SizedBox(width: 8),
                Text(_statusLabel(offer.status, l10n), style: TextStyle(color: _statusColor(offer.status), fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Text('${offer.quantity} ${offer.unit} @ ${offer.pricePerUnit}'),
            if (offer.status == 'active') ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  OutlinedButton(onPressed: () => _acceptOffer(offer, l10n), child: Text(l10n.acceptOfferButton)),
                  OutlinedButton(onPressed: () => _showCounterSheet(offer, l10n), child: Text(l10n.counterOfferButton)),
                  OutlinedButton(onPressed: () => _rejectOffer(offer, l10n), child: Text(l10n.rejectOfferButton)),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
