/// Data models mirroring backend/app/schemas/{farm,plot,crop}.py. Kept as
/// plain classes with fromJson factories - no code-gen dependency, matches
/// the pattern already used by FarmerProfile.
library;

class Farm {
  final String id;
  final String farmName;
  final String? description;
  final double? latitude;
  final double? longitude;
  final int? stateId;
  final int? districtId;
  final int? mandalId;
  final int? villageId;
  final String? stateName;
  final String? districtName;
  final String? mandalName;
  final String? villageName;
  final double areaValue;
  final String areaUnit;
  final String status;

  Farm({
    required this.id,
    required this.farmName,
    this.description,
    this.latitude,
    this.longitude,
    this.stateId,
    this.districtId,
    this.mandalId,
    this.villageId,
    this.stateName,
    this.districtName,
    this.mandalName,
    this.villageName,
    required this.areaValue,
    required this.areaUnit,
    required this.status,
  });

  factory Farm.fromJson(Map<String, dynamic> json) => Farm(
        id: json['id'] as String,
        farmName: json['farm_name'] as String,
        description: json['description'] as String?,
        latitude: json['latitude'] != null ? double.parse(json['latitude'].toString()) : null,
        longitude: json['longitude'] != null ? double.parse(json['longitude'].toString()) : null,
        stateId: json['state_id'] as int?,
        districtId: json['district_id'] as int?,
        mandalId: json['mandal_id'] as int?,
        villageId: json['village_id'] as int?,
        stateName: json['state_name'] as String?,
        districtName: json['district_name'] as String?,
        mandalName: json['mandal_name'] as String?,
        villageName: json['village_name'] as String?,
        areaValue: double.parse(json['area_value'].toString()),
        areaUnit: json['area_unit'] as String,
        status: json['status'] as String,
      );
}

class Plot {
  final String id;
  final String farmId;
  final String plotName;
  final double areaValue;
  final String areaUnit;
  final String? soilType;
  final String? irrigationType;
  final String status;

  Plot({
    required this.id,
    required this.farmId,
    required this.plotName,
    required this.areaValue,
    required this.areaUnit,
    this.soilType,
    this.irrigationType,
    required this.status,
  });

  factory Plot.fromJson(Map<String, dynamic> json) => Plot(
        id: json['id'] as String,
        farmId: json['farm_id'] as String,
        plotName: json['plot_name'] as String,
        areaValue: double.parse(json['area_value'].toString()),
        areaUnit: json['area_unit'] as String,
        soilType: json['soil_type'] as String?,
        irrigationType: json['irrigation_type'] as String?,
        status: json['status'] as String,
      );
}

class CropMaster {
  final String id;
  final String name;
  final String? category;

  CropMaster({required this.id, required this.name, this.category});

  factory CropMaster.fromJson(Map<String, dynamic> json) =>
      CropMaster(id: json['id'] as String, name: json['name'] as String, category: json['category'] as String?);
}

class CropCycle {
  final String id;
  final String plotId;
  final CropMaster crop;
  final String? season;
  final String sowingDate;
  final String? expectedHarvestDate;
  final String? actualHarvestDate;
  final String cultivationStatus;
  final String? seedVariety;

  CropCycle({
    required this.id,
    required this.plotId,
    required this.crop,
    this.season,
    required this.sowingDate,
    this.expectedHarvestDate,
    this.actualHarvestDate,
    required this.cultivationStatus,
    this.seedVariety,
  });

  factory CropCycle.fromJson(Map<String, dynamic> json) => CropCycle(
        id: json['id'] as String,
        plotId: json['plot_id'] as String,
        crop: CropMaster.fromJson(json['crop'] as Map<String, dynamic>),
        season: json['season'] as String?,
        sowingDate: json['sowing_date'] as String,
        expectedHarvestDate: json['expected_harvest_date'] as String?,
        actualHarvestDate: json['actual_harvest_date'] as String?,
        cultivationStatus: json['cultivation_status'] as String,
        seedVariety: json['seed_variety'] as String?,
      );
}

/// Forward-only path, mirrors backend/app/models/crop_cycle.py's
/// ALLOWED_TRANSITIONS exactly - kept in sync manually since Flutter and
/// Python don't share a schema-generation step in this project. Used only
/// to decide which "advance to..." button to show; the backend is still
/// the actual enforcement point.
const List<String> cultivationStatusOrder = [
  'planned',
  'sown',
  'growing',
  'flowering',
  'fruiting',
  'ready_for_harvest',
  'harvested',
];

String? nextStatusAfter(String current) {
  final index = cultivationStatusOrder.indexOf(current);
  if (index == -1 || index >= cultivationStatusOrder.length - 1) return null;
  return cultivationStatusOrder[index + 1];
}
