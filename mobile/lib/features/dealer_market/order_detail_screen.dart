import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'dealer_market_models.dart';
import 'dealer_market_repository.dart';
import 'order_status_labels.dart';

String _disputeReasonLabel(String reason, AppLocalizations l10n) {
  switch (reason) {
    case 'wrong_product':
      return l10n.orderDisputeReasonWrongProductLabel;
    case 'missing_item':
      return l10n.orderDisputeReasonMissingItemLabel;
    case 'damaged_product':
      return l10n.orderDisputeReasonDamagedProductLabel;
    case 'payment_issue':
      return l10n.orderDisputeReasonPaymentIssueLabel;
    case 'delivery_issue':
      return l10n.orderDisputeReasonDeliveryIssueLabel;
    case 'unexpected_charge':
      return l10n.orderDisputeReasonUnexpectedChargeLabel;
    case 'product_authenticity_concern':
      return l10n.orderDisputeReasonProductAuthenticityConcernLabel;
    default:
      return l10n.otherReasonLabel;
  }
}

/// Serves double duty as both the cart (status == draft) and the order
/// tracking screen (any later status) - the backend itself models a cart
/// as just a DRAFT order, so this screen mirrors that instead of building
/// a separate cart UI that would drift from the real object.
///
/// Every action shown is gated by the backend's own real transition
/// rules (ALLOWED_ORDER_TRANSITIONS / dispute_service's own status
/// check), never invented - same convention as SaleDetailScreen.
class OrderDetailScreen extends StatefulWidget {
  final String orderId;
  const OrderDetailScreen({super.key, required this.orderId});

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  DealerOrder? _order;
  DealerDelivery? _delivery;
  DealerOrderDispute? _dispute;
  bool _loading = true;
  bool _acting = false;
  String? _error;

