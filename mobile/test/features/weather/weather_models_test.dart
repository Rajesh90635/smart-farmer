import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/weather/weather_models.dart';

void main() {
  group('FarmWeather (Step 15)', () {
    test('parses an available weather response with current + forecast, exactly as returned', () {
      final json = {
        'available': true,
        'provider': 'fake_test_provider',
        'is_stale': false,
        'fetched_at': '2026-01-01T06:00:00Z',
        'current': {'temperature_c': 28.0, 'humidity_percent': 60.0, 'wind_speed_kmh': 10.0},
        'forecast': [
          {
            'forecast_date': '2026-01-01',
            'reading': {'rain_probability_percent': 20.0},
          }
        ],
        'crop_action': null,
      };
      final weather = FarmWeather.fromJson(json);
      expect(weather.available, isTrue);
      expect(weather.current!.temperatureC, 28.0);
      expect(weather.forecast.length, 1);
      expect(weather.cropAction, isNull);
    });

    test('unavailable weather never carries a current reading, forecast, or crop action', () {
      final json = {
        'available': false,
        'unavailable_reason': 'Weather information is temporarily unavailable.',
        'is_stale': false,
        'forecast': [],
      };
      final weather = FarmWeather.fromJson(json);
      expect(weather.available, isFalse);
      expect(weather.current, isNull);
      expect(weather.cropAction, isNull);
      expect(weather.unavailableReason, isNotNull);
    });

    test('isStale flag is preserved distinctly from availability', () {
      final json = {
        'available': true,
        'is_stale': true,
        'fetched_at': '2026-01-01T00:00:00Z',
        'current': {'temperature_c': 25.0},
        'forecast': [],
      };
      final weather = FarmWeather.fromJson(json);
      expect(weather.available, isTrue);
      expect(weather.isStale, isTrue);
    });

    test('crop_action parses exactly the three real backend fields - no more, no less', () {
      final json = {
        'available': true,
        'is_stale': false,
        'current': {'wind_speed_kmh': 45.0},
        'forecast': [],
        'crop_action': {'action': 'avoid_spraying', 'reason_message_key': 'spray_condition_warning', 'basis': 'high_wind'},
      };
      final weather = FarmWeather.fromJson(json);
      expect(weather.cropAction!.action, 'avoid_spraying');
      expect(weather.cropAction!.reasonMessageKey, 'spray_condition_warning');
      expect(weather.cropAction!.basis, 'high_wind');
    });

    test('missing optional current-reading fields do not crash parsing', () {
      final json = {
        'available': true,
        'is_stale': false,
        'current': <String, dynamic>{},
        'forecast': [],
      };
      final weather = FarmWeather.fromJson(json);
      expect(weather.current!.temperatureC, isNull);
      expect(weather.current!.windSpeedKmh, isNull);
    });

    test('the one real crop-action message key maps correctly - none invented for an unimplemented rule', () {
      expect(cropActionMessageKeys['spray_condition_warning'], 'sprayConditionWarning');
      expect(cropActionMessageKeys.length, 1);
    });
  });
}
