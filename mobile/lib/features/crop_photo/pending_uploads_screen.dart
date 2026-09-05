import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/app_localizations.dart';
import 'pending_upload_queue.dart';
import 'sync_coordinator.dart';

/// The "manual retry UI path" referenced in pending_upload_queue.dart's
/// and sync_coordinator.dart's own comments, which previously didn't
/// exist anywhere - an upload stuck in `authenticationRequired` or
/// `retriesExhausted` was permanently invisible to the farmer, with no
/// way to see it or act on it. Reachable from HomeScreen's banner.
class PendingUploadsScreen extends StatelessWidget {
  const PendingUploadsScreen({super.key});

  Future<void> _retry(BuildContext context, PendingUpload upload) async {
    await context.read<PendingUploadQueue>().reviveForRetry(upload.clientUploadId);
    if (!context.mounted) return;
    // Fire-and-forget, same as login_screen.dart's post-login revival -
    // the queue's own ChangeNotifier updates this screen live as the
    // retry proceeds (uploading -> uploaded/failed), no separate
    // loading state needs to be tracked here.
    context.read<SyncCoordinator>().syncNow();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.pendingUploadsTitle)),
      body: Consumer<PendingUploadQueue>(
        builder: (context, queue, _) {
          final items = queue.needsManualAction;
          if (items.isEmpty) {
            return Center(child: Text(l10n.pendingUploadsEmptyMessage));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final upload = items[index];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.warning_amber, color: Colors.orange),
                  title: Text(upload.fileName),
                  subtitle: upload.lastErrorMessage != null ? Text(upload.lastErrorMessage!) : null,
                  trailing: ElevatedButton(
                    onPressed: () => _retry(context, upload),
                    child: Text(l10n.retryUploadButton),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
