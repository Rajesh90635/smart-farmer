import '../../core/api_client.dart';
import 'notification_models.dart';

class NotificationRepository {
  final ApiClient _apiClient;
  NotificationRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<NotificationPage> listNotifications({bool unreadOnly = false, int limit = 50, int offset = 0}) async {
    final response =
        await _apiClient.get('/notifications?unread_only=$unreadOnly&limit=$limit&offset=$offset');
    return NotificationPage.fromJson(response);
  }

  Future<AppNotification> markRead(String notificationId) async {
    final response = await _apiClient.post('/notifications/$notificationId/read');
    return AppNotification.fromJson(response);
  }

  Future<int> markAllRead() async {
    final response = await _apiClient.post('/notifications/read-all');
    return response['marked_read'] as int;
  }

  Future<NotificationPreferences> getPreferences() async {
    final response = await _apiClient.get('/notification-preferences');
    return NotificationPreferences.fromJson(response);
  }

  Future<NotificationPreferences> updatePreferences({
    bool? weatherAlertsEnabled,
    bool? rainAlertsEnabled,
    bool? cropAlertsEnabled,
    bool? diseaseAlertsEnabled,
    bool? audioAlertsEnabled,
    bool? generalNotificationsEnabled,
  }) async {
    final response = await _apiClient.put('/notification-preferences', body: {
      if (weatherAlertsEnabled != null) 'weather_alerts_enabled': weatherAlertsEnabled,
      if (rainAlertsEnabled != null) 'rain_alerts_enabled': rainAlertsEnabled,
      if (cropAlertsEnabled != null) 'crop_alerts_enabled': cropAlertsEnabled,
      if (diseaseAlertsEnabled != null) 'disease_alerts_enabled': diseaseAlertsEnabled,
      if (audioAlertsEnabled != null) 'audio_alerts_enabled': audioAlertsEnabled,
      if (generalNotificationsEnabled != null) 'general_notifications_enabled': generalNotificationsEnabled,
    });
    return NotificationPreferences.fromJson(response);
  }
}
