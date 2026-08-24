/// Mirrors backend/app/schemas/harvest.py and app/models/harvest_record.py
/// / harvest_listing.py exactly. `status` and `deliveryOption` are kept as
/// the backend's own raw enum strings (never recomputed) - the 8 real
/// HarvestStatus values are: planned, approaching, ready, harvested,
/// listed, partially_sold, sold, cancelled. The 3 real CollectionOption
/// values are: buyer_collection, farmer_delivery, third_party_logistics.
/// Decimal fields (estimated_quantity, actual_quantity, quantity_available,
/// preferred_price) are transmitted by the backend as JSON strings, not
/// numbers - kept as String here rather than parsed to double, so nothing
/// is ever displayed with fabricated precision.
library;

class HarvestRecord {
  final String id;
  final String cropCycleId;
  final String cropId;
  final String? expectedHarvestDate;
  final String? actualHarvestDate;
  final String? estimatedQuantity;
  final String? actualQuantity;
  final String unit;
  final String? qualityGrade;
  final String status;
  final String createdAt;

  HarvestRecord({
    required this.id,
    required this.cropCycleId,
    required this.cropId,
    this.expectedHarvestDate,
    this.actualHarvestDate,
    this.estimatedQuantity,
    this.actualQuantity,
    required this.unit,
    this.qualityGrade,
    required this.status,
    required this.createdAt,
  });

  factory HarvestRecord.fromJson(Map<String, dynamic> json) => HarvestRecord(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        cropId: json['crop_id'] as String,
        expectedHarvestDate: json['expected_harvest_date'] as String?,
        actualHarvestDate: json['actual_harvest_date'] as String?,
        estimatedQuantity: json['estimated_quantity'] as String?,
        actualQuantity: json['actual_quantity'] as String?,
        unit: json['unit'] as String,
        qualityGrade: json['quality_grade'] as String?,
        status: json['status'] as String,
        createdAt: json['created_at'] as String,
      );
}

class HarvestListing {
  final String id;
  final String harvestRecordId;
  final String cropId;
  final String quantityAvailable;
  final String unit;
  final String? qualityGrade;
  final String? expectedAvailabilityDate;
  final Map<String, dynamic>? serviceArea;
  final String? preferredPrice;
  final String deliveryOption;
  final bool isActive;
  final String createdAt;

  HarvestListing({
    required this.id,
    required this.harvestRecordId,
    required this.cropId,
    required this.quantityAvailable,
    required this.unit,
    this.qualityGrade,
    this.expectedAvailabilityDate,
    this.serviceArea,
    this.preferredPrice,
    required this.deliveryOption,
    required this.isActive,
    required this.createdAt,
  });

  factory HarvestListing.fromJson(Map<String, dynamic> json) => HarvestListing(
        id: json['id'] as String,
        harvestRecordId: json['harvest_record_id'] as String,
        cropId: json['crop_id'] as String,
        quantityAvailable: json['quantity_available'] as String,
        unit: json['unit'] as String,
        qualityGrade: json['quality_grade'] as String?,
        expectedAvailabilityDate: json['expected_availability_date'] as String?,
        serviceArea: json['service_area'] as Map<String, dynamic>?,
        preferredPrice: json['preferred_price'] as String?,
        deliveryOption: json['delivery_option'] as String,
        isActive: json['is_active'] as bool,
        createdAt: json['created_at'] as String,
      );
}
