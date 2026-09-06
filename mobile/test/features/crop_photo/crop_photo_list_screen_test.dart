import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_list_screen.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_repository.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

/// D82-06 (docs/audit/FINAL_CANONICAL_group_D.md): crop_photo_list_screen.dart
/// previously had zero references to PendingUploadQueue - a farmer had no
/// visibility here into a photo still queued/uploading/failed for THIS
/// crop cycle.
class FakeCropPhotoRepository extends CropPhotoRepository {
  final List<CropPhoto> photos;
  FakeCropPhotoRepository({this.photos = const []}) : super(apiClient: ApiClient());

  @override
  Future<List<CropPhoto>> listPhotosForCropCycle(String cropCycleId) async => photos;
}

/// Same pattern as pending_uploads_screen_test.dart's own class of the
/// same name - avoids ever hitting a real path_provider platform channel.
class FakeDocumentsDirectoryPathProvider extends PathProviderPlatform {
  final String _path;
  FakeDocumentsDirectoryPathProvider(this._path);

  @override
  Future<String?> getApplicationDocumentsPath() async => _path;
}

// A minimal, valid 1x1 transparent PNG - real bytes an Image.file widget
// can actually decode, not a placeholder path.
const List<int> _onePixelPng = [
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
  0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
  0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
  0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
  0x42, 0x60, 0x82,
];

/// D82-06: PendingUploadQueue.enqueue() persists to disk via path_provider
/// then real dart:io File writes (see pending_upload_queue.dart's own
/// _persist()) - a genuine OS-backed async file operation started outside
/// WidgetTester.runAsync() never completes inside testWidgets' synthetic
/// fake-async zone (the exact documented gotcha in
/// pending_uploads_screen_test.dart). Both the temp-photo write AND the
/// enqueue call are wrapped together here for that reason.
Future<void> _enqueueWithTempPhoto(WidgetTester tester, PendingUploadQueue queue, String clientUploadId, {required String cropCycleId, PendingUploadStatus status = PendingUploadStatus.waitingForNetwork}) async {
  final dir = (await tester.runAsync(() => Directory.systemTemp.createTemp('crop_photo_list_screen_test')))!;
  PathProviderPlatform.instance = FakeDocumentsDirectoryPathProvider(dir.path);

  await tester.runAsync(() async {
    final file = File('${dir.path}/$clientUploadId.png');
    await file.writeAsBytes(_onePixelPng, flush: true);
    await queue.enqueue(PendingUpload(
      clientUploadId: clientUploadId,
      sessionId: 'session-1',
      cropCycleId: cropCycleId,
      localFilePath: file.path,
      fileName: 'leaf.jpg',
      mimeType: 'image/jpeg',
      source: 'camera',
      status: status,
    ));
  });
}

Widget _wrap(CropPhotoRepository repo, PendingUploadQueue queue) {
  return MultiProvider(
    providers: [
      Provider<CropPhotoRepository>.value(value: repo),
      ChangeNotifierProvider<PendingUploadQueue>.value(value: queue),
    ],
    child: const MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: CropPhotoListScreen(cropCycleId: 'cycle-1'),
    ),
  );
}

void main() {
  testWidgets('shows a Queued badge for a photo still waiting for network', (tester) async {
    final queue = PendingUploadQueue();
    await _enqueueWithTempPhoto(tester, queue, 'a', cropCycleId: 'cycle-1');

    await tester.pumpWidget(_wrap(FakeCropPhotoRepository(), queue));
    await tester.pumpAndSettle();

    expect(find.text('Queued'), findsOneWidget);
  });

  testWidgets('shows a Needs attention badge once retries are exhausted', (tester) async {
    final queue = PendingUploadQueue();
    await _enqueueWithTempPhoto(tester, queue, 'a', cropCycleId: 'cycle-1', status: PendingUploadStatus.retriesExhausted);

    await tester.pumpWidget(_wrap(FakeCropPhotoRepository(), queue));
    await tester.pumpAndSettle();

    expect(find.text('Needs attention'), findsOneWidget);
  });

  testWidgets("does not show a pending tile for a different crop cycle's upload", (tester) async {
    final queue = PendingUploadQueue();
    await _enqueueWithTempPhoto(tester, queue, 'a', cropCycleId: 'a-different-cycle');

    await tester.pumpWidget(_wrap(FakeCropPhotoRepository(), queue));
    await tester.pumpAndSettle();

    expect(find.text('Queued'), findsNothing);
  });

  testWidgets('an uploaded (server-confirmed) queue item is not double-shown as a pending tile', (tester) async {
    final queue = PendingUploadQueue();
    await _enqueueWithTempPhoto(tester, queue, 'a', cropCycleId: 'cycle-1', status: PendingUploadStatus.uploaded);

    await tester.pumpWidget(_wrap(FakeCropPhotoRepository(), queue));
    await tester.pumpAndSettle();

    expect(find.text('Uploaded'), findsNothing);
  });
}
