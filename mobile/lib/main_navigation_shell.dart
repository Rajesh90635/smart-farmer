import 'package:flutter/material.dart';

import 'features/assistant/assistant_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/home_screen.dart';
import 'features/farm/my_farms_screen.dart';
import 'features/market/market_screen.dart';
import 'screens/profile_screen.dart';
import 'l10n/app_localizations.dart';

/// The 6-tab navigation shell (Home / Camera / My Farm / Market /
/// Assistant / Profile) per the simplified navigation principle in the
/// approved UX spec. "My Farm" opens the real Farm/Plot/Crop flow
/// (MyFarmsScreen); "Market" opens the real farmer-side offer/sale
/// management flow (MarketScreen); "Assistant" opens the real,
/// persisted AI Assistant chat (AssistantScreen); "Camera" opens a
/// crop picker that hands off to the existing crop-photo capture flow
/// (CameraScreen) - all six tabs are now real, no placeholders remain.
class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _selectedIndex = 0;

  static const _screens = [
    HomeScreen(),
    CameraScreen(),
    MyFarmsScreen(),
    MarketScreen(),
    AssistantScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.home), label: l10n.navHome),
          NavigationDestination(icon: const Icon(Icons.camera_alt), label: l10n.navCamera),
          NavigationDestination(icon: const Icon(Icons.grass), label: l10n.navMyFarm),
          NavigationDestination(icon: const Icon(Icons.storefront), label: l10n.navMarket),
          NavigationDestination(icon: const Icon(Icons.mic), label: l10n.navAssistant),
          NavigationDestination(icon: const Icon(Icons.person), label: l10n.navProfile),
        ],
      ),
    );
  }
}
