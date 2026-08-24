import 'package:flutter/material.dart';

import 'screens/assistant_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/home_screen.dart';
import 'features/farm/my_farms_screen.dart';
import 'features/market/market_screen.dart';
import 'screens/profile_screen.dart';

/// The 6-tab navigation shell (Home / Camera / My Farm / Market /
/// Assistant / Profile) per the simplified navigation principle in the
/// approved UX spec. "My Farm" opens the real Farm/Plot/Crop flow
/// (MyFarmsScreen); "Market" opens the real farmer-side offer/sale
/// management flow (MarketScreen); Camera and Assistant remain
/// placeholders - see PROJECT_STATUS.md for implementation order.
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
    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.camera_alt), label: 'Camera'),
          NavigationDestination(icon: Icon(Icons.grass), label: 'My Farm'),
          NavigationDestination(icon: Icon(Icons.storefront), label: 'Market'),
          NavigationDestination(icon: Icon(Icons.mic), label: 'Assistant'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
