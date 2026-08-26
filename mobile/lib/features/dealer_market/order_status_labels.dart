import 'package:flutter/material.dart';

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

String orderStatusLabel(String status) => status.replaceAll('_', ' ').toUpperCase();
