import 'package:flutter/material.dart';

/// Foundation-phase connectivity architecture (Step 16).
///
/// This does NOT implement the full offline engine yet (local cache,
/// pending-sync queue, retry, conflict resolution - see
/// OFFLINE_ARCHITECTURE.md for the documented design). It establishes:
///   1. A ConnectivityStatus enum business code can depend on.
///   2. A banner widget every screen can show consistently when offline,
///      per the UX rule that offline state must always be visible, never
///      silent.
enum ConnectivityStatus { online, offline, unknown }

/// Placeholder notifier. Wiring this to a real connectivity plugin
/// (e.g. connectivity_plus) happens in the Offline-First epic - this
/// foundation only defines the contract other widgets should depend on.
class ConnectivityController extends ChangeNotifier {
  ConnectivityStatus _status = ConnectivityStatus.unknown;
  ConnectivityStatus get status => _status;

  void update(ConnectivityStatus status) {
    _status = status;
    notifyListeners();
  }
}

class OfflineBanner extends StatelessWidget {
  final ConnectivityStatus status;
  final String message;

  const OfflineBanner({super.key, required this.status, required this.message});

  @override
  Widget build(BuildContext context) {
    if (status != ConnectivityStatus.offline) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      color: Theme.of(context).colorScheme.errorContainer,
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Text(
        message,
        style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
        textAlign: TextAlign.center,
      ),
    );
  }
}
