import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../features/auth/auth_state.dart';
import '../features/crop_photo/sync_coordinator.dart';

/// Attempts to restore a previous session (via the stored refresh token)
/// before deciding whether to show Welcome/Login or go straight to Home -
/// this is the "automatic session restoration where appropriate" behavior.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _decideInitialRoute());
  }

  Future<void> _decideInitialRoute() async {
    final authState = context.read<AuthState>();
    await authState.restoreSession();

    // Offline-first media sync: restore any photos queued before the app
    // was last closed, and start listening for connectivity so they
    // upload automatically without the farmer needing to reopen the
    // exact screen they were captured from. Runs regardless of auth
    // outcome - a queued photo predates knowing whether the session is
    // still valid, and re-authentication (if needed) happens on the
    // upload call itself via the existing API client.
    if (mounted) {
      await initializeOfflineSync(context);
    }

    if (!mounted) return;

    final route = authState.status == AuthStatus.authenticated ? '/home' : '/welcome';
    Navigator.of(context).pushReplacementNamed(route);
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}
