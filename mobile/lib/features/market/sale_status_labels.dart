import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

/// Shared between SalesScreen and SaleDetailScreen so the two views of a
/// SaleOrder's status never drift apart. Mirrors the backend's 11 real
/// SaleOrderStatus values exactly - never a fabricated state.
Color saleStatusColor(String status) {
  switch (status) {
    case 'accepted':
      return Colors.blue;
    case 'preparing':
      return Colors.indigo;
    case 'ready_for_collection':
      return Colors.teal;
    case 'collected':
      return Colors.cyan;
    case 'in_transit':
      return Colors.deepPurple;
    case 'delivered':
      return Colors.lightGreen;
    case 'payment_pending':
      return Colors.amber;
    case 'paid':
      return Colors.green;
    case 'cancelled':
      return Colors.red;
    case 'disputed':
      return Colors.deepOrange;
    case 'completed':
      return Colors.green;
    default:
      return Colors.grey;
  }
}

String saleStatusLabel(String status, AppLocalizations l10n) {
  switch (status) {
    case 'accepted':
      return l10n.saleStatusAcceptedLabel;
    case 'preparing':
      return l10n.saleStatusPreparingLabel;
    case 'ready_for_collection':
      return l10n.saleStatusReadyForCollectionLabel;
    case 'collected':
      return l10n.saleStatusCollectedLabel;
    case 'in_transit':
      return l10n.saleStatusInTransitLabel;
    case 'delivered':
      return l10n.saleStatusDeliveredLabel;
    case 'payment_pending':
      return l10n.saleStatusPaymentPendingLabel;
    case 'paid':
      return l10n.saleStatusPaidLabel;
    case 'cancelled':
      return l10n.saleStatusCancelledLabel;
    case 'disputed':
      return l10n.saleStatusDisputedLabel;
    case 'completed':
      return l10n.saleStatusCompletedLabel;
    default:
      return l10n.saleStatusPendingLabel;
  }
}
