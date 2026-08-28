import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

/// Shared between OrderListScreen and OrderDetailScreen so the two views
/// of a DealerOrder's status never drift apart. Mirrors the backend's 16
/// real OrderStatus values exactly - never a fabricated state.
Color orderStatusColor(String status) {
  switch (status) {
    case 'draft':
      return Colors.grey;
    case 'pending_confirmation':
      return Colors.blueGrey;
    case 'confirmed':
      return Colors.blue;
    case 'payment_pending':
      return Colors.amber;
    case 'paid':
      return Colors.green;
    case 'accepted_by_dealer':
      return Colors.indigo;
    case 'preparing':
      return Colors.deepPurple;
    case 'ready_for_dispatch':
      return Colors.teal;
    case 'dispatched':
      return Colors.cyan;
    case 'out_for_delivery':
      return Colors.lightBlue;
    case 'delivered':
      return Colors.lightGreen;
    case 'cancelled':
      return Colors.red;
    case 'rejected':
      return Colors.red;
    case 'refund_pending':
      return Colors.orange;
    case 'refunded':
      return Colors.brown;
    case 'disputed':
      return Colors.deepOrange;
    default:
      return Colors.grey;
  }
}

String orderStatusLabel(String status, AppLocalizations l10n) {
  switch (status) {
    case 'draft':
      return l10n.orderStatusDraftLabel;
    case 'pending_confirmation':
      return l10n.orderStatusPendingConfirmationLabel;
    case 'confirmed':
      return l10n.orderStatusConfirmedLabel;
    case 'payment_pending':
      return l10n.orderStatusPaymentPendingLabel;
    case 'paid':
      return l10n.orderStatusPaidLabel;
    case 'accepted_by_dealer':
      return l10n.orderStatusAcceptedByDealerLabel;
    case 'preparing':
      return l10n.orderStatusPreparingLabel;
    case 'ready_for_dispatch':
      return l10n.orderStatusReadyForDispatchLabel;
    case 'dispatched':
      return l10n.orderStatusDispatchedLabel;
    case 'out_for_delivery':
      return l10n.orderStatusOutForDeliveryLabel;
    case 'delivered':
      return l10n.orderStatusDeliveredLabel;
    case 'cancelled':
      return l10n.orderStatusCancelledLabel;
    case 'rejected':
      return l10n.orderStatusRejectedLabel;
    case 'refund_pending':
      return l10n.orderStatusRefundPendingLabel;
    case 'refunded':
      return l10n.orderStatusRefundedLabel;
    case 'disputed':
      return l10n.orderStatusDisputedLabel;
    default:
      return status;
  }
}
