import 'dart:io';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'crop_photo_models.dart';
import 'crop_photo_repository.dart';
import 'network_status_checker.dart';
import 'pending_upload_queue.dart';

/// Generates a client-side idempotency key without pulling in a new
/// package dependency just for UUID formatting - this doesn't need to be
/// a strict RFC4122 UUID, only unique-enough and stable across retries
/// (the backend's uniqueness constraint is on the string value, not its
/// format).
String _generateClientUploadId() {
  final random = Random.secure();
  final bytes = List<int>.generate(16, (_) => random.nextInt(256));
  return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
}

/// Home -> My Crop -> Check Crop -> Take Photo -> Preview -> Use Photo /
/// Retake -> Upload, per the approved flow. Also supports gallery
/// selection from the same screen (Requirement 5) via a second button.
class CameraCaptureScreen extends StatefulWidget {
  final String sessionId;
  const CameraCaptureScreen({super.key, required this.sessionId});

  @override
  State<CameraCaptureScreen> createState() => _CameraCaptureScreenState();
}

enum _CaptureUiState { idle, previewing, uploading, uploaded, qualityRejected, failed, waitingForNetwork }

class _CameraCaptureScreenState extends State<CameraCaptureScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _capturedFile;
  String _source = 'camera';
  _CaptureUiState _state = _CaptureUiState.idle;
  String? _errorMessage;
  List<String> _qualityReasons = const [];
  late final String _clientUploadId;

  @override
  void initState() {
    super.initState();
    _clientUploadId = _generateClientUploadId();
  }

  Future<void> _capture(ImageSource source) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 95);
    if (picked == null) return;
    setState(() {
      _capturedFile = picked;
      _source = source == ImageSource.camera ? 'camera' : 'gallery';
      _state = _CaptureUiState.previewing;
    });
  }

  void _retake() {
    setState(() {
      _capturedFile = null;
      _state = _CaptureUiState.idle;
    });
  }

  Future<void> _usePhoto() async {
    if (_capturedFile == null) return;

    final networkChecker = context.read<NetworkStatusChecker>();
    final isOnline = await networkChecker.isOnline();

    final queue = context.read<PendingUploadQueue>();
    // Copy into the queue's own persistent directory FIRST - the photo
    // must survive an app restart before the network returns, which the
    // original image_picker temp file is not guaranteed to do.
    final bytes = await _capturedFile!.readAsBytes();
    final localPath = await queue.persistFile(bytes, _capturedFile!.name);
    final pending = PendingUpload(
      clientUploadId: _clientUploadId,
      sessionId: widget.sessionId,
      localFilePath: localPath,
      fileName: _capturedFile!.name,
      mimeType: 'image/jpeg',
      source: _source,
    );
    await queue.enqueue(pending);

    if (!isOnline) {
      setState(() => _state = _CaptureUiState.waitingForNetwork);
      return;
    }

    await _attemptUpload(pending);
  }

  Future<void> _attemptUpload(PendingUpload pending) async {
    setState(() {
      _state = _CaptureUiState.uploading;
      _errorMessage = null;
    });

    final queue = context.read<PendingUploadQueue>();
    await queue.updateStatus(pending.clientUploadId, PendingUploadStatus.uploading);

    try {
      // Same clientUploadId is sent every time - a retry after a failed
      // attempt, an app restart, or an automatic background sync
      // (see sync_coordinator.dart) is always safe and will not create a
      // duplicate photo record - enforced by the backend's real unique
      // constraint on (session_id, client_upload_id).
      final bytes = await pending.readBytes();
      final result = await context.read<CropPhotoRepository>().uploadPhoto(
            sessionId: pending.sessionId,
            fileBytes: bytes,
            fileName: pending.fileName,
            mimeType: pending.mimeType,
            clientUploadId: pending.clientUploadId,
            source: pending.source,
          );
      // Transport succeeded either way - a quality rejection is a
      // successful HTTP response with image_quality_status=rejected in
      // the body, NOT an exception, so this is correctly marked
      // 'uploaded' (not 'failed') and removed from the retry queue in
      // both cases: nothing here is ever retried again, since retrying
      // would just re-send the exact same rejected photo (Requirement 8
      // - "quality rejected ≠ retry forever"). The only thing that
      // differs is what the FARMER sees.
      await queue.updateStatus(pending.clientUploadId, PendingUploadStatus.uploaded);
      await queue.remove(pending.clientUploadId);
      if (!mounted) return;
      if (result.isLowQuality) {
        setState(() {
          _state = _CaptureUiState.qualityRejected;
          _qualityReasons = result.qualityReasons;
        });
      } else {
        setState(() => _state = _CaptureUiState.uploaded);
      }
    } on ApiException catch (e) {
      // Real bug fixed here: this path used to fall into the generic
      // catch below and be marked 'failed' identically to a plain network
      // error - unlike sync_coordinator.dart's background upload path,
      // which already correctly distinguishes a 401 (needs re-login, will
      // never succeed by simply retrying) from a transient failure. A
      // farmer tapping "Retry" here on an expired session would just get
      // the exact same 401 again, forever, with a misleading "try again"
      // message.
      if (e.statusCode == 401) {
        final message = AppLocalizations.of(context)!.errorSessionExpired;
        await queue.updateStatus(pending.clientUploadId, PendingUploadStatus.authenticationRequired, errorMessage: message);
        if (!mounted) return;
        setState(() {
          _state = _CaptureUiState.failed;
          _errorMessage = message;
        });
        return;
      }
      final message = FriendlyError.from(e, AppLocalizations.of(context)!);
      await queue.updateStatus(pending.clientUploadId, PendingUploadStatus.failed, errorMessage: message);
      if (!mounted) return;
      setState(() {
        _state = _CaptureUiState.failed;
        _errorMessage = message;
      });
    } catch (e) {
      final message = FriendlyError.from(e, AppLocalizations.of(context)!);
      await queue.updateStatus(pending.clientUploadId, PendingUploadStatus.failed, errorMessage: message);
      if (!mounted) return;
      setState(() {
        _state = _CaptureUiState.failed;
        _errorMessage = message;
      });
    }
  }

  Future<void> _retryUpload() async {
    if (_capturedFile == null) return;
    final queue = context.read<PendingUploadQueue>();
    final bytes = await _capturedFile!.readAsBytes();
    final localPath = await queue.persistFile(bytes, _capturedFile!.name);
    final pending = PendingUpload(
      clientUploadId: _clientUploadId, // SAME id - this is what makes retry safe
      sessionId: widget.sessionId,
      localFilePath: localPath,
      fileName: _capturedFile!.name,
      mimeType: 'image/jpeg',
      source: _source,
    );
    await _attemptUpload(pending);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.checkCropTitle)),
      body: SafeArea(child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_state == _CaptureUiState.idle) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ElevatedButton.icon(
              onPressed: () => _capture(ImageSource.camera),
              icon: const Icon(Icons.camera_alt, size: 32),
              label: Text(l10n.takePhotoButton),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => _capture(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: Text(l10n.chooseFromGalleryButton),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Expanded(
          child: _capturedFile != null
              ? Image.file(File(_capturedFile!.path), fit: BoxFit.contain)
              : const SizedBox.shrink(),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: _buildActionArea(l10n),
        ),
      ],
    );
  }

  Widget _buildActionArea(AppLocalizations l10n) {
    switch (_state) {
      case _CaptureUiState.previewing:
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            OutlinedButton.icon(onPressed: _retake, icon: const Icon(Icons.replay), label: Text(l10n.retakeButton)),
            ElevatedButton.icon(onPressed: _usePhoto, icon: const Icon(Icons.check), label: Text(l10n.usePhotoButton)),
          ],
        );
      case _CaptureUiState.waitingForNetwork:
        return Column(
          children: [
            Text(l10n.waitingForNetwork),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: () async {
                final online = await context.read<NetworkStatusChecker>().isOnline();
                if (online) {
                  final queueItem = context
                      .read<PendingUploadQueue>()
                      .items
                      .where((u) => u.clientUploadId == _clientUploadId)
                      .firstOrNull;
                  if (queueItem != null) await _attemptUpload(queueItem);
                }
              },
              child: Text(l10n.retryUploadButton),
            ),
          ],
        );
      case _CaptureUiState.uploading:
        return Column(children: [const CircularProgressIndicator(), const SizedBox(height: 8), Text(l10n.uploadingPhoto)]);
      case _CaptureUiState.uploaded:
        return Column(
          children: [
            Text(l10n.uploadSuccess, style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ElevatedButton(onPressed: () => Navigator.of(context).pop(true), child: Text(l10n.doneButton)),
          ],
        );
      case _CaptureUiState.qualityRejected:
        // Deliberately NOT l10n.uploadSuccess - the photo was received
        // and stored, but the server flagged it as unsuitable for
        // reliable diagnosis. This is neither a transport success message
        // nor a network-failure message - its own distinct state.
        return Column(
          children: [
            Text(l10n.photoNeedsAnotherTry, style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...qualityFriendlyMessages(l10n, _qualityReasons).map(
              (msg) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                    const SizedBox(width: 6),
                    Flexible(child: Text(msg)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton.icon(onPressed: _retake, icon: const Icon(Icons.camera_alt), label: Text(l10n.retakeButton)),
          ],
        );
      case _CaptureUiState.failed:
        return Column(
          children: [
            Text(l10n.uploadFailed, style: const TextStyle(color: Colors.red)),
            if (_errorMessage != null) Text(_errorMessage!, style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 8),
            ElevatedButton(onPressed: _retryUpload, child: Text(l10n.retryUploadButton)),
          ],
        );
      case _CaptureUiState.idle:
        return const SizedBox.shrink();
    }
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
