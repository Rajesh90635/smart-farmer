import 'dart:io';

import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_repository.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_uploads_screen.dart';
import 'package:smart_farmer_mobile/features/crop_photo/sync_coordinator.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

import '../../screens/login_screen_test.dart' show FakeOfflineConnectivityPlatform;

PendingUpload _upload(String id, PendingUploadStatus status, {String? lastErrorMessage}) => PendingUpload(
      clientUploadId: id,
      sessionId: 'session-1',
      localFilePath: '/tmp/$id.jpg',
      fileName: '$id.jpg',
      mimeType: 'image/jpeg',
      source: 'camera',
      status: status,
      lastErrorMessage: lastErrorMessage,
    );

/// PendingUploadQueue's every mutation (enqueue/updateStatus/reviveForRetry)
/// persists to disk via path_provider's `getApplicationDocumentsDirectory()`
/// then real `dart:io` Directory/File calls (see pending_upload_queue.dart's
/// `_persist()`). Faking the federated-plugin interface here (the same
/// pattern as FakeOfflineConnectivityPlatform for connectivity_plus) avoids
/// ever hitting a real platform channel for the path itself.
///
/// The real `dart:io` calls that follow still need `WidgetTester.runAsync()`
/// around every call site that triggers them: `testWidgets` runs in a
/// synthetic zone that only pumps Flutter-driven timers/microtasks, so a
/// genuine OS-backed async file operation started outside `runAsync` never
/// completes (confirmed by direct isolation - it doesn't return even
/// wrapped in an explicit 5-second `.timeout()`, i.e. the call itself never
/// resolves, not merely slow). `pending_upload_queue_test.dart` never hits
/// this because it uses plain `test()`, which has no such synthetic zone.
class FakeDocumentsDirectoryPathProvider extends PathProviderPlatform {
  final String _path;
  FakeDocumentsDirectoryPathProvider(this._path);

  @override
  Future<String?> getApplicationDocumentsPath() async => _path;
}

Widget _wrap(PendingUploadQueue queue) {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider<PendingUploadQueue>.value(value: queue),
      Provider<SyncCoordinator>(
        create: (_) => SyncCoordinator(
          queue: queue,
          networkChecker: NetworkStatusChecker(),
          repository: CropPhotoRepository(apiClient: ApiClient()),
        ),
      ),
    ],
    child: const MaterialApp(
      localizationsDelegates: [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: [Locale('en')],
      home: PendingUploadsScreen(),
    ),
  );
}

void main() {
  ConnectivityPlatform.instance = FakeOfflineConnectivityPlatform();

  testWidgets('shows the empty message when nothing needs manual action', (tester) async {
    await tester.pumpWidget(_wrap(PendingUploadQueue()));

    expect(find.text('No pending uploads.'), findsOneWidget);
  });

  testWidgets('lists authenticationRequired and retriesExhausted items with their error message', (tester) async {
    final dir = (await tester.runAsync(() => Directory.systemTemp.createTemp('pending_uploads_screen_test_')))!;
    PathProviderPlatform.instance = FakeDocumentsDirectoryPathProvider(dir.path);

    final queue = PendingUploadQueue();
    await tester.runAsync(() async {
      await queue.enqueue(_upload('a', PendingUploadStatus.authenticationRequired, lastErrorMessage: 'Please log in again.'));
      await queue.enqueue(_upload('b', PendingUploadStatus.retriesExhausted, lastErrorMessage: 'Upload failed repeatedly.'));
      // Neither a normal in-flight nor an already-terminal-success item is
      // ever a candidate for manual action - must not appear here.
      await queue.enqueue(_upload('c', PendingUploadStatus.waitingForNetwork));
    });

    await tester.pumpWidget(_wrap(queue));

    expect(find.text('a.jpg'), findsOneWidget);
    expect(find.text('b.jpg'), findsOneWidget);
    expect(find.text('c.jpg'), findsNothing);
    expect(find.text('Please log in again.'), findsOneWidget);
    expect(find.text('Upload failed repeatedly.'), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Retry'), findsNWidgets(2));
  });

  testWidgets('tapping Retry revives the item back to waitingForNetwork and removes it from view', (tester) async {
    final dir = (await tester.runAsync(() => Directory.systemTemp.createTemp('pending_uploads_screen_test_')))!;
    PathProviderPlatform.instance = FakeDocumentsDirectoryPathProvider(dir.path);

    final queue = PendingUploadQueue();
    await tester.runAsync(
      () => queue.enqueue(_upload('a', PendingUploadStatus.retriesExhausted, lastErrorMessage: 'Upload failed repeatedly.')),
    );

    await tester.pumpWidget(_wrap(queue));
    expect(find.text('a.jpg'), findsOneWidget);

    // The Retry button's onPressed itself triggers real persistence (see
    // FakeDocumentsDirectoryPathProvider's doc comment above) - tap and
    // settle inside the SAME runAsync callback so that work resolves
    // against the real event loop rather than the fake-async test zone.
    await tester.runAsync(() async {
      await tester.tap(find.widgetWithText(ElevatedButton, 'Retry'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));
    });
    await tester.pumpAndSettle();

    // Revived to waitingForNetwork (no longer `needsManualAction`) - the
    // fake connectivity reports offline, so SyncCoordinator.syncNow()
    // returns without touching it further, leaving it in that state.
    expect(queue.items.firstWhere((u) => u.clientUploadId == 'a').status, PendingUploadStatus.waitingForNetwork);
    expect(find.text('a.jpg'), findsNothing);
    expect(find.text('No pending uploads.'), findsOneWidget);
  });
}
