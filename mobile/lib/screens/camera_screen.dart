import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/friendly_error.dart';
import '../features/crop_photo/crop_photo_list_screen.dart';
import '../features/farm/crop_repository.dart';
import '../features/farm/farm_models.dart';
import '../l10n/app_localizations.dart';

/// The Camera tab has no crop context of its own (unlike the identical
/// capture flow reached from a specific crop's details screen) - so its
/// only job is to let the farmer pick WHICH crop they're checking, then
/// hand off to the exact same, already-built CropPhotoListScreen. No
/// photo/session logic is duplicated here.
class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late Future<List<CropCycle>> _cyclesFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _cyclesFuture = context.read<CropRepository>().listAllMyCropCycles();
  }

  Future<void> _refresh() async {
    setState(_load);
    await _cyclesFuture;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.cameraTabTitle)),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<CropCycle>>(
          future: _cyclesFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ListView(
                children: [
                  const SizedBox(height: 80),
                  Center(child: Text(FriendlyError.from(snapshot.error!))),
                  const SizedBox(height: 12),
                  Center(child: ElevatedButton(onPressed: _refresh, child: Text(l10n.genericErrorRetry))),
                ],
              );
            }
            final cycles = snapshot.data ?? [];
            if (cycles.isEmpty) {
              return ListView(
                children: [
                  const SizedBox(height: 80),
                  const Center(child: Icon(Icons.camera_alt_outlined, size: 64, color: Colors.grey)),
                  const SizedBox(height: 16),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Center(child: Text(l10n.cameraTabNoCropsYet, textAlign: TextAlign.center)),
                  ),
                ],
              );
            }
            return ListView(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(l10n.cameraTabPickCropHint, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ),
                for (final cycle in cycles)
                  ListTile(
                    leading: const Icon(Icons.grass),
                    title: Text(cycle.crop.name),
                    subtitle: Text('${l10n.cameraTabSownOnLabel}: ${cycle.sowingDate}'),
                    trailing: Chip(label: Text(cycle.cultivationStatus.replaceAll('_', ' ').toUpperCase())),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => CropPhotoListScreen(cropCycleId: cycle.id)),
                    ),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}
