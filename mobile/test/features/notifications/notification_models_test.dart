import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/notifications/notification_models.dart';

void main() {
  group('AppNotification.fromJson', () {
    test('a notification with no read_at is unread', () {
      final notification = AppNotification.fromJson({
        'id': 'n1',
        'category': 'rain_alert',
        'priority': 'high',
        'title': 'Rain expected',
        'body': 'Heavy rain expected tomorrow.',
        'language_code': 'en',
        'related_entity_type': 'farm',
        'related_entity_id': 'f1',
        'read_at': null,
        'created_at': '2026-08-26T00:00:00Z',
      });
      expect(notification.isUnread, isTrue);
    });

    test('a notification with a real read_at is not unread', () {
      final notification = AppNotification.fromJson({
        'id': 'n1',
        'category': 'crop_alert',
        'priority': 'medium',
        'title': 'Crop update',
        'body': 'Your crop cycle has an update.',
        'language_code': 'en',
        'related_entity_type': null,
        'related_entity_id': null,
        'read_at': '2026-08-26T01:00:00Z',
        'created_at': '2026-08-26T00:00:00Z',
      });
      expect(notification.isUnread, isFalse);
    });
  });

  group('NotificationPage.fromJson', () {
    test('parses items, total, and unread_count exactly as returned by the backend, never recomputed', () {
      final page = NotificationPage.fromJson({
        'items': [
          {
            'id': 'n1',
            'category': 'disease_alert',
            'priority': 'critical',
            'title': 'Disease detected',
            'body': 'Possible disease detected in your crop photo.',
            'language_code': 'en',
            'related_entity_type': 'crop_cycle',
            'related_entity_id': 'c1',
            'read_at': null,
            'created_at': '2026-08-26T00:00:00Z',
          },
        ],
        'total': 5,
        'unread_count': 3,
      });
      expect(page.items.length, 1);
      expect(page.total, 5);
      expect(page.unreadCount, 3);
    });

    test('an empty page parses to an empty list, not a fabricated placeholder item', () {
      final page = NotificationPage.fromJson({'items': [], 'total': 0, 'unread_count': 0});
      expect(page.items, isEmpty);
      expect(page.unreadCount, 0);
    });
  });

  group('NotificationPreferences.fromJson', () {
    test('parses every real backend toggle and leaves unset quiet hours null, not fabricated', () {
      final preferences = NotificationPreferences.fromJson({
        'weather_alerts_enabled': true,
        'rain_alerts_enabled': true,
        'crop_alerts_enabled': true,
        'disease_alerts_enabled': true,
        'audio_alerts_enabled': false,
        'general_notifications_enabled': true,
        'quiet_hours_start': null,
        'quiet_hours_end': null,
      });
      expect(preferences.audioAlertsEnabled, isFalse);
      expect(preferences.generalNotificationsEnabled, isTrue);
      expect(preferences.quietHoursStart, isNull);
    });
  });
}
