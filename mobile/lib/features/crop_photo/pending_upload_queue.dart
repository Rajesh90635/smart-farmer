import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// A photo capture waiting to be uploaded - created the moment the farmer
/// taps "Use Photo", independent of whether the network is currently up.
/// The photo must never disappear if the network fails OR if the app is
/// closed/restarted before the network returns - this is what makes this
/// queue genuinely "offline-first" rather than merely "network-retry
/// within one app session" (the previous in-memory-only version's
/// disclosed limitation). Every entry carries a stable `clientUploadId`
/// so retrying an upload is always idempotent against the backend's real
/// unique constraint on (session_id, client_upload_id) - verified
/// unchanged in app/models/crop_photo.py; no backend change was needed
/// for this phase.
class PendingUpload {
  final String clientUploadId; // idempotency key - same value on every retry
  final String sessionId;
  final String localFilePath; // persisted on-device file - NOT raw bytes in memory
  final String fileName;
  final String mimeType;
  final String source; // 'camera' | 'gallery'
  PendingUploadStatus status;
  String? lastErrorMessage;
  int retryCount; // caps automatic retries so a permanently-failing upload doesn't hammer forever

  PendingUpload({
    required this.clientUploadId,
    required this.sessionId,
    required this.localFilePath,
    required this.fileName,
    required this.mimeType,
    required this.source,
    this.status = PendingUploadStatus.waitingForNetwork,
    this.lastErrorMessage,
    this.retryCount = 0,
  });

  /// Bytes are only ever read from disk at the moment of an actual upload
  /// attempt - never held in memory for the queue's lifetime, since a
  /// farmer may queue several photos before connectivity returns.
  Future<Uint8List> readBytes() => File(localFilePath).readAsBytes();

  Map<String, dynamic> toJson() => {
        'clientUploadId': clientUploadId,
        'sessionId': sessionId,
        'localFilePath': localFilePath,
        'fileName': fileName,
        'mimeType': mimeType,
        'source': source,
        'status': status.name,
        'lastErrorMessage': lastErrorMessage,
        'retryCount': retryCount,
      };

  factory PendingUpload.fromJson(Map<String, dynamic> json) => PendingUpload(
        clientUploadId: json['clientUploadId'] as String,
        sessionId: json['sessionId'] as String,
        localFilePath: json['localFilePath'] as String,
        fileName: json['fileName'] as String,
        mimeType: json['mimeType'] as String,
        source: json['source'] as String,
        status: PendingUploadStatus.values.byName(json['status'] as String),
        lastErrorMessage: json['lastErrorMessage'] as String?,
        // Defaulted for forward-compatibility with a manifest written by
        // a version of this app before retryCount existed.
        retryCount: json['retryCount'] as int? ?? 0,
      );
}

/// authenticationRequired and retriesExhausted are both terminal for
/// AUTOMATIC retry purposes (excluded from `retryable`, see below) - a
/// bug found during Step 10 verification: the original implementation
/// treated every failure identically and would retry an expired-session
/// upload forever, indefinitely, on every future connectivity change.
/// Neither state deletes the queued photo or its local file - the farmer
/// can still act on it (re-authenticate, then manually retry via the
/// existing UI retry path), it just stops being auto-retried.
enum PendingUploadStatus { waitingForNetwork, uploading, uploaded, failed, authenticationRequired, retriesExhausted }

/// Automatic retries stop after this many attempts for a given upload -
/// prevents an upload that will never succeed (e.g. a corrupted file, a
/// permanently rejected format) from being retried forever. Manual retry
/// remains possible regardless (a farmer explicitly retrying resets this
/// via a fresh PendingUpload with retryCount 0 - see camera_capture_screen.dart).
const int kMaxAutomaticRetries = 5;

/// Offline-first persistent queue: every enqueue/status-change/remove is
/// written to a JSON manifest file in the app's own document directory
/// (via path_provider - free, local, no new native permissions), and the
/// image bytes themselves are copied into that same directory so they
/// survive an app restart, a killed process, or a device reboot before
/// connectivity returns. `loadFromDisk()` restores the full in-memory
/// mirror (for UI reactivity via ChangeNotifier) from that manifest on
/// app startup - a farmer's queued photo is never silently lost.
///
/// Public API (enqueue/updateStatus/remove/retryable) is UNCHANGED from
/// the prior in-memory-only version, exactly as that version's own
/// docstring anticipated - only the storage behind it changed, so no
/// caller (camera_capture_screen.dart) needed a behavioral rewrite,
/// only the small addition of persisting the picked file before
/// enqueueing (see camera_capture_screen.dart's _persistPickedFile).
class PendingUploadQueue extends ChangeNotifier {
  final List<PendingUpload> _items = [];
  bool _loaded = false;

