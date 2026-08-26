import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'dealer_market_models.dart';
import 'dealer_market_repository.dart';
import 'order_detail_screen.dart';
import 'order_status_labels.dart';

/// GET /orders never returns a DRAFT order (the cart is excluded
/// server-side) - this is genuinely "my confirmed-or-further purchase
/// history", not a full order+cart list, matching the backend's own
/// query exactly.
class OrderListScreen extends StatefulWidget {
  const OrderListScreen({super.key});

  @override
  State<OrderListScreen> createState() => _OrderListScreenState();
}

class _OrderListScreenState extends State<OrderListScreen> {
  List<DealerOrder> _orders = [];
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
      final orders = await context.read<DealerMarketRepository>().listMyOrders();
      if (!mounted) return;
      setState(() {
        _orders = orders;
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
    return Scaffold(
      appBar: AppBar(title: const Text('My Orders')),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
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
    if (_orders.isEmpty) {
      return ListView(children: const [SizedBox(height: 100), Center(child: Text('No orders yet.'))]);
    }

    return ListView.builder(
      itemCount: _orders.length,
      itemBuilder: (context, index) {
        final order = _orders[index];
        final itemsSummary = order.items.map((i) => '${i.productNameSnapshot} x${i.quantity}').join(', ');
        return ListTile(
          leading: Container(width: 12, height: 12, decoration: BoxDecoration(color: orderStatusColor(order.status), shape: BoxShape.circle)),
          title: Text(itemsSummary, maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: Text(orderStatusLabel(order.status)),
          trailing: order.finalAmount != null ? Text('₹${order.finalAmount}') : null,
          onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => OrderDetailScreen(orderId: order.id))).then((_) => _load()),
        );
      },
    );
  }
}
