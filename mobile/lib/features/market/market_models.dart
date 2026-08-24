/// Mirrors backend/app/schemas/marketplace.py exactly. Decimal fields
/// (quantity, price_per_unit, gross_value, charges, net_value) are
/// transmitted by the backend as JSON strings, not numbers - kept as
/// String here, same convention as harvest_models.dart, so nothing is
/// ever displayed with fabricated precision. `status` is always the
/// backend's own raw enum string, never recomputed. There is no farmer
/// or buyer display name anywhere in this contract - only UUIDs -
/// matching what the backend actually provides, not fabricated.
library;

class Offer {
  final String id;
  final String harvestListingId;
  final String buyerId;
  final String quantity;
  final String unit;
  final String pricePerUnit;
  final String status;
  final String createdAt;

  Offer({
    required this.id,
    required this.harvestListingId,
    required this.buyerId,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.status,
    required this.createdAt,
  });

  factory Offer.fromJson(Map<String, dynamic> json) => Offer(
        id: json['id'] as String,
        harvestListingId: json['harvest_listing_id'] as String,
        buyerId: json['buyer_id'] as String,
        quantity: json['quantity'] as String,
        unit: json['unit'] as String,
        pricePerUnit: json['price_per_unit'] as String,
        status: json['status'] as String,
        createdAt: json['created_at'] as String,
      );
}

class CounterOffer {
  final String id;
  final String buyerOfferId;
  final String proposedBy;
  final String pricePerUnit;
  final String quantity;
  final String? message;
  final String createdAt;

  CounterOffer({
    required this.id,
    required this.buyerOfferId,
    required this.proposedBy,
    required this.pricePerUnit,
    required this.quantity,
    this.message,
    required this.createdAt,
  });

  factory CounterOffer.fromJson(Map<String, dynamic> json) => CounterOffer(
        id: json['id'] as String,
        buyerOfferId: json['buyer_offer_id'] as String,
        proposedBy: json['proposed_by'] as String,
        pricePerUnit: json['price_per_unit'] as String,
        quantity: json['quantity'] as String,
        message: json['message'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class SaleOrder {
  final String id;
  final String harvestListingId;
  final String buyerId;
  final String cropId;
  final String quantity;
  final String unit;
  final String pricePerUnit;
  final String grossValue;
  final String charges;
  final String netValue;
  final String collectionMethod;
  final String status;
  final String? cancellationReason;
  final String createdAt;

  SaleOrder({
    required this.id,
    required this.harvestListingId,
    required this.buyerId,
    required this.cropId,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.grossValue,
    required this.charges,
    required this.netValue,
    required this.collectionMethod,
    required this.status,
    this.cancellationReason,
    required this.createdAt,
  });

  factory SaleOrder.fromJson(Map<String, dynamic> json) => SaleOrder(
        id: json['id'] as String,
        harvestListingId: json['harvest_listing_id'] as String,
        buyerId: json['buyer_id'] as String,
        cropId: json['crop_id'] as String,
        quantity: json['quantity'] as String,
        unit: json['unit'] as String,
        pricePerUnit: json['price_per_unit'] as String,
        grossValue: json['gross_value'] as String,
        charges: json['charges'] as String,
        netValue: json['net_value'] as String,
        collectionMethod: json['collection_method'] as String,
        status: json['status'] as String,
        cancellationReason: json['cancellation_reason'] as String?,
        createdAt: json['created_at'] as String,
      );
}
