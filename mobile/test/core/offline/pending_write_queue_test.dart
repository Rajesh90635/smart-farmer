import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/offline/pending_write_queue.dart';

/// D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors
/// pending_upload_queue_test.dart's own test structure - same
/// persistence/retry/terminal-state contract, generalized past photo
/// uploads.
PendingWrite _makeWrite(String id) => PendingWrite(
      clientRequestId: id,
      method: 'POST',
      path: '/farms',
      body: {'farm_name': 'Test Farm $id'},
    );

void main() {
  // Persistence to disk is best-effort - in this host test environment
  // there is no real path_provider platform channel available, so every
  // persist attempt fails silently and only the in-memory behavior under
  // test here is exercised (same documented limitation as
  // pending_upload_queue_test.dart, which uses plain test() for the same
  // reason - no testWidgets synthetic zone to fight).

  test('enqueue adds an item with the default waitingForNetwork status', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    expect(queue.items.length, 1);
    expect(queue.items.first.status, PendingWriteStatus.waitingForNetwork);
  });

  test('updateStatus changes only the matching item', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.enqueue(_makeWrite('b'));

    await queue.updateStatus('a', PendingWriteStatus.sending);

    expect(queue.items.firstWhere((w) => w.clientRequestId == 'a').status, PendingWriteStatus.sending);
    expect(queue.items.firstWhere((w) => w.clientRequestId == 'b').status, PendingWriteStatus.waitingForNetwork);
  });

  test('remove drops the item from the queue - success removal', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.sent);
    await queue.remove('a');
    expect(queue.items, isEmpty);
  });

  test('retryable includes failed and waitingForNetwork, excludes sent/sending', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a')); // waitingForNetwork
    await queue.enqueue(_makeWrite('b'));
    await queue.updateStatus('b', PendingWriteStatus.failed);
    await queue.enqueue(_makeWrite('c'));
    await queue.updateStatus('c', PendingWriteStatus.sending);

    final retryableIds = queue.retryable.map((w) => w.clientRequestId).toSet();
    expect(retryableIds, {'a', 'b'});
  });

  test('failed write retains its error message', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.failed, errorMessage: 'Network error');
    expect(queue.items.first.lastErrorMessage, 'Network error');
  });

  test('toJson/fromJson round-trip preserves all fields', () {
    final original = _makeWrite('a');
    final restored = PendingWrite.fromJson(original.toJson());
    expect(restored.clientRequestId, original.clientRequestId);
    expect(restored.method, original.method);
    expect(restored.path, original.path);
    expect(restored.body, original.body);
    expect(restored.status, original.status);
    expect(restored.retryCount, original.retryCount);
  });

  test('loadFromDisk with no prior manifest leaves the queue empty, not crashed', () async {
    final queue = PendingWriteQueue();
    await queue.loadFromDisk();
    expect(queue.items, isEmpty);
  });

  test('authenticationRequired writes are excluded from retryable but appear in needsManualAction', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.authenticationRequired, errorMessage: 'Please log in again.');

    expect(queue.retryable, isEmpty);
    expect(queue.needsManualAction.map((w) => w.clientRequestId), ['a']);
    // Still present in the queue at all - not silently dropped/deleted.
    expect(queue.items.length, 1);
  });

  test('retriesExhausted writes are excluded from retryable but appear in needsManualAction', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.retriesExhausted, errorMessage: 'Upload failed repeatedly.');

    expect(queue.retryable, isEmpty);
    expect(queue.needsManualAction.map((w) => w.clientRequestId), ['a']);
  });

  test('reviveAuthRequiredItems resets authenticationRequired items back to retryable', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.authenticationRequired, errorMessage: 'Please log in again.');

    await queue.reviveAuthRequiredItems();

    expect(queue.items.first.status, PendingWriteStatus.waitingForNetwork);
    expect(queue.items.first.lastErrorMessage, isNull);
  });

  test('reviveForRetry resets one item and its retryCount', () async {
    final queue = PendingWriteQueue();
    await queue.enqueue(_makeWrite('a'));
    await queue.updateStatus('a', PendingWriteStatus.retriesExhausted, errorMessage: 'Upload failed repeatedly.');
    queue.items.first.retryCount = 5;

    await queue.reviveForRetry('a');

    expect(queue.items.first.status, PendingWriteStatus.waitingForNetwork);
    expect(queue.items.first.retryCount, 0);
    expect(queue.items.first.lastErrorMessage, isNull);
  });

  test('clientRequestId is the idempotency key - the same value is reused across a retry, never regenerated', () async {
    final queue = PendingWriteQueue();
    final write = _makeWrite('stable-id');
    await queue.enqueue(write);
    await queue.updateStatus('stable-id', PendingWriteStatus.failed, errorMessage: 'boom');
    await queue.reviveForRetry('stable-id');

    expect(queue.items.length, 1);
    expect(queue.items.first.clientRequestId, 'stable-id');
  });

  test('generateClientRequestId produces distinct values each call', () {
    final a = generateClientRequestId();
    final b = generateClientRequestId();
    expect(a, isNot(equals(b)));
    expect(a, isNotEmpty);
  });
}
