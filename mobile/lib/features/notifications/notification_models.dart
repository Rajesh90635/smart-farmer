/// Mirrors backend/app/schemas/notification.py exactly. Named
/// `AppNotification` (not `Notification`) to avoid colliding with
/// Flutter's own `Notification` widget-event class.
///
/// `title`/`body` are already rendered server-side in the farmer's own
/// language at creation time (see the backend model's own doc comment) -
/// this Flutter layer renders them verbatim, never recomposes them.
library;

class AppNotification {
  final String id;
  final String category;
  final String priority;
  final String title;
  final String body;
  final String languageCode;
  final String? relatedEntityType;
  final String? relatedEntityId;
  final String? readAt;
  final String createdAt;

  AppNotification({
    required this.id,
    required this.category,
    required this.priority,
    required this.title,
    required this.body,
    required this.languageCode,
    this.relatedEntityType,
    this.relatedEntityId,
    this.readAt,
    required this.createdAt,
  });

  bool get isUnread => readAt == null;

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: json['id'] as String,
        category: json['category'] as String,
        priority: json['priority'] as String,
        title: json['title'] as String,
        body: json['body'] as String,
        languageCode: json['language_code'] as String,
        relatedEntityType: json['related_entity_type'] as String?,
        relatedEntityId: json['related_entity_id'] as String?,
        readAt: json['read_at'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class NotificationPage {
  final List<AppNotification> items;
  final int total;
  final int unreadCount;

  NotificationPage({required this.items, required this.total, required this.unreadCount});

  factory NotificationPage.fromJson(Map<String, dynamic> json) => NotificationPage(
        items: (json['items'] as List).cast<Map<String, dynamic>>().map(AppNotification.fromJson).toList(),
        total: json['total'] as int,
        unreadCount: json['unread_count'] as int,
      );
}

class NotificationPreferences {
  final bool weatherAlertsEnabled;
  final bool rainAlertsEnabled;
  final bool cropAlertsEnabled;
  final bool diseaseAlertsEnabled;
  final bool audioAlertsEnabled;
  final bool generalNotificationsEnabled;
  final String? quietHoursStart;
  final String? quietHoursEnd;

  NotificationPreferences({
    required this.weatherAlertsEnabled,
    required this.rainAlertsEnabled,
    required this.cropAlertsEnabled,
    required this.diseaseAlertsEnabled,
    required this.audioAlertsEnabled,
    required this.generalNotificationsEnabled,
    this.quietHoursStart,
    this.quietHoursEnd,
  });

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) => NotificationPreferences(
        weatherAlertsEnabled: json['weather_alerts_enabled'] as bool,
        rainAlertsEnabled: json['rain_alerts_enabled'] as bool,
        cropAlertsEnabled: json['crop_alerts_enabled'] as bool,
        diseaseAlertsEnabled: json['disease_alerts_enabled'] as bool,
        audioAlertsEnabled: json['audio_alerts_enabled'] as bool,
        generalNotificationsEnabled: json['general_notifications_enabled'] as bool,
        quietHoursStart: json['quiet_hours_start'] as String?,
        quietHoursEnd: json['quiet_hours_end'] as String?,
      );
}
