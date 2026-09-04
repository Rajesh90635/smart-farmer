import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'market_models.dart';
import 'market_repository.dart';
import 'sale_status_labels.dart';

/// Farmer-side sale management. Advance actions stop at `delivered` -
/// the backend's generic /advance endpoint would technically allow a
/// farmer to self-declare `payment_pending` too, but that step is meant
/// to be the buyer's own delivery confirmation (see
/// POST /purchases/{id}/confirm-delivery, a buyer-only endpoint) - giving
/// a farmer a UI button to self-declare it would let them claim a
/// delivery the buyer never confirmed, so that action is deliberately
/// not exposed here even though the raw endpoint doesn't forbid it.
class SaleDetailScreen extends StatefulWidget {
  final String saleId;
  const SaleDetailScreen({super.key, required this.saleId});

  @override
  State<SaleDetailScreen> createState() => _SaleDetailScreenState();
}

class _SaleDetailScreenState extends State<SaleDetailScreen> {
  SaleOrder? _sale;
  bool _loading = true;
  String? _error;

  static const _forwardAdvanceTarget = {
    'accepted': 'preparing',
    'preparing': 'ready_for_collection',
    'ready_for_collection': 'collected',
    'collected': 'in_transit',
    'in_transit': 'delivered',
  };
  static const _cancellableStatuses = {'pending', 'accepted', 'preparing', 'ready_for_collection'};
  static const _disputableStatuses = {'delivered', 'payment_pending', 'paid', 'disputed'};
  static const _cancellationReasons = [
    'price_dispute',
    'quantity_change',
    'buyer_cancelled',
    'farmer_cancelled',
    'logistics_failure',
    'weather',
    'other',
  ];
  static const _disputeReasons = [
    'wrong_quantity',
    'quality_disagreement',
    'price_disagreement',
    'payment_issue',
    'delivery_issue',
    'buyer_cancellation',
    'farmer_cancellation',
    'damaged_crop',
    'other',
  ];

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
      final sale = await context.read<MarketRepository>().getSale(widget.saleId);
      if (!mounted) return;
      setState(() {
        _sale = sale;
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

  Future<void> _acceptSale(AppLocalizations l10n) async {
    try {
      await context.read<MarketRepository>().acceptSale(widget.saleId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.saleAcceptedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  Future<void> _advanceSale(String targetStatus, AppLocalizations l10n) async {
    try {
      await context.read<MarketRepository>().advanceSale(saleId: widget.saleId, targetStatus: targetStatus);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.saleAdvancedMessage)));
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  String _reasonLabel(String reason, AppLocalizations l10n) {
    switch (reason) {
      case 'price_dispute':
        return l10n.cancellationReasonPriceDisputeLabel;
      case 'quantity_change':
        return l10n.cancellationReasonQuantityChangeLabel;
      case 'buyer_cancelled':
        return l10n.cancellationReasonBuyerCancelledLabel;
      case 'farmer_cancelled':
        return l10n.cancellationReasonFarmerCancelledLabel;
      case 'logistics_failure':
        return l10n.cancellationReasonLogisticsFailureLabel;
      case 'weather':
        return l10n.cancellationReasonWeatherLabel;
      case 'wrong_quantity':
        return l10n.disputeReasonWrongQuantityLabel;
      case 'quality_disagreement':
        return l10n.disputeReasonQualityDisagreementLabel;
      case 'price_disagreement':
        return l10n.disputeReasonPriceDisagreementLabel;
      case 'payment_issue':
        return l10n.disputeReasonPaymentIssueLabel;
      case 'delivery_issue':
        return l10n.disputeReasonDeliveryIssueLabel;
      case 'buyer_cancellation':
        return l10n.disputeReasonBuyerCancellationLabel;
      case 'farmer_cancellation':
        return l10n.disputeReasonFarmerCancellationLabel;
      case 'damaged_crop':
        return l10n.disputeReasonDamagedCropLabel;
      default:
        return l10n.otherReasonLabel;
    }
  }

  Future<void> _showCancelSheet(AppLocalizations l10n) async {
    String selectedReason = _cancellationReasons.first;
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
              Text(l10n.cancelSaleTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedReason,
                items: _cancellationReasons.map((r) => DropdownMenuItem(value: r, child: Text(_reasonLabel(r, l10n)))).toList(),
                onChanged: (v) => setSheetState(() => selectedReason = v ?? _cancellationReasons.first),
                decoration: InputDecoration(labelText: l10n.cancellationReasonLabel),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<MarketRepository>().cancelSale(saleId: widget.saleId, reason: selectedReason);
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.saleCancelledMessage)));
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  }
                },
                child: Text(l10n.cancelSaleButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showDisputeSheet(AppLocalizations l10n) async {
    String selectedReason = _disputeReasons.first;
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
              Text(l10n.fileDisputeTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedReason,
                items: _disputeReasons.map((r) => DropdownMenuItem(value: r, child: Text(_reasonLabel(r, l10n)))).toList(),
                onChanged: (v) => setSheetState(() => selectedReason = v ?? _disputeReasons.first),
                decoration: InputDecoration(labelText: l10n.disputeReasonLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: descriptionController, decoration: InputDecoration(labelText: l10n.disputeDescriptionOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<MarketRepository>().fileSaleDispute(
                          saleId: widget.saleId,
                          reason: selectedReason,
                          description: descriptionController.text.trim().isEmpty ? null : descriptionController.text.trim(),
                        );
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.disputeFiledMessage)));
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  }
                },
                child: Text(l10n.submitDisputeButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showFeedbackSheet(AppLocalizations l10n) async {
    int? selectedRating;
    final textController = TextEditingController();
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
              Text(l10n.leaveFeedbackTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              DropdownButtonFormField<int?>(
                value: selectedRating,
                items: [null, 1, 2, 3, 4, 5]
                    .map((r) => DropdownMenuItem(value: r, child: Text(r?.toString() ?? '-')))
                    .toList(),
                onChanged: (v) => setSheetState(() => selectedRating = v),
                decoration: InputDecoration(labelText: l10n.feedbackRatingOptionalLabel),
              ),
              const SizedBox(height: 12),
              TextField(controller: textController, decoration: InputDecoration(labelText: l10n.feedbackTextOptionalLabel)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<MarketRepository>().submitSaleFeedback(
                          saleId: widget.saleId,
                          rating: selectedRating,
                          feedbackText: textController.text.trim().isEmpty ? null : textController.text.trim(),
                        );
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.feedbackSubmittedMessage)));
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  }
                },
                child: Text(l10n.submitFeedbackButton),
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
    return Scaffold(
      appBar: AppBar(title: Text(l10n.saleDetailTitle)),
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
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
        ],
      );
    }

    final sale = _sale!;
    final nextTarget = _forwardAdvanceTarget[sale.status];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Container(width: 12, height: 12, decoration: BoxDecoration(color: saleStatusColor(sale.status), shape: BoxShape.circle)),
            const SizedBox(width: 8),
            Text(saleStatusLabel(sale.status, l10n), style: TextStyle(color: saleStatusColor(sale.status), fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
        const SizedBox(height: 16),
        Text('${sale.quantity} ${sale.unit} @ ${sale.pricePerUnit}'),
        const SizedBox(height: 8),
        Text('${l10n.grossValueLabel}: ${sale.grossValue}'),
        Text('${l10n.chargesLabel}: ${sale.charges}'),
        Text('${l10n.netValueLabel}: ${sale.netValue}'),
        if (sale.cancellationReason != null) Text(_reasonLabel(sale.cancellationReason!, l10n)),
        const SizedBox(height: 20),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            if (sale.status == 'pending') ElevatedButton(onPressed: () => _acceptSale(l10n), child: Text(l10n.acceptSaleButton)),
            if (nextTarget != null)
              ElevatedButton(
                onPressed: () => _advanceSale(nextTarget, l10n),
                child: Text('${l10n.advanceSaleButton} ${saleStatusLabel(nextTarget, l10n)}'),
              ),
            if (_cancellableStatuses.contains(sale.status))
              OutlinedButton(onPressed: () => _showCancelSheet(l10n), child: Text(l10n.cancelSaleButton)),
            if (_disputableStatuses.contains(sale.status))
              OutlinedButton(onPressed: () => _showDisputeSheet(l10n), child: Text(l10n.fileDisputeButton)),
            OutlinedButton(onPressed: () => _showFeedbackSheet(l10n), child: Text(l10n.leaveFeedbackButton)),
          ],
        ),
      ],
    );
  }
}
