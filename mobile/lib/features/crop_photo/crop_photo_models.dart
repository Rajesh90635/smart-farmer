/// Data models mirroring backend/app/schemas/crop_photo.py.
library;

import '../../l10n/app_localizations.dart';

class CropPhotoSession {
  final String id;
  final String cropCycleId;
  final String? label;

  CropPhotoSession({required this.id, required this.cropCycleId, this.label});

  factory CropPhotoSession.fromJson(Map<String, dynamic> json) => CropPhotoSession(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        label: json['label'] as String?,
      );
}

class CropPhoto {
  final String id;
  final String sessionId;
  final String cropCycleId;
  final String? originalFilename;
  final String mimeType;
  final int fileSizeBytes;
  final int widthPx;
  final int heightPx;
  final String uploadTimestamp;
  final String source;
  final String uploadStatus;
  final String imageQualityStatus;
  final List<String> qualityReasons;

  CropPhoto({
    required this.id,
    required this.sessionId,
    required this.cropCycleId,
    this.originalFilename,
    required this.mimeType,
    required this.fileSizeBytes,
    required this.widthPx,
    required this.heightPx,
    required this.uploadTimestamp,
    required this.source,
    required this.uploadStatus,
    required this.imageQualityStatus,
    required this.qualityReasons,
  });

  bool get isLowQuality => imageQualityStatus == 'rejected';

  factory CropPhoto.fromJson(Map<String, dynamic> json) => CropPhoto(
        id: json['id'] as String,
        sessionId: json['session_id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        originalFilename: json['original_filename'] as String?,
        mimeType: json['mime_type'] as String,
        fileSizeBytes: json['file_size_bytes'] as int,
        widthPx: json['width_px'] as int,
        heightPx: json['height_px'] as int,
        uploadTimestamp: json['upload_timestamp'] as String,
        source: json['source'] as String,
        uploadStatus: json['upload_status'] as String,
        imageQualityStatus: json['image_quality_status'] as String,
        qualityReasons: (json['quality_reasons'] as List?)?.cast<String>() ?? const [],
      );
}

/// The two real fields Flutter needs from AIAnalysisResponse's initial
/// POST .../analyze call - `requiresReview` is the actual backend
/// boolean (never inferred from result_status text), used to decide
/// whether "Request Expert Review" should be offered at all (Step 13).
class AnalysisTriggerResult {
  final String analysisId;
  final bool requiresReview;
  AnalysisTriggerResult({required this.analysisId, required this.requiresReview});
}

/// Mirrors backend/app/schemas/farmer_friendly_result.py exactly - the
/// backend has ALREADY converted the raw AI result into farmer-friendly,
/// localized text (title/confidence_wording/next_action) via the same
/// template system used for weather/notification messages. This class
/// exists so Flutter only ever RENDERS these fields verbatim - it never
/// maps result_status to its own wording, which would risk diverging
/// from (or duplicating) the backend's own safety-reviewed phrasing.
class FarmerFriendlyAnalysisResult {
  final String analysisId;
  final String languageCode;
  final String resultStatus; // 'healthy' | 'disease_detected' | 'unknown' | 'low_confidence' | 'crop_mismatch' | 'ai_unavailable' | 'failed' | 'processing'
  final String title;
  final String? confidenceWording;
  final String? nextAction;
  final String audioText;

  FarmerFriendlyAnalysisResult({
    required this.analysisId,
    required this.languageCode,
    required this.resultStatus,
    required this.title,
    this.confidenceWording,
    this.nextAction,
    required this.audioText,
  });

  factory FarmerFriendlyAnalysisResult.fromJson(Map<String, dynamic> json) => FarmerFriendlyAnalysisResult(
        analysisId: json['analysis_id'] as String,
        languageCode: json['language_code'] as String,
        resultStatus: json['result_status'] as String,
        title: json['title'] as String,
        confidenceWording: json['confidence_wording'] as String?,
        nextAction: json['next_action'] as String?,
        // A real backend field (see
        // backend/app/services/ai_result_localization_service.py -
        // audio_text is always set, never null) that the earlier Flutter
        // model never captured at all - found and fixed while wiring up
        // voice output this phase. Falls back to `title` defensively
        // only if an unexpected response is ever missing it.
        audioText: json['audio_text'] as String? ?? json['title'] as String,
      );
}

/// Farmer-facing retake guidance, keyed by the same reason codes the
/// backend's quality heuristic returns (never a disease term - see
/// backend/app/core/image_quality.py). Actual strings come from
/// AppLocalizations at the call site; this just maps code -> l10n key
/// name, kept centralized so it isn't duplicated per screen.
const Map<String, String> qualityReasonMessageKeys = {
  'too_dark': 'photoTooDark',
  'too_bright': 'photoTooBright',
  'too_blurry': 'photoTooBlurry',
};

/// Shared quality-reason-to-farmer-message mapping - extracted from
/// crop_photo_detail_screen.dart (which had this exact logic private to
/// itself) so camera_capture_screen.dart can show the identical wording
/// immediately after upload, rather than a second, possibly-diverging
/// copy. An unrecognized reason code falls back to the raw code itself -
/// never invents a message the server didn't imply, matching the
/// existing behavior this was extracted from unchanged.
List<String> qualityFriendlyMessages(AppLocalizations l10n, List<String> reasons) {
  return reasons.map((reason) {
    switch (reason) {
      case 'too_dark':
        return l10n.photoTooDark;
      case 'too_bright':
        return l10n.photoTooBright;
      case 'too_blurry':
        return l10n.photoTooBlurry;
      default:
        return reason;
    }
  }).toList();
}
