import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import 'add_edit_farm_screen.dart';
import 'farm_models.dart';
import 'farm_details_screen.dart';
import 'farm_repository.dart';

/// Home -> My Farms. A farmer may own multiple farms - shown as a simple
/// list, each tile opening Farm Details.
class MyFarmsScreen extends StatefulWidget {
  const MyFarmsScreen({super.key});

  @override
  State<MyFarmsScreen> createState() => _MyFarmsScreenState();
}

class _MyFarmsScreenState extends State<MyFarmsScreen> {
  late Future<List<Farm>> _farmsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _farmsFuture = context.read<FarmRepository>().listMyFarms();
  }

  Future<void> _refresh() async {
    setState(_load);
    await _farmsFuture;
  }

  Future<void> _addFarm() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const AddEditFarmScreen()),
    );
    if (created == true) _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Farms')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addFarm,
        icon: const Icon(Icons.add),
        label: const Text('Add Farm'),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Farm>>(
          future: _farmsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _ErrorView(error: snapshot.error!, onRetry: _refresh);
            }
            final farms = snapshot.data ?? [];
            if (farms.isEmpty) {
              return ListView(
                children: const [
                  SizedBox(height: 80),
                  Center(child: Icon(Icons.grass, size: 64, color: Colors.grey)),
                  SizedBox(height: 16),
                  Center(child: Text('No farms yet. Tap "Add Farm" to get started.')),
                ],
              );
            }
            return ListView.builder(
              itemCount: farms.length,
              itemBuilder: (context, index) {
                final farm = farms[index];
                return ListTile(
                  leading: const Icon(Icons.grass, size: 32),
                  title: Text(farm.farmName, style: const TextStyle(fontSize: 18)),
                  subtitle: Text('${farm.areaValue} ${farm.areaUnit}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    await Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => FarmDetailsScreen(farmId: farm.id)),
                    );
                    _refresh();
                  },
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final Object error;
  final Future<void> Function() onRetry;
  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(FriendlyError.from(error)),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    );
  }
}
