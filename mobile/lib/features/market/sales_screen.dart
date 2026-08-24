import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'market_models.dart';
import 'market_repository.dart';
import 'sale_detail_screen.dart';
import 'sale_status_labels.dart';

class SalesScreen extends StatefulWidget {
  const SalesScreen({super.key});

  @override
  State<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  List<SaleOrder> _sales = [];
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
      final sales = await context.read<MarketRepository>().listMySales();
      if (!mounted) return;
      setState(() {
        _sales = sales;
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
      appBar: AppBar(title: Text(l10n.salesTitle)),
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
    if (_sales.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noSalesYet))]);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: _sales.map((sale) => _buildSaleCard(sale, l10n)).toList(),
    );
  }

  Widget _buildSaleCard(SaleOrder sale, AppLocalizations l10n) {
    return Card(
      child: ListTile(
        title: Text('${sale.quantity} ${sale.unit} @ ${sale.pricePerUnit}'),
        subtitle: Row(
          children: [
            Container(width: 10, height: 10, decoration: BoxDecoration(color: saleStatusColor(sale.status), shape: BoxShape.circle)),
            const SizedBox(width: 8),
            Text(saleStatusLabel(sale.status, l10n), style: TextStyle(color: saleStatusColor(sale.status))),
          ],
        ),
        trailing: Text(sale.netValue),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => SaleDetailScreen(saleId: sale.id)),
        ),
      ),
    );
  }
}