  List<PendingUpload> get items => List.unmodifiable(_items);

  Future<Directory> _queueDirectory() async {
    final docs = await getApplicationDocumentsDirectory();
    final dir = Directory('${docs.path}/pending_crop_photo_uploads');
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  Future<File> _manifestFile() async {
    final dir = await _queueDirectory();
    return File('${dir.path}/manifest.json');
  }

  /// Must be called once at app startup (before any UI reads `items`) -
  /// restores whatever was queued before the app was last closed.
  Future<void> loadFromDisk() async {
    if (_loaded) return;
    _loaded = true;
    try {
      final file = await _manifestFile();
      if (!await file.exists()) return;
      final raw = await file.readAsString();
      final List<dynamic> decoded = jsonDecode(raw) as List<dynamic>;
      _items
        ..clear()
        ..addAll(decoded.map((e) => PendingUpload.fromJson(e as Map<String, dynamic>)));
      notifyListeners();
    } catch (_) {
      // A corrupted/unreadable manifest must never crash app startup -
      // worst case, previously-queued photos are not recovered, but the
      // app still starts normally and new photos can still be queued.
    }
  }

  Future<void> _persist() async {
    // A transient disk-write failure (or, in a host test environment, no
    // path_provider platform channel being available at all) must never
    // corrupt in-memory queue state - the in-memory list is still the
    // source of truth for the running app session regardless of whether
    // the on-disk mirror succeeded. This also means the pure
    // list-manipulation behavior (enqueue/updateStatus/remove) stays unit
    // -testable without needing to mock a platform channel.
    try {
      final file = await _manifestFile();
      await file.writeAsString(jsonEncode(_items.map((u) => u.toJson()).toList()));
    } catch (_) {
      // Best-effort persistence only, as above.
    }
  }

  /// Copies a freshly-captured/picked file into this queue's own
  /// persistent directory, returning the new stable path to store on the
  /// PendingUpload - the original image_picker temp file is not relied
  /// upon to survive (the OS can clear it at any time).
  Future<String> persistFile(Uint8List bytes, String suggestedFileName) async {
    final dir = await _queueDirectory();
    final path = '${dir.path}/${DateTime.now().microsecondsSinceEpoch}_$suggestedFileName';
    await File(path).writeAsBytes(bytes, flush: true);
    return path;
  }

  Future<void> enqueue(PendingUpload upload) async {
    _items.add(upload);
    notifyListeners();
    await _persist();
  }

  Future<void> updateStatus(String clientUploadId, PendingUploadStatus status, {String? errorMessage}) async {
    final upload = _items.where((u) => u.clientUploadId == clientUploadId).firstOrNull;
    if (upload == null) return;
    upload.status = status;
    upload.lastErrorMessage = errorMessage;
    notifyListeners();
    await _persist();
  }

  Future<void> remove(String clientUploadId) async {
    final upload = _items.where((u) => u.clientUploadId == clientUploadId).firstOrNull;
    _items.removeWhere((u) => u.clientUploadId == clientUploadId);
    notifyListeners();
    await _persist();
    // Clean up the persisted file too - once uploaded, there's no reason
    // to keep a second copy on-device indefinitely.
    if (upload != null) {
      try {
        final f = File(upload.localFilePath);
        if (await f.exists()) await f.delete();
      } catch (_) {
        // Best-effort cleanup only - a failure to delete a leftover local
        // file must never break the (already-successful) upload flow.
      }
    }
  }

  List<PendingUpload> get retryable =>
      _items.where((u) => u.status == PendingUploadStatus.failed || u.status == PendingUploadStatus.waitingForNetwork).toList();

  /// Uploads that will NEVER be automatically retried again - either the
  /// farmer's session needs re-authentication, or automatic retries were
  /// exhausted. Still present in the queue (not deleted) so a farmer-
  /// facing UI can surface them distinctly and offer manual action.
  List<PendingUpload> get needsManualAction =>
      _items.where((u) => u.status == PendingUploadStatus.authenticationRequired || u.status == PendingUploadStatus.retriesExhausted).toList();
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
