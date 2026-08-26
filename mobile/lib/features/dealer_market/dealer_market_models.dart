/// Mirrors backend/app/schemas/{product,price,order}.py exactly. Decimal
/// fields are transmitted by the backend as JSON strings/numbers - kept
/// as String here (never `double.parse`d for money), same convention as
/// market_models.dart/harvest_models.dart. `status` is always the
/// backend's own raw enum string, never recomputed client-side.
///
/// Only the farmer-facing subset of the real 20-endpoint products/orders
/// contract is modeled here - dealer-role and admin-role endpoints
/// (create listing, accept/advance order, resolve dispute) have no
/// consumer anywhere in this app, matching the established farmer-only
/// persona boundary (no dealer/admin login UI exists).
library;

class Product {
  final String id;
  final String name;
  final String category;
  final String? manufacturer;
  final List<String> activeIngredients;
  final String packSizeValue;
  final String packSizeUnit;
  final String? description;
  final String? usageInformation;
  final String status;

  Product({
    required this.id,
    required this.name,
    required this.category,
    this.manufacturer,
    required this.activeIngredients,
    required this.packSizeValue,
    required this.packSizeUnit,
    this.description,
    this.usageInformation,
    required this.status,
  });

  factory Product.fromJson(Map<String, dynamic> json) => Product(
        id: json['id'] as String,
        name: json['name'] as String,
        category: json['category'] as String,
        manufacturer: json['manufacturer'] as String?,
        activeIngredients: (json['active_ingredients'] as List?)?.cast<String>() ?? [],
        packSizeValue: json['pack_size_value'].toString(),
        packSizeUnit: json['pack_size_unit'] as String,
        description: json['description'] as String?,
        usageInformation: json['usage_information'] as String?,
        status: json['status'] as String,
      );
}

const List<String> productCategoryOptions = [
  'seed',
  'fertilizer',
  'bio_input',
  'pest_control_product',
  'crop_protection_product',
  'equipment',
  'other_agricultural_input',
];

/// A single dealer's real, live offer to sell a product - from
/// PriceComparisonResponse.offers (GET /products/{id}/compare). This is
/// the only place a `dealer_product_id` (the id actually needed to add
/// to cart) is ever surfaced to a farmer.
class DealerOffer {
  final String dealerProductId;
  final String dealerId;
  final String dealerPrice;
  final String pricePerUnit;
  final String unit;
  final int stockQuantity;
  final bool isAvailable;

  DealerOffer({
    required this.dealerProductId,
    required this.dealerId,
    required this.dealerPrice,
    required this.pricePerUnit,
    required this.unit,
    required this.stockQuantity,
    required this.isAvailable,
  });

  factory DealerOffer.fromJson(Map<String, dynamic> json) => DealerOffer(
        dealerProductId: json['dealer_product_id'] as String,
        dealerId: json['dealer_id'] as String,
        dealerPrice: json['dealer_price'].toString(),
        pricePerUnit: json['price_per_unit'].toString(),
        unit: json['unit'] as String,
        stockQuantity: json['stock_quantity'] as int,
        isAvailable: json['is_available'] as bool,
      );
}

class PriceComparison {
  final String productId;
  final String? referencePrice;
  final String? referencePricePerUnit;
  final String? referenceSource;
  final List<DealerOffer> offers;

  PriceComparison({
    required this.productId,
    this.referencePrice,
    this.referencePricePerUnit,
    this.referenceSource,
    required this.offers,
  });

  factory PriceComparison.fromJson(Map<String, dynamic> json) => PriceComparison(
        productId: json['product_id'] as String,
        referencePrice: json['reference_price']?.toString(),
        referencePricePerUnit: json['reference_price_per_unit']?.toString(),
        referenceSource: json['reference_source'] as String?,
        offers: (json['offers'] as List).cast<Map<String, dynamic>>().map(DealerOffer.fromJson).toList(),
      );
}

/// `anomalyLevel` is null when the backend genuinely found nothing
/// unusual - never rendered as a fabricated "normal" badge, just the
/// absence of a warning.
class ScamShieldStatus {
  final String dealerProductId;
  final String pricePerUnit;
  final String? referencePricePerUnit;
  final double? percentAboveReference;
  final String? anomalyLevel;
  final String message;

  ScamShieldStatus({
    required this.dealerProductId,
    required this.pricePerUnit,
    this.referencePricePerUnit,
    this.percentAboveReference,
    this.anomalyLevel,
    required this.message,
  });

