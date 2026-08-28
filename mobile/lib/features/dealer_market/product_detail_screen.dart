import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'dealer_market_models.dart';
import 'dealer_market_repository.dart';
import 'order_detail_screen.dart';
import 'product_list_screen.dart';

/// The only screen where a farmer sees real dealer offers
/// (dealer_product_id) for a product and can add one to the cart. Every
/// price/stock figure shown is the backend's own current value, fetched
/// fresh on this screen's load - never cached from the browse list
/// (GET /products never returns a price at all, by design).
class ProductDetailScreen extends StatefulWidget {
  final String productId;
  const ProductDetailScreen({super.key, required this.productId});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  Product? _product;
  PriceComparison? _comparison;
  bool _loading = true;
  String? _error;
  bool _addingToCart = false;

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
      final repository = context.read<DealerMarketRepository>();
      final results = await Future.wait([repository.getProduct(widget.productId), repository.compareOffers(widget.productId)]);
      if (!mounted) return;
      setState(() {
        _product = results[0] as Product;
        _comparison = results[1] as PriceComparison;
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

  Future<void> _checkScamShield(DealerOffer offer, AppLocalizations l10n) async {
    try {
      final status = await context.read<DealerMarketRepository>().getScamShieldStatus(offer.dealerProductId);
      if (!mounted) return;
      await showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(l10n.productDetailScamShieldTitle),
          content: Text(status.message),
          actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(l10n.productDetailOkButton))],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _addToCart(DealerOffer offer, AppLocalizations l10n) async {
    int quantity = 1;
    final confirmed = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.productDetailQuantityLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: quantity > 1 ? () => setSheetState(() => quantity--) : null,
                  ),
                  Text('$quantity', style: const TextStyle(fontSize: 20)),
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline),
                    onPressed: quantity < offer.stockQuantity ? () => setSheetState(() => quantity++) : null,
                  ),
                ],
              ),
              Text(
                l10n.productDetailInStockLabel(offer.stockQuantity.toString()),
                style: const TextStyle(fontSize: 12, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => Navigator.of(sheetContext).pop(quantity), child: Text(l10n.productDetailAddToCartButton)),
            ],
          ),
        ),
      ),
    );
    if (confirmed == null) return;

    setState(() => _addingToCart = true);
    try {
      final cart = await context.read<DealerMarketRepository>().addToCart(dealerProductId: offer.dealerProductId, quantity: confirmed);
      if (!mounted) return;
      setState(() => _addingToCart = false);
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => OrderDetailScreen(orderId: cart.id)));
    } catch (e) {
      if (!mounted) return;
      setState(() => _addingToCart = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(_product?.name ?? l10n.productDetailDefaultTitle)),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: Text(l10n.genericErrorRetry))],
        ),
      );
    }

    final product = _product!;
    final comparison = _comparison!;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(productCategoryLabel(product.category, l10n), style: const TextStyle(color: Colors.grey)),
        const SizedBox(height: 4),
        Text('${product.packSizeValue} ${product.packSizeUnit}', style: const TextStyle(fontSize: 16)),
        if (product.manufacturer != null) Text(l10n.productDetailByManufacturerLabel(product.manufacturer!)),
        if (product.description != null) ...[const SizedBox(height: 12), Text(product.description!)],
        if (product.usageInformation != null) ...[
          const SizedBox(height: 12),
          Text(l10n.productDetailUsageLabel, style: Theme.of(context).textTheme.titleSmall),
          Text(product.usageInformation!),
        ],
        if (comparison.referencePricePerUnit != null) ...[
          const SizedBox(height: 16),
          Text(
            '${l10n.productDetailReferencePriceLabel(comparison.referencePricePerUnit!)}${comparison.referenceSource != null ? ' (${comparison.referenceSource})' : ''}',
            style: const TextStyle(fontStyle: FontStyle.italic),
          ),
        ],
        const SizedBox(height: 20),
        Text(l10n.productDetailAvailableFromDealersLabel, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (comparison.offers.isEmpty)
          Text(l10n.productDetailNoDealersAvailableMessage)
        else
          ...comparison.offers.map((offer) => _buildOfferCard(offer, l10n)),
      ],
    );
  }

  Widget _buildOfferCard(DealerOffer offer, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('₹${offer.dealerPrice}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(
              l10n.productDetailOfferSummaryLabel(offer.pricePerUnit, offer.unit, offer.stockQuantity.toString()),
              style: const TextStyle(fontSize: 12),
            ),
            if (!offer.isAvailable) Text(l10n.productDetailCurrentlyUnavailableLabel, style: const TextStyle(color: Colors.red, fontSize: 12)),
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton(onPressed: () => _checkScamShield(offer, l10n), child: Text(l10n.productDetailCheckPriceFairnessButton)),
                const Spacer(),
                ElevatedButton(
                  onPressed: offer.isAvailable && offer.stockQuantity > 0 && !_addingToCart ? () => _addToCart(offer, l10n) : null,
                  child: Text(l10n.productDetailAddToCartButton),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
