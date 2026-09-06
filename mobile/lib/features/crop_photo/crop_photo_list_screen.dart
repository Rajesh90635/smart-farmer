import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'authenticated_crop_photo.dart';
import 'crop_photo_detail_screen.dart';
import 'crop_photo_models.dart';
import 'crop_photo_repository.dart';
import 'pending_upload_queue.dart';
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
      MaterialPageRoute(builder: (_) => PhotoGuidanceScreen(sessionId: session.id, cropCycleId: widget.cropCycleId)),
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
        child: Consumer<PendingUploadQueue>(
          builder: (context, queue, _) {
            // D82-06 (docs/audit/FINAL_CANONICAL_group_D.md): this crop
            // cycle's own not-yet-server-confirmed uploads, shown as
            // extra tiles ahead of the server-confirmed ones below - a
            // farmer previously had zero visibility here into a photo
            // still queued/uploading/failed for THIS crop.
            final pending = queue.forCropCycle(widget.cropCycleId);
            return FutureBuilder<List<CropPhoto>>(
              future: _photosFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(child: Text(FriendlyError.from(snapshot.error!, AppLocalizations.of(context)!)));
                }
                final photos = snapshot.data ?? [];
                if (photos.isEmpty && pending.isEmpty) {
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
                  itemCount: pending.length + photos.length,
                  itemBuilder: (context, index) {
                    if (index < pending.length) {
                      return _PendingPhotoTile(upload: pending[index]);
                    }
                    final photo = photos[index - pending.length];
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
            );
          },
        ),
      ),
    );
  }
}

/// D82-06 (docs/audit/FINAL_CANONICAL_group_D.md): a locally-queued photo
/// that hasn't reached (or been confirmed by) the server yet - rendered
/// from the on-device file the queue itself already persists, since
/// there is no server photo id to fetch a thumbnail for.
class _PendingPhotoTile extends StatelessWidget {
  final PendingUpload upload;
  const _PendingPhotoTile({required this.upload});

  static const _labels = {
    PendingUploadStatus.waitingForNetwork: 'Queued',
    PendingUploadStatus.uploading: 'Uploading',
    PendingUploadStatus.uploaded: 'Uploaded',
    PendingUploadStatus.failed: 'Failed',
    PendingUploadStatus.authenticationRequired: 'Needs login',
    PendingUploadStatus.retriesExhausted: 'Needs attention',
  };

  static const _needsAttention = {PendingUploadStatus.failed, PendingUploadStatus.authenticationRequired, PendingUploadStatus.retriesExhausted};

  @override
  Widget build(BuildContext context) {
    final badgeColor = _needsAttention.contains(upload.status) ? Colors.red.shade700 : Colors.black54;
    return Stack(
      fit: StackFit.expand,
      children: [
        Image.file(File(upload.localFilePath), fit: BoxFit.cover),
        Positioned(
          bottom: 4,
          left: 4,
          right: 4,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: badgeColor, borderRadius: BorderRadius.circular(4)),
            child: Text(
              _labels[upload.status] ?? upload.status.name,
              style: const TextStyle(color: Colors.white, fontSize: 11),
            ),
          ),
        ),
      ],
    );
  }
}
