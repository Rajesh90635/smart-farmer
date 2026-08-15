import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'authenticated_crop_photo.dart';
import 'crop_photo_detail_screen.dart';
import 'crop_photo_models.dart';
import 'crop_photo_repository.dart';
import 'photo_guidance_screen.dart';

/// My Crop -> Photos -> Photo list (Requirement 23). Shows thumbnail,
/// date, upload status, basic quality status only - no internal/technical
/// metadata (storage paths, DB ids) per Requirement 24's spirit applied
/// to the list view too.
class CropPhotoListScreen extends StatefulWidget {
  final String cropCycleId;
  const CropPhotoListScreen({super.key, required this.cropCycleId});

  @override
  State<CropPhotoListScreen> createState() => _CropPhotoListScreenState();
}

class _CropPhotoListScreenState extends State<CropPhotoListScreen> {
  late Future<List<CropPhoto>> _photosFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _photosFuture = context.read<CropPhotoRepository>().listPhotosForCropCycle(widget.cropCycleId);
  }

  Future<void> _refresh() async {
    setState(_load);
    await _photosFuture;
  }

  Future<void> _checkCrop() async {
    final session = await context.read<CropPhotoRepository>().createSession(widget.cropCycleId);
    if (!mounted) return;
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => PhotoGuidanceScreen(sessionId: session.id)),
    );
    if (result == true) _refresh();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.myCropPhotosTitle)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _checkCrop,
        icon: const Icon(Icons.camera_alt),
        label: Text(l10n.checkCropTitle),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<CropPhoto>>(
          future: _photosFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text(FriendlyError.from(snapshot.error!)));
            }
            final photos = snapshot.data ?? [];
            if (photos.isEmpty) {
              return ListView(
                children: [
                  const SizedBox(height: 80),
                  const Center(child: Icon(Icons.photo_camera_back, size: 64, color: Colors.grey)),
                  const SizedBox(height: 16),
                  Center(child: Text(l10n.noPhotosYet)),
                ],
              );
            }
            return GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 8, mainAxisSpacing: 8),
              itemCount: photos.length,
              itemBuilder: (context, index) {
                final photo = photos[index];
                return InkWell(
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => CropPhotoDetailScreen(photoId: photo.id)),
                  ),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      AuthenticatedCropPhoto(photoId: photo.id, thumbnail: true),
                      Positioned(
                        bottom: 4,
                        left: 4,
                        right: 4,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(4)),
                          child: Text(
                            photo.isLowQuality ? 'Low quality' : photo.uploadStatus,
                            style: const TextStyle(color: Colors.white, fontSize: 11),
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
