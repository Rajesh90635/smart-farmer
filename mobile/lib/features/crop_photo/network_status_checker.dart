import 'package:connectivity_plus/connectivity_plus.dart';

/// Thin wrapper around connectivity_plus - the crop photo upload flow
/// needs a real, queryable "am I online right now" check (not just the
/// foundation-phase placeholder ConnectivityController, which was never
/// wired to a real plugin). Kept as a separate small class rather than
/// retrofitting the placeholder, so the foundation's documented
/// "not wired yet" status stays accurate for anything still using it.
class NetworkStatusChecker {
  final Connectivity _connectivity;
  NetworkStatusChecker({Connectivity? connectivity}) : _connectivity = connectivity ?? Connectivity();

  Future<bool> isOnline() async {
    final results = await _connectivity.checkConnectivity();
    return results.any((r) => r != ConnectivityResult.none);
  }

  Stream<bool> onStatusChange() {
    return _connectivity.onConnectivityChanged.map((results) => results.any((r) => r != ConnectivityResult.none));
  }
}
