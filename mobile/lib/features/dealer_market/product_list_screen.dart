import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'dealer_market_models.dart';
import 'dealer_market_repository.dart';
import 'order_list_screen.dart';
import 'product_detail_screen.dart';

String productCategoryLabel(String category, AppLocalizations l10n) {
  switch (category) {
    case 'seed':
      return l10n.productCategorySeedLabel;
    case 'fertilizer':
      return l10n.productCategoryFertilizerLabel;
    case 'bio_input':
      return l10n.productCategoryBioInputLabel;
    case 'pest_control_product':
      return l10n.productCategoryPestControlLabel;
    case 'crop_protection_product':
      return l10n.productCategoryCropProtectionLabel;
    case 'equipment':
      return l10n.productCategoryEquipmentLabel;
    case 'other_agricultural_input':
      return l10n.productCategoryOtherLabel;
    default:
      return category;
  }
}

/// Browse: only APPROVED products (enforced server-side by
/// product_service.list_approved_products) ever appear here - a farmer
/// never sees a pending/rejected/suspended/recalled listing.
class ProductListScreen extends StatefulWidget {
  const ProductListScreen({super.key});

  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  List<Product> _products = [];
  bool _loading = true;
  String? _error;
  String _query = '';
  String? _selectedCategory;

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
      final products = await context.read<DealerMarketRepository>().listProducts(query: _query.isEmpty ? null : _query);
      if (!mounted) return;
      setState(() {
        _products = products;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.productListTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.receipt_long),
            tooltip: l10n.orderListTitle,
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const OrderListScreen())),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: TextField(
              decoration: InputDecoration(labelText: l10n.productListSearchLabel, prefixIcon: const Icon(Icons.search)),
              onSubmitted: (v) {
                _query = v;
                _load();
              },
            ),
          ),
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(l10n.productListAllCategoryLabel),
                    selected: _selectedCategory == null,
                    onSelected: (_) => setState(() => _selectedCategory = null),
                  ),
                ),
                ...productCategoryOptions.map(
                  (category) => Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(productCategoryLabel(category, l10n)),
                      selected: _selectedCategory == category,
                      onSelected: (_) => setState(() => _selectedCategory = category),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(child: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n))),
        ],
      ),
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
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.genericErrorRetry))),
        ],
      );
    }

    final filtered = _selectedCategory == null ? _products : _products.where((p) => p.category == _selectedCategory).toList();
    if (filtered.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.productListNoProductsFoundMessage))]);
    }

    return ListView.builder(
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        final product = filtered[index];
        return ListTile(
          leading: const Icon(Icons.inventory_2_outlined),
          title: Text(product.name),
          subtitle: Text('${productCategoryLabel(product.category, l10n)} • ${product.packSizeValue} ${product.packSizeUnit}'),
          onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProductDetailScreen(productId: product.id))),
        );
      },
    );
  }
}
