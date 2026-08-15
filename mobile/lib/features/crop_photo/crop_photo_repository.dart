import 'dart:typed_data';

import '../../core/api_client.dart';
import 'crop_photo_models.dart';

class CropPhotoRepository {
  final ApiClient _apiClient;
  CropPhotoRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<CropPhotoSession> createSession(String cropCycleId, {String? label}) async {
    final response = await _apiClient.post('/crop-photo-sessions', body: {
      'crop_cycle_id': cropCycleId,
      if (label != null) 'label': label,
    });
    return CropPhotoSession.fromJson(response);
  }

  /// Uploads with the SAME clientUploadId on every retry - the backend's
  /// unique constraint on (session_id, client_upload_id) guarantees a
  /// retried call returns the original photo record rather than creating
  /// a duplicate (see backend/docs/CROP_PHOTO_MODULE.md "Idempotency").
  Future<CropPhoto> uploadPhoto({
    required String sessionId,
    required Uint8List fileBytes,
    required String fileName,
    required String mimeType,
    required String clientUploadId,
    required String source,
    bool shareLocation = false,
    double? latitude,
    double? longitude,
  }) async {
    final response = await _apiClient.uploadMultipart(
      '/crop-photo-sessions/$sessionId/photos',
      fileBytes: fileBytes,
      fileName: fileName,
      mimeType: mimeType,
      fields: {
        'client_upload_id': clientUploadId,
        'source': source,
        'share_location': shareLocation.toString(),
        if (latitude != null) 'latitude': latitude.toString(),
        if (longitude != null) 'longitude': longitude.toString(),
      },
    );
    return CropPhoto.fromJson(response);
  }

  Future<List<CropPhoto>> listPhotosForCropCycle(String cropCycleId) async {
    final response = await _apiClient.get('/crop-cycles/$cropCycleId/photos');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(CropPhoto.fromJson).toList();
  }

  Future<CropPhoto> getPhoto(String photoId) async {
    final response = await _apiClient.get('/crop-photos/$photoId');
    return CropPhoto.fromJson(response);
  }

  /// The image bytes are served through an authenticated endpoint, never
  /// a public URL - Image.network can't attach the Authorization header,
  /// so callers use this to get raw bytes and render via Image.memory.
  Future<Uint8List> fetchPhotoBytes(String photoId, {bool thumbnail = false}) {
    final suffix = thumbnail ? '?thumbnail=true' : '';
    return _apiClient.getBytes('/crop-photos/$photoId/file$suffix');
  }

  Future<void> deletePhoto(String photoId) async {
    await _apiClient.delete('/crop-photos/$photoId');
  }

  /// Triggers analysis for an already-uploaded, quality-accepted photo.
  /// The backend's own quality gate (image_quality_status == REJECTED)
  /// is the authoritative check - this call is only ever made after the
  /// client-side isLowQuality check as a first line of defense, never
  /// instead of it. Returns the real requires_review boolean from
  /// AIAnalysisResponse (not discarded) - this is the authoritative,
  /// backend-computed signal for whether an "Request Expert Review"
  /// action should even be offered (Step 13), never a Flutter-side
  /// guess based on result_status text alone.
  Future<AnalysisTriggerResult> analyzePhoto(String photoId) async {
    final response = await _apiClient.post('/crop-photos/$photoId/analyze');
    return AnalysisTriggerResult(
      analysisId: response['id'] as String,
      requiresReview: response['requires_review'] as bool? ?? false,
    );
  }

  /// The farmer-friendly, already-localized rendering of an analysis -
  /// title/confidence_wording/next_action come from the backend's own
  /// safety-reviewed templates (see
  /// backend/app/services/ai_result_localization_service.py) and are
  /// rendered verbatim, never reinterpreted client-side.
  Future<FarmerFriendlyAnalysisResult> getLocalizedAnalysis(String analysisId, {String? language}) async {
    final suffix = language != null ? '?language=$language' : '';
    final response = await _apiClient.get('/ai/analysis/$analysisId/localized$suffix');
    return FarmerFriendlyAnalysisResult.fromJson(response);
  }
}
