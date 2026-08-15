/// Mirrors backend/app/schemas/weather.py exactly. `cropAction` is a
/// live re-evaluation of the SAME deterministic rule already used for
/// the background spray-condition notification - not a second rule, not
/// AI-generated. `null` covers both "conditions fine" and (when
/// `available` is false) "no data at all" - the outer `available` flag
/// is what a farmer-facing UI must check first to tell those apart.
library;

class WeatherReading {
  final double? temperatureC;
  final double? feelsLikeC;
  final double? temperatureMinC;
  final double? temperatureMaxC;
  final double? humidityPercent;
  final double? rainProbabilityPercent;
  final double? rainfallMm;
  final double? windSpeedKmh;
  final double? windDirectionDegrees;
  final String? conditionCode;

  WeatherReading({
    this.temperatureC,
    this.feelsLikeC,
    this.temperatureMinC,
    this.temperatureMaxC,
    this.humidityPercent,
    this.rainProbabilityPercent,
    this.rainfallMm,
    this.windSpeedKmh,
    this.windDirectionDegrees,
    this.conditionCode,
  });

  factory WeatherReading.fromJson(Map<String, dynamic> json) => WeatherReading(
        temperatureC: (json['temperature_c'] as num?)?.toDouble(),
        feelsLikeC: (json['feels_like_c'] as num?)?.toDouble(),
        temperatureMinC: (json['temperature_min_c'] as num?)?.toDouble(),
        temperatureMaxC: (json['temperature_max_c'] as num?)?.toDouble(),
        humidityPercent: (json['humidity_percent'] as num?)?.toDouble(),
        rainProbabilityPercent: (json['rain_probability_percent'] as num?)?.toDouble(),
        rainfallMm: (json['rainfall_mm'] as num?)?.toDouble(),
        windSpeedKmh: (json['wind_speed_kmh'] as num?)?.toDouble(),
        windDirectionDegrees: (json['wind_direction_degrees'] as num?)?.toDouble(),
        conditionCode: json['condition_code'] as String?,
      );
}

class ForecastDay {
  final String forecastDate;
  final WeatherReading reading;
  ForecastDay({required this.forecastDate, required this.reading});

  factory ForecastDay.fromJson(Map<String, dynamic> json) =>
      ForecastDay(forecastDate: json['forecast_date'] as String, reading: WeatherReading.fromJson(json['reading'] as Map<String, dynamic>));
}

/// `basis`/`action` are stable CODES, not free text - the farmer-facing
/// sentence is looked up from `reasonMessageKey` via the existing
/// localization system, never invented here, exactly like
/// qualityReasonMessageKeys/caseStatusMessageKeys elsewhere in this app.
class CropActionAdvisory {
  final String action;
  final String reasonMessageKey;
  final String basis;

  CropActionAdvisory({required this.action, required this.reasonMessageKey, required this.basis});

  factory CropActionAdvisory.fromJson(Map<String, dynamic> json) => CropActionAdvisory(
        action: json['action'] as String,
        reasonMessageKey: json['reason_message_key'] as String,
        basis: json['basis'] as String,
      );
}

class FarmWeather {
  final bool available;
  final String? provider;
  final String? unavailableReason;
  final bool isStale;
  final String? fetchedAt;
  final WeatherReading? current;
  final List<ForecastDay> forecast;
  final CropActionAdvisory? cropAction;

  FarmWeather({
    required this.available,
    this.provider,
    this.unavailableReason,
    required this.isStale,
    this.fetchedAt,
    this.current,
    required this.forecast,
    this.cropAction,
  });

  factory FarmWeather.fromJson(Map<String, dynamic> json) => FarmWeather(
        available: json['available'] as bool,
        provider: json['provider'] as String?,
        unavailableReason: json['unavailable_reason'] as String?,
        isStale: json['is_stale'] as bool? ?? false,
        fetchedAt: json['fetched_at'] as String?,
        current: json['current'] != null ? WeatherReading.fromJson(json['current'] as Map<String, dynamic>) : null,
        forecast: (json['forecast'] as List? ?? []).map((e) => ForecastDay.fromJson(e as Map<String, dynamic>)).toList(),
        cropAction: json['crop_action'] != null ? CropActionAdvisory.fromJson(json['crop_action'] as Map<String, dynamic>) : null,
      );
}

/// Maps the real backend message keys (farmer_messages.py) used by
/// crop_action.reason_message_key to farmer-friendly text. Only the one
/// key the implemented rule actually produces is mapped - no others
/// invented ahead of a rule that doesn't exist yet.
const Map<String, String> cropActionMessageKeys = {
  'spray_condition_warning': 'sprayConditionWarning',
};
