import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/voice_language_controller.dart';
import '../../core/voice_service.dart';
import '../../l10n/app_localizations.dart';
import '../expert_case/case_models.dart';
import '../expert_case/case_repository.dart';
import 'authenticated_crop_photo.dart';
import 'crop_photo_models.dart';
import 'crop_photo_repository.dart';

/// Photo detail (Requirement 24): photo, crop-cycle context, date,
/// status. Deliberately does NOT show storage path, DB id, or other
/// internal processing details.
class CropPhotoDetailScreen extends StatefulWidget {
  final String photoId;
  const CropPhotoDetailScreen({super.key, required this.photoId});

  @override
  State<CropPhotoDetailScreen> createState() => _CropPhotoDetailScreenState();
}

class _CropPhotoDetailScreenState extends State<CropPhotoDetailScreen> {
  CropPhoto? _photo;
  bool _loading = true;
  String? _error;

  bool _analyzing = false;
  FarmerFriendlyAnalysisResult? _analysisResult;
  String? _analysisError;
  bool _lastAnalysisRequiresReview = false;
  String? _lastAnalysisId;

  ExpertCase? _case;
  bool _requestingCase = false;
  String? _caseError;
  bool _loadingCaseStatus = false;
  bool _voiceUnavailableMessageShown = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final photo = await context.read<CropPhotoRepository>().getPhoto(widget.photoId);
      setState(() {
        _photo = photo;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
  }

  /// The client-side isLowQuality guard (never showing the Analyze
  /// button for a rejected photo) is the first line of defense; this
  /// duplicate `if` is a defensive backstop in case this method is ever
  /// reachable through a path other than the button (e.g. a future
  /// deep link) - the backend's own quality gate remains the actual
  /// authority regardless (a rejected photo's analyze call would fail
  /// server-side either way).
  Future<void> _analyzeCrop() async {
    final photo = _photo;
    if (photo == null || photo.isLowQuality || _analyzing) return;

    setState(() {
      _analyzing = true;
      _analysisError = null;
    });

    try {
      final repo = context.read<CropPhotoRepository>();
      final trigger = await repo.analyzePhoto(photo.id);
      final result = await repo.getLocalizedAnalysis(trigger.analysisId);
      if (!mounted) return;
      setState(() {
        _analysisResult = result;
        _lastAnalysisRequiresReview = trigger.requiresReview;
        _lastAnalysisId = trigger.analysisId;
        _analyzing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _analysisError = FriendlyError.from(e, AppLocalizations.of(context)!);
        _analyzing = false;
      });
    }
  }

  /// Only reachable when `_lastAnalysisRequiresReview` is true (a REAL
  /// backend boolean, see crop_photo_models.dart) OR when AI was
  /// unavailable (case creation doesn't require an AI result at all -
  /// both crop_photo_id and ai_analysis_id are optional on the backend,
  /// confirmed by reading CaseCreateRequest directly). Duplicate-request
  /// protection is session-local only: once `_case` is set, the button
  /// is replaced by status display - there is no backend "does a case
  /// already exist for this photo" lookup to check across app restarts,
  /// a disclosed limitation (see PROJECT_STATUS.md).
  Future<void> _requestExpertReview() async {
    final photo = _photo;
    if (photo == null || _requestingCase || _case != null) return;

    setState(() {
      _requestingCase = true;
      _caseError = null;
    });

    try {
      final reason = _lastAnalysisRequiresReview ? 'ai_low_confidence' : 'farmer_requested';
      final newCase = await context.read<CaseRepository>().createCase(
            cropCycleId: photo.cropCycleId,
            cropPhotoId: photo.id,
            aiAnalysisId: _lastAnalysisId,
            requestedProfessionalRole: 'expert',
            reason: reason,
            consentSharedItems: ['crop_photo', if (_lastAnalysisId != null) 'ai_analysis'],
          );
      if (!mounted) return;
      setState(() {
        _case = newCase;
        _requestingCase = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _caseError = FriendlyError.from(e, AppLocalizations.of(context)!);
        _requestingCase = false;
      });
    }
  }

  /// Manual refresh only - no push notifications, polling, or real-time
  /// update mechanism exists anywhere in this project (confirmed by
  /// search before deciding this), so this is the honest, non-fabricated
  /// way for a farmer to check for a status change.
  Future<void> _refreshCaseStatus() async {
    final current = _case;
    if (current == null || _loadingCaseStatus) return;
    setState(() => _loadingCaseStatus = true);
    try {
      final updated = await context.read<CaseRepository>().getCase(current.id);
      if (!mounted) return;
      setState(() {
        _case = updated;
        _loadingCaseStatus = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _caseError = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loadingCaseStatus = false;
      });
    }
  }

  Future<void> _delete() async {
    final l10n = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(l10n.deletePhotoConfirm),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(l10n.cancelButton)),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: Text(l10n.removeButton)),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await context.read<CropPhotoRepository>().deletePhoto(widget.photoId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.photoDeleted)));
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  /// The ONLY place this screen ever calls VoiceService.speak() - always
  /// with text that already came verbatim from the backend response
  /// (result.audioText), never text this screen constructs itself. If
  /// speech genuinely can't play (unsupported language, no TTS engine on
  /// the device), the text is ALREADY visible on screen from the normal
  /// result rendering above - nothing is lost.
  Future<void> _speak(String text, String languageCode) async {
    // In location mode, this can only ever change the VOICE LOCALE, not
    // re-translate `text` itself (already backend-composed in
    // `languageCode`) - same disclosed limitation as every other
    // non-daily-briefing voice call site.
    final voiceLanguageController = context.read<VoiceLanguageController>();
    final voiceLanguageCode = await voiceLanguageController.resolveLanguageCode(contentLanguageCode: languageCode);
    if (!mounted) return;

    final voice = context.read<VoiceService>();
    final started = await voice.speak(text, languageCode: voiceLanguageCode);
    if (!mounted) return;
    setState(() => _voiceUnavailableMessageShown = !started);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.photoDetailTitle),
        actions: [
          if (_photo != null) IconButton(icon: const Icon(Icons.delete_outline), onPressed: _delete),
        ],
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [Text(_error!), const SizedBox(height: 12), ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))],
        ),
      );
    }

    final photo = _photo!;
    return ListView(
      children: [
        AspectRatio(
          aspectRatio: photo.widthPx / photo.heightPx,
          child: AuthenticatedCropPhoto(photoId: photo.id),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Taken: ${photo.uploadTimestamp}'),
              const SizedBox(height: 8),
              Text('Status: ${photo.uploadStatus}'),
              if (photo.isLowQuality) ...[
                const SizedBox(height: 8),
                ...qualityFriendlyMessages(l10n, photo.qualityReasons).map(
                  (msg) => Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Row(
                      children: [
                        const Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                        const SizedBox(width: 6),
                        Expanded(child: Text(msg)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(l10n.qualityRejectedCannotAnalyze, style: const TextStyle(fontStyle: FontStyle.italic)),
              ] else
                ..._buildAnalysisSection(l10n),
                ..._buildCaseSection(l10n),
            ],
          ),
        ),
      ],
    );
  }

  /// Not shown at all for a quality-rejected photo (per the check in
  /// _buildBody) - the Analyze action, loading state, error state, and
  /// result never exist in that case, rather than existing-but-disabled.
  List<Widget> _buildAnalysisSection(AppLocalizations l10n) {
    final widgets = <Widget>[const SizedBox(height: 16)];

    if (_analyzing) {
      widgets.add(Row(children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(l10n.analyzingCrop)]));
      return widgets;
    }

    if (_analysisError != null) {
      widgets.addAll([
        Text(_analysisError!, style: const TextStyle(color: Colors.red)),
        const SizedBox(height: 8),
        ElevatedButton(onPressed: _analyzeCrop, child: Text(l10n.retryUploadButton)),
      ]);
      return widgets;
    }

    final result = _analysisResult;
    if (result == null) {
      widgets.add(ElevatedButton.icon(onPressed: _analyzeCrop, icon: const Icon(Icons.biotech), label: Text(l10n.analyzeCropButton)));
      return widgets;
    }

    // Everything below is rendered VERBATIM from the backend's own
    // farmer-friendly, safety-reviewed text - result_status is used only
    // to pick an icon/color, never to construct or reinterpret the
    // message itself (Requirement 8/29's "backend response is the
    // source of truth").
    final isUnsafeToTrust = result.resultStatus == 'low_confidence' || result.resultStatus == 'unknown' || result.resultStatus == 'crop_mismatch' || result.resultStatus == 'ai_unavailable' || result.resultStatus == 'failed';
    widgets.addAll([
      const Divider(height: 24),
      Row(
        children: [
          Icon(isUnsafeToTrust ? Icons.info_outline : Icons.check_circle_outline, color: isUnsafeToTrust ? Colors.orange : Colors.green),
          const SizedBox(width: 8),
          Expanded(child: Text(result.title, style: const TextStyle(fontWeight: FontWeight.bold))),
        ],
      ),
      if (result.confidenceWording != null) ...[const SizedBox(height: 6), Text(result.confidenceWording!)],
      if (result.nextAction != null) ...[
        const SizedBox(height: 6),
        Row(
          children: [
            const Icon(Icons.arrow_forward, size: 16),
            const SizedBox(width: 6),
            Expanded(child: Text(result.nextAction!, style: const TextStyle(fontStyle: FontStyle.italic))),
          ],
        ),
      ],
      const SizedBox(height: 12),
      OutlinedButton.icon(onPressed: _analyzeCrop, icon: const Icon(Icons.refresh), label: Text(l10n.analyzeAgainButton)),
      const SizedBox(height: 8),
      OutlinedButton.icon(
        onPressed: () => _speak(result.audioText, result.languageCode),
        icon: const Icon(Icons.volume_up),
        label: Text(l10n.listenButton),
      ),
      if (_voiceUnavailableMessageShown) Padding(padding: const EdgeInsets.only(top: 4), child: Text(l10n.voiceUnavailable, style: const TextStyle(fontSize: 12, color: Colors.grey))),
    ]);
    return widgets;
  }

  /// Kept visually and structurally SEPARATE from the AI result section
  /// above (Requirement 14 - "never merge the two into one fabricated
  /// diagnosis") - this section only ever renders real ExpertCase/
  /// CaseAuditEntry fields, never AI-derived text.
  List<Widget> _buildCaseSection(AppLocalizations l10n) {
    final analysisDone = _analysisResult != null;
    final eligibleForReviewRequest = _lastAnalysisRequiresReview || (analysisDone && _analysisResult!.resultStatus == 'ai_unavailable');

    // Nothing at all is shown until there's a reason to - no empty
    // section, no premature "Request Review" button before any analysis
    // has run.
    if (_case == null && !eligibleForReviewRequest) return const [];

    final widgets = <Widget>[const Divider(height: 32), Text(l10n.expertReviewSectionTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)), const SizedBox(height: 8)];

    if (_case == null) {
      if (_requestingCase) {
        widgets.add(Row(children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(l10n.requestingExpertReview)]));
        return widgets;
      }
      if (_caseError != null) {
        widgets.addAll([Text(_caseError!, style: const TextStyle(color: Colors.red)), const SizedBox(height: 8)]);
      }
      widgets.add(ElevatedButton.icon(onPressed: _requestExpertReview, icon: const Icon(Icons.support_agent), label: Text(l10n.requestExpertReviewButton)));
      return widgets;
    }

    // A case exists - display its REAL status, never a fabricated one.
    final caseData = _case!;
    final statusKey = caseStatusMessageKeys[caseData.status];
    final statusText = statusKey != null ? _lookupCaseStatusMessage(l10n, statusKey) : caseData.status;
    widgets.add(Text(statusText));

    if (caseData.isCompleted) {
      if (caseData.finalVerifiedClass != null) {
        widgets.add(const SizedBox(height: 6));
        widgets.add(Text('${l10n.finalFindingLabel}: ${caseData.finalVerifiedClass}'));
      }
      if (caseData.finalVerificationSource != null) {
        widgets.add(const SizedBox(height: 4));
        widgets.add(Text('${l10n.reviewedByLabel}: ${caseData.finalVerificationSource}', style: const TextStyle(fontSize: 12, color: Colors.grey)));
      }
    }

    if (_caseError != null) {
      widgets.addAll([const SizedBox(height: 8), Text(_caseError!, style: const TextStyle(color: Colors.red))]);
    }

    if (!caseData.isCompleted) {
      widgets.add(const SizedBox(height: 8));
      widgets.add(
        _loadingCaseStatus
            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
            : OutlinedButton.icon(onPressed: _refreshCaseStatus, icon: const Icon(Icons.refresh), label: Text(l10n.refreshStatusButton)),
      );
    }

    return widgets;
  }

  /// AppLocalizations has no dynamic-key-by-string-name lookup (it's a
  /// generated class with one getter per key) - this small switch is the
  /// same pattern already established for qualityFriendlyMessages, just
  /// for case-status keys instead of quality-reason keys.
  String _lookupCaseStatusMessage(AppLocalizations l10n, String key) {
    switch (key) {
      case 'caseStatusOpen':
        return l10n.caseStatusOpen;
      case 'caseStatusWaitingForAssignment':
        return l10n.caseStatusWaitingForAssignment;
      case 'caseStatusAssigned':
        return l10n.caseStatusAssigned;
      case 'caseStatusInReview':
        return l10n.caseStatusInReview;
      case 'caseStatusNeedsMoreInformation':
        return l10n.caseStatusNeedsMoreInformation;
      case 'caseStatusVerified':
        return l10n.caseStatusVerified;
      case 'caseStatusRejected':
        return l10n.caseStatusRejected;
      case 'caseStatusEscalated':
        return l10n.caseStatusEscalated;
      case 'caseStatusClosed':
        return l10n.caseStatusClosed;
      case 'caseStatusCancelled':
        return l10n.caseStatusCancelled;
      default:
        return key;
    }
  }
}