  static const _disputableStatuses = {'delivered', 'out_for_delivery'};

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
      final order = await repository.getOrder(widget.orderId);
      DealerDelivery? delivery;
      DealerOrderDispute? dispute;
      if (order.status != 'draft') {
        delivery = await repository.getDelivery(widget.orderId);
        dispute = await repository.getDispute(widget.orderId);
      }
      if (!mounted) return;
      setState(() {
        _order = order;
        _delivery = delivery;
        _dispute = dispute;
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

  Future<void> _updateQuantity(DealerOrderItem item, int newQuantity) async {
    setState(() => _acting = true);
    try {
      final repository = context.read<DealerMarketRepository>();
      if (newQuantity <= 0) {
        await repository.removeCartItem(orderId: widget.orderId, dealerProductId: item.dealerProductId);
      } else {
        await repository.updateCartItemQuantity(orderId: widget.orderId, dealerProductId: item.dealerProductId, quantity: newQuantity);
      }
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _checkout(AppLocalizations l10n) async {
    if (_order!.items.isEmpty) return;
    setState(() => _acting = true);
    try {
      final idempotencyKey = 'checkout-${_order!.id}-${_order!.items.length}-${_order!.items.map((i) => i.quantity).join('-')}';
      await context.read<DealerMarketRepository>().checkout(orderId: _order!.id, idempotencyKey: idempotencyKey);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.orderDetailOrderPlacedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _cancelOrder(AppLocalizations l10n) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(l10n.orderDetailCancelConfirmTitle),
        content: Text(l10n.orderDetailCancelConfirmMessage),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(l10n.orderDetailNoButton)),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: Text(l10n.orderDetailYesCancelButton)),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _acting = true);
    try {
      await context.read<DealerMarketRepository>().cancelOrder(widget.orderId);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _pay() async {
    setState(() => _acting = true);
    try {
      await context.read<DealerMarketRepository>().initiatePayment(widget.orderId);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  /// SANDBOX/TEST-ONLY - see DealerMarketRepository.completeSandboxPayment.
  /// Labeled plainly as a simulation in the UI, never presented as a real
  /// payment gateway.
  Future<void> _completeSandboxPayment() async {
    setState(() => _acting = true);
    try {
      await context.read<DealerMarketRepository>().completeSandboxPayment(widget.orderId);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _confirmDelivery(AppLocalizations l10n) async {
    setState(() => _acting = true);
    try {
      await context.read<DealerMarketRepository>().confirmDelivery(widget.orderId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.orderDetailDeliveryConfirmedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _showDisputeSheet(AppLocalizations l10n) async {
    String selectedReason = orderDisputeReasons.first;
    final descriptionController = TextEditingController();
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.orderDetailFileDisputeTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedReason,
                items: orderDisputeReasons.map((r) => DropdownMenuItem(value: r, child: Text(_disputeReasonLabel(r, l10n)))).toList(),
                onChanged: (v) => setSheetState(() => selectedReason = v ?? orderDisputeReasons.first),
                decoration: InputDecoration(labelText: l10n.orderDetailDisputeReasonLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: descriptionController, decoration: InputDecoration(labelText: l10n.orderDetailDisputeDescriptionOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  setState(() => _acting = true);
                  try {
                    await context.read<DealerMarketRepository>().fileDispute(
                          orderId: widget.orderId,
                          reason: selectedReason,
                          description: descriptionController.text.trim().isEmpty ? null : descriptionController.text.trim(),
                        );
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.orderDetailDisputeFiledMessage)));
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  } finally {
                    if (mounted) setState(() => _acting = false);
                  }
                },
                child: Text(l10n.orderDetailSubmitDisputeButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isCart = _order?.status == 'draft';
    return Scaffold(
      appBar: AppBar(title: Text(isCart ? l10n.orderDetailCartTitle : l10n.orderDetailOrderTitle)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
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

    final order = _order!;
    final isCart = order.status == 'draft';

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (!isCart) ...[
          Row(
            children: [
              Container(width: 12, height: 12, decoration: BoxDecoration(color: orderStatusColor(order.status), shape: BoxShape.circle)),
              const SizedBox(width: 8),
              Text(orderStatusLabel(order.status, l10n), style: TextStyle(color: orderStatusColor(order.status), fontWeight: FontWeight.bold, fontSize: 18)),
            ],
          ),
          const SizedBox(height: 16),
        ],
        Text(l10n.orderDetailItemsLabel, style: Theme.of(context).textTheme.titleMedium),
        ...order.items.map((item) => _buildItemTile(item, isCart, l10n)),
        if (order.items.isEmpty) Padding(padding: const EdgeInsets.symmetric(vertical: 16), child: Text(l10n.orderDetailNoItemsMessage)),
        if (!isCart && order.finalAmount != null) ...[
          const Divider(height: 32),
          if (order.subtotalAmount != null) Text(l10n.orderDetailSubtotalLabel(order.subtotalAmount!)),
          if (order.taxAmount != null) Text(l10n.orderDetailTaxLabel(order.taxAmount!)),
          if (order.deliveryFeeAmount != null) Text(l10n.orderDetailDeliveryFeeLabel(order.deliveryFeeAmount!)),
          Text(l10n.orderDetailTotalLabel(order.finalAmount!), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ],
        if (order.rejectionReason != null) ...[
          const SizedBox(height: 8),
          Text(l10n.orderDetailRejectedLabel(order.rejectionReason!), style: const TextStyle(color: Colors.red)),
        ],
        if (_delivery != null) ...[
          const Divider(height: 32),
          Text(l10n.orderDetailDeliveryLabel, style: Theme.of(context).textTheme.titleMedium),
          Text(_delivery!.status.replaceAll('_', ' ').toUpperCase()),
          if (_delivery!.estimatedDeliveryDate != null) Text(l10n.orderDetailEstimatedDeliveryLabel(_delivery!.estimatedDeliveryDate!)),
          if (_delivery!.trackingNote != null) Text(_delivery!.trackingNote!),
        ],
        if (_dispute != null) ...[
          const Divider(height: 32),
          Text(l10n.orderDetailDisputeLabel, style: Theme.of(context).textTheme.titleMedium),
          Text('${_disputeReasonLabel(_dispute!.reason, l10n)} - ${_dispute!.status.replaceAll('_', ' ').toUpperCase()}'),
        ],
        const SizedBox(height: 24),
        if (_acting) const Center(child: CircularProgressIndicator()) else _buildActions(order, isCart, l10n),
      ],
    );
  }

  Widget _buildItemTile(DealerOrderItem item, bool isCart, AppLocalizations l10n) {
    return Card(
      child: ListTile(
        title: Text(item.productNameSnapshot),
        subtitle: item.finalItemAmount != null
            ? Text('₹${item.unitPrice} x ${item.quantity} = ₹${item.finalItemAmount}')
            : Text(l10n.orderDetailItemQuantityLabel(item.quantity.toString())),
        trailing: isCart
            ? Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () => _updateQuantity(item, item.quantity - 1)),
                  Text('${item.quantity}'),
                  IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () => _updateQuantity(item, item.quantity + 1)),
                ],
              )
            : null,
      ),
    );
  }

  Widget _buildActions(DealerOrder order, bool isCart, AppLocalizations l10n) {
    if (isCart) {
      return ElevatedButton(onPressed: order.items.isEmpty ? null : () => _checkout(l10n), child: Text(l10n.orderDetailCheckoutButton));
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        if (order.status == 'confirmed') ElevatedButton(onPressed: _pay, child: Text(l10n.orderDetailPayButton)),
        if (order.status == 'payment_pending')
          ElevatedButton(onPressed: _completeSandboxPayment, child: Text(l10n.orderDetailSimulatePaymentButton)),
        if (cancellableOrderStatuses.contains(order.status))
          OutlinedButton(onPressed: () => _cancelOrder(l10n), child: Text(l10n.orderDetailCancelOrderButton)),
        if (order.status == 'delivered')
          ElevatedButton(onPressed: () => _confirmDelivery(l10n), child: Text(l10n.orderDetailConfirmDeliveryButton)),
        if (_disputableStatuses.contains(order.status) && _dispute == null)
          OutlinedButton(onPressed: () => _showDisputeSheet(l10n), child: Text(l10n.orderDetailFileDisputeButton)),
      ],
    );
  }
}
