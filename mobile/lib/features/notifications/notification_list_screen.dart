import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'notification_models.dart';
import 'notification_preferences_screen.dart';
import 'notification_repository.dart';

const Map<String, IconData> _categoryIcons = {
  'weather_alert': Icons.cloud_outlined,
  'rain_alert': Icons.water_drop_outlined,
  'heavy_rain_alert': Icons.thunderstorm_outlined,
  'crop_alert': Icons.grass_outlined,
  'disease_alert': Icons.coronavirus_outlined,
  'harvest_alert': Icons.agriculture_outlined,
};

/// No push notifications or polling exist anywhere in this project (a
/// disclosed limitation reused from the Expert Case / Weather features) -
/// this screen is a manual pull-to-refresh list, same convention as
/// every other feature screen here.
class NotificationListScreen extends StatefulWidget {
  const NotificationListScreen({super.key});

  @override
  State<NotificationListScreen> createState() => _NotificationListScreenState();
}

class _NotificationListScreenState extends State<NotificationListScreen> {
  NotificationPage? _page;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await context.read<NotificationRepository>().listNotifications();
      if (!mounted) return;
      setState(() {
        _page = page;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  Future<void> _openNotification(AppNotification notification) async {
    if (notification.isUnread) {
      try {
        await context.read<NotificationRepository>().markRead(notification.id);
        await _load();
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
      }
    }
  }

  Future<void> _markAllRead() async {
    try {
      await context.read<NotificationRepository>().markAllRead();
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final unreadCount = _page?.unreadCount ?? 0;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          if (unreadCount > 0)
            TextButton(
              onPressed: _markAllRead,
              child: const Text('Mark all read', style: TextStyle(color: Colors.white)),
            ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Preferences',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const NotificationPreferencesScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(child: Text(_error!)),
          const SizedBox(height: 12),
          Center(child: ElevatedButton(onPressed: _load, child: const Text('Try again'))),
        ],
      );
    }

    final items = _page!.items;
    if (items.isEmpty) {
      return ListView(
        children: const [SizedBox(height: 100), Center(child: Text('No notifications yet.'))],
      );
    }

    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, index) => _buildTile(items[index]),
    );
  }

  Widget _buildTile(AppNotification notification) {
    return ListTile(
      leading: Icon(_categoryIcons[notification.category] ?? Icons.notifications_outlined),
      title: Text(
        notification.title,
        style: TextStyle(fontWeight: notification.isUnread ? FontWeight.bold : FontWeight.normal),
      ),
      subtitle: Text(notification.body),
      trailing: notification.isUnread
          ? Container(width: 10, height: 10, decoration: const BoxDecoration(color: Colors.blue, shape: BoxShape.circle))
          : null,
      onTap: () => _openNotification(notification),
    );
  }
}