  factory ScamShieldStatus.fromJson(Map<String, dynamic> json) => ScamShieldStatus(
        dealerProductId: json['dealer_product_id'] as String,
        pricePerUnit: json['price_per_unit'].toString(),
        referencePricePerUnit: json['reference_price_per_unit']?.toString(),
        percentAboveReference: (json['percent_above_reference'] as num?)?.toDouble(),
        anomalyLevel: json['anomaly_level'] as String?,
        message: json['message'] as String,
      );
}

class DealerOrderItem {
  final String id;
  final String dealerProductId;
  final String productNameSnapshot;
  final int quantity;
  final String? unitPrice;
  final String? finalItemAmount;

  DealerOrderItem({
    required this.id,
    required this.dealerProductId,
    required this.productNameSnapshot,
    required this.quantity,
    this.unitPrice,
    this.finalItemAmount,
  });

  factory DealerOrderItem.fromJson(Map<String, dynamic> json) => DealerOrderItem(
        id: json['id'] as String,
        dealerProductId: json['dealer_product_id'] as String,
        productNameSnapshot: json['product_name_snapshot'] as String,
        quantity: json['quantity'] as int,
        unitPrice: json['unit_price']?.toString(),
        finalItemAmount: json['final_item_amount']?.toString(),
      );
}

/// Mirrors OrderResponse. Named `DealerOrder` (not `Order`) to keep this
/// input-purchase order distinct from the harvest-sale `SaleOrder` model
/// in market_models.dart - two genuinely different backends/domains.
/// Money fields stay null while status is `draft` (the cart) - the
/// backend never computes a subtotal until real checkout, so this model
/// never fabricates one either.
class DealerOrder {
  final String id;
  final String dealerId;
  final String status;
  final String? subtotalAmount;
  final String? discountAmount;
  final String? deliveryFeeAmount;
  final String? taxAmount;
  final String? finalAmount;
  final String? rejectionReason;
  final List<DealerOrderItem> items;
  final String createdAt;

  DealerOrder({
    required this.id,
    required this.dealerId,
    required this.status,
    this.subtotalAmount,
    this.discountAmount,
    this.deliveryFeeAmount,
    this.taxAmount,
    this.finalAmount,
    this.rejectionReason,
    required this.items,
    required this.createdAt,
  });

  factory DealerOrder.fromJson(Map<String, dynamic> json) => DealerOrder(
        id: json['id'] as String,
        dealerId: json['dealer_id'] as String,
        status: json['status'] as String,
        subtotalAmount: json['subtotal_amount']?.toString(),
        discountAmount: json['discount_amount']?.toString(),
        deliveryFeeAmount: json['delivery_fee_amount']?.toString(),
        taxAmount: json['tax_amount']?.toString(),
        finalAmount: json['final_amount']?.toString(),
        rejectionReason: json['rejection_reason'] as String?,
        items: (json['items'] as List).cast<Map<String, dynamic>>().map(DealerOrderItem.fromJson).toList(),
        createdAt: json['created_at'] as String,
      );
}

/// Statuses (and their real, order-model-defined forward transitions)
/// where a farmer can still cancel - mirrors ALLOWED_ORDER_TRANSITIONS'
/// own CANCELLED targets exactly, never invented.
const Set<String> cancellableOrderStatuses = {
  'draft',
  'pending_confirmation',
  'confirmed',
  'payment_pending',
  'accepted_by_dealer',
};

/// Mirrors DisputeReason exactly.
const List<String> orderDisputeReasons = [
  'wrong_product',
  'missing_item',
  'damaged_product',
  'payment_issue',
  'delivery_issue',
  'unexpected_charge',
  'product_authenticity_concern',
];

class DealerOrderDispute {
  final String id;
  final String orderId;
  final String reason;
  final String status;
  final String createdAt;

  DealerOrderDispute({required this.id, required this.orderId, required this.reason, required this.status, required this.createdAt});

  factory DealerOrderDispute.fromJson(Map<String, dynamic> json) => DealerOrderDispute(
        id: json['id'] as String,
        orderId: json['order_id'] as String,
        reason: json['reason'] as String,
        status: json['status'] as String,
        createdAt: json['created_at'] as String,
      );
}

class DealerDelivery {
  final String id;
  final String orderId;
  final String status;
  final String? estimatedDeliveryDate;
  final String? trackingNote;

  DealerDelivery({required this.id, required this.orderId, required this.status, this.estimatedDeliveryDate, this.trackingNote});

  factory DealerDelivery.fromJson(Map<String, dynamic> json) => DealerDelivery(
        id: json['id'] as String,
        orderId: json['order_id'] as String,
        status: json['status'] as String,
        estimatedDeliveryDate: json['estimated_delivery_date'] as String?,
        trackingNote: json['tracking_note'] as String?,
      );
}
