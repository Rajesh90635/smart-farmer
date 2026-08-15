import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';

PendingUpload _makeUpload(String id) => PendingUpload(
      clientUploadId: id,
      sessionId: 'session-1',
      localFilePath: '/tmp/does-not-need-to-exist-for-these-tests-$id.jpg',
      fileName: 'leaf.jpg',
      mimeType: 'image/jpeg',
      source: 'camera',
    );

void main() {
  // Persistence to disk is best-effort (see pending_upload_queue.dart's
  // _persist()) - in this host test environment there is no real
  // path_provider platform channel available, so every persist attempt
  // fails silently and only the in-memory behavior under test here is
  // exercised. This is the same "platform-channel limitation" already
  // documented for every other Flutter test in this project - the
  // in-memory contract is still fully real and verified.

  test('enqueue adds an item with the default waitingForNetwork status', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    expect(queue.items.length, 1);
    expect(queue.items.first.status, PendingUploadStatus.waitingForNetwork);
  });

  test('updateStatus changes only the matching item', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    await queue.enqueue(_makeUpload('b'));

    await queue.updateStatus('a', PendingUploadStatus.uploading);

    expect(queue.items.firstWhere((u) => u.clientUploadId == 'a').status, PendingUploadStatus.uploading);
    expect(queue.items.firstWhere((u) => u.clientUploadId == 'b').status, PendingUploadStatus.waitingForNetwork);
  });

  test('remove drops the item from the queue', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    await queue.remove('a');
    expect(queue.items, isEmpty);
  });

  test('retryable includes failed and waitingForNetwork, excludes uploaded/uploading', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a')); // waitingForNetwork
    await queue.enqueue(_makeUpload('b'));
    await queue.updateStatus('b', PendingUploadStatus.failed);
    await queue.enqueue(_makeUpload('c'));
    await queue.updateStatus('c', PendingUploadStatus.uploaded);

    final retryableIds = queue.retryable.map((u) => u.clientUploadId).toSet();
    expect(retryableIds, {'a', 'b'});
  });

  test('failed upload retains its error message', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    await queue.updateStatus('a', PendingUploadStatus.failed, errorMessage: 'Network error');
    expect(queue.items.first.lastErrorMessage, 'Network error');
  });

  test('toJson/fromJson round-trip preserves all fields', () {
    final original = _makeUpload('a');
    final restored = PendingUpload.fromJson(original.toJson());
    expect(restored.clientUploadId, original.clientUploadId);
    expect(restored.sessionId, original.sessionId);
    expect(restored.localFilePath, original.localFilePath);
    expect(restored.fileName, original.fileName);
    expect(restored.mimeType, original.mimeType);
    expect(restored.source, original.source);
    expect(restored.status, original.status);
  });

  test('loadFromDisk with no prior manifest leaves the queue empty, not crashed', () async {
    final queue = PendingUploadQueue();
    await queue.loadFromDisk();
    expect(queue.items, isEmpty);
  });

  test('authenticationRequired uploads are excluded from retryable but appear in needsManualAction', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    await queue.updateStatus('a', PendingUploadStatus.authenticationRequired, errorMessage: 'Please log in again.');

    expect(queue.retryable, isEmpty);
    expect(queue.needsManualAction.map((u) => u.clientUploadId), ['a']);
    // Still present in the queue at all - not silently dropped/deleted.
    expect(queue.items.length, 1);
  });

  test('retriesExhausted uploads are excluded from retryable but appear in needsManualAction', () async {
    final queue = PendingUploadQueue();
    await queue.enqueue(_makeUpload('a'));
    await queue.updateStatus('a', PendingUploadStatus.retriesExhausted, errorMessage: 'Upload failed repeatedly.');

    expect(queue.retryable, isEmpty);
    expect(queue.needsManualAction.map((u) => u.clientUploadId), ['a']);
  });

  test('retryCount defaults to zero and round-trips through JSON', () {
    final original = _makeUpload('a');
    expect(original.retryCount, 0);

    original.retryCount = 3;
    final restored = PendingUpload.fromJson(original.toJson());
    expect(restored.retryCount, 3);
  });

  test('fromJson defaults retryCount to zero for a manifest written before this field existed', () {
    final legacyJson = {
      'clientUploadId': 'a',
      'sessionId': 'session-1',
      'localFilePath': '/tmp/x.jpg',
      'fileName': 'leaf.jpg',
      'mimeType': 'image/jpeg',
      'source': 'camera',
      'status': 'failed',
      'lastErrorMessage': null,
      // no 'retryCount' key at all - simulates an old manifest file
    };
    final restored = PendingUpload.fromJson(legacyJson);
    expect(restored.retryCount, 0);
  });
}
