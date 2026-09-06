import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// D81-01: thrown by a repository method (e.g. FarmRepository.createFarm)
/// when the device is offline and the write was queued instead of sent -
/// a distinct, non-error outcome a screen can catch separately from a
/// genuine failure, mirroring SessionExpiredException's role in
/// api_client.dart for a different kind of "not a normal success/failure".
class QueuedForSyncException implements Exception {
  const QueuedForSyncException();

  @override
  String toString() => 'QueuedForSyncException';
}

/// Generates a client-side idempotency key - same non-cryptographic-UUID
/// approach already used for crop-photo uploads
/// (camera_capture_screen.dart's _generateClientUploadId), reused here
/// rather than duplicated.
String generateClientRequestId() {
  final random = Random.secure();
  final bytes = List<int>.generate(16, (_) => random.nextInt(256));
  return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
}

/// D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): the generic offline
/// write queue this row itself recommends building ONCE and reusing for
/// D81-02..07/09 (plot/crop/task/expense/harvest edits) rather than
/// seven bespoke queues - extracted from PendingUploadQueue's own
/// proven persistence/retry/terminal-state pattern
/// (features/crop_photo/pending_upload_queue.dart), generalized to hold
/// an arbitrary JSON-serializable API write instead of a file upload.
class PendingWrite {
  final String clientRequestId; // idempotency key - same value on every retry
  final String method; // 'POST' | 'PUT'
  final String path; // e.g. '/farms' - always relative, ApiClient prepends baseUrl
  final Map<String, dynamic> body;
  PendingWriteStatus status;
  String? lastErrorMessage;
  int retryCount;
  // D83-02 (docs/audit/FINAL_CANONICAL_group_D.md): see
  // PendingUpload.lastAttemptAt's own docstring - same backoff-gating
  // purpose, generalized past photo uploads.
  DateTime? lastAttemptAt;

  PendingWrite({
    required this.clientRequestId,
    required this.method,
    required this.path,
    required this.body,
    this.status = PendingWriteStatus.waitingForNetwork,
    this.lastErrorMessage,
    this.retryCount = 0,
    this.lastAttemptAt,
  });

  Map<String, dynamic> toJson() => {
        'clientRequestId': clientRequestId,
        'method': method,
        'path': path,
        'body': body,
        'status': status.name,
        'lastErrorMessage': lastErrorMessage,
        'retryCount': retryCount,
        'lastAttemptAt': lastAttemptAt?.toUtc().toIso8601String(),
      };

  factory PendingWrite.fromJson(Map<String, dynamic> json) => PendingWrite(
        clientRequestId: json['clientRequestId'] as String,
        method: json['method'] as String,
        path: json['path'] as String,
        body: Map<String, dynamic>.from(json['body'] as Map),
        status: PendingWriteStatus.values.byName(json['status'] as String),
        lastErrorMessage: json['lastErrorMessage'] as String?,
        retryCount: json['retryCount'] as int? ?? 0,
        // Defaulted for forward-compatibility with a manifest written by
        // a version of this app before lastAttemptAt existed.
        lastAttemptAt: json['lastAttemptAt'] != null ? DateTime.parse(json['lastAttemptAt'] as String) : null,
      );
}

/// Same terminal-state set as PendingUploadQueue's PendingUploadStatus -
/// see that enum's own docstring for why authenticationRequired/
/// retriesExhausted are excluded from automatic retry.
enum PendingWriteStatus { waitingForNetwork, sending, sent, failed, authenticationRequired, retriesExhausted }

const int kMaxAutomaticWriteRetries = 5;

/// Offline-first persistent queue for generic API writes - same
/// manifest-file persistence strategy as PendingUploadQueue, in its own
/// subdirectory so the two queues' manifests never collide.
class PendingWriteQueue extends ChangeNotifier {
  final List<PendingWrite> _items = [];
  bool _loaded = false;

  List<PendingWrite> get items => List.unmodifiable(_items);

  Future<Directory> _queueDirectory() async {
    final docs = await getApplicationDocumentsDirectory();
    final dir = Directory('${docs.path}/pending_writes');
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  Future<File> _manifestFile() async {
    final dir = await _queueDirectory();
    return File('${dir.path}/manifest.json');
  }

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
        ..addAll(decoded.map((e) => PendingWrite.fromJson(e as Map<String, dynamic>)));
      notifyListeners();
    } catch (_) {
      // A corrupted/unreadable manifest must never crash app startup.
    }
  }

  Future<void> _persist() async {
    try {
      final file = await _manifestFile();
      await file.writeAsString(jsonEncode(_items.map((w) => w.toJson()).toList()));
    } catch (_) {
      // Best-effort persistence only - in-memory list stays authoritative
      // for the running app session regardless of disk-write success.
    }
  }

  Future<void> enqueue(PendingWrite write) async {
    _items.add(write);
    notifyListeners();
    await _persist();
  }

  Future<void> updateStatus(String clientRequestId, PendingWriteStatus status, {String? errorMessage}) async {
    final write = _items.where((w) => w.clientRequestId == clientRequestId).firstOrNull;
    if (write == null) return;
    write.status = status;
    write.lastErrorMessage = errorMessage;
    notifyListeners();
    await _persist();
  }

  Future<void> remove(String clientRequestId) async {
    _items.removeWhere((w) => w.clientRequestId == clientRequestId);
    notifyListeners();
    await _persist();
  }

  List<PendingWrite> get retryable =>
      _items.where((w) => w.status == PendingWriteStatus.failed || w.status == PendingWriteStatus.waitingForNetwork).toList();

  List<PendingWrite> get needsManualAction =>
      _items.where((w) => w.status == PendingWriteStatus.authenticationRequired || w.status == PendingWriteStatus.retriesExhausted).toList();

  Future<void> reviveAuthRequiredItems() async {
    var changed = false;
    for (final w in _items) {
      if (w.status == PendingWriteStatus.authenticationRequired) {
        w.status = PendingWriteStatus.waitingForNetwork;
        w.lastErrorMessage = null;
        changed = true;
      }
    }
    if (!changed) return;
    notifyListeners();
    await _persist();
  }

  Future<void> reviveForRetry(String clientRequestId) async {
    final write = _items.where((w) => w.clientRequestId == clientRequestId).firstOrNull;
    if (write == null) return;
    write.status = PendingWriteStatus.waitingForNetwork;
    write.lastErrorMessage = null;
    write.retryCount = 0;
    notifyListeners();
    await _persist();
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
