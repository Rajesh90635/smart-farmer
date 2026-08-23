import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';

CropPhoto _makePhoto({required String imageQualityStatus, List<String> qualityReasons = const []}) => CropPhoto(
      id: 'photo-1',
      sessionId: 'session-1',
      cropCycleId: 'cycle-1',
      mimeType: 'image/jpeg',
      fileSizeBytes: 1024,
      widthPx: 800,
      heightPx: 600,
      uploadTimestamp: '2026-01-01T00:00:00Z',
      source: 'camera',
      uploadStatus: 'uploaded',
      imageQualityStatus: imageQualityStatus,
      qualityReasons: qualityReasons,
    );

void main() {
  group('CropPhoto quality result handling (Step 11 Phase 1)', () {
    test('accepted result is not treated as low quality', () {
      final photo = _makePhoto(imageQualityStatus: 'accepted');
      expect(photo.isLowQuality, isFalse);
    });

    test('rejected result is treated as low quality', () {
      final photo = _makePhoto(imageQualityStatus: 'rejected', qualityReasons: ['too_dark']);
      expect(photo.isLowQuality, isTrue);
    });

    test('rejected result with a single reason', () {
      final photo = _makePhoto(imageQualityStatus: 'rejected', qualityReasons: ['too_blurry']);
      expect(photo.isLowQuality, isTrue);
      expect(photo.qualityReasons, ['too_blurry']);
    });

    test('rejected result with multiple reasons preserves all of them', () {
      final photo = _makePhoto(imageQualityStatus: 'rejected', qualityReasons: ['too_dark', 'too_blurry']);
      expect(photo.qualityReasons, ['too_dark', 'too_blurry']);
    });

    test('rejected result with an empty reason list does not crash isLowQuality', () {
      final photo = _makePhoto(imageQualityStatus: 'rejected', qualityReasons: []);
      expect(photo.isLowQuality, isTrue);
      expect(photo.qualityReasons, isEmpty);
    });

    test('an unrecognized/unknown quality status is NOT treated as low quality', () {
      final photo = _makePhoto(imageQualityStatus: 'pending');
      expect(photo.isLowQuality, isFalse);
    });

    test('fromJson round-trip preserves image_quality_status and quality_reasons', () {
      final json = {
        'id': 'photo-1',
        'session_id': 'session-1',
        'crop_cycle_id': 'cycle-1',
        'mime_type': 'image/jpeg',
        'file_size_bytes': 1024,
        'width_px': 800,
        'height_px': 600,
        'upload_timestamp': '2026-01-01T00:00:00Z',
        'source': 'gallery',
        'upload_status': 'uploaded',
        'image_quality_status': 'rejected',
        'quality_reasons': ['too_bright'],
      };
      final photo = CropPhoto.fromJson(json);
      expect(photo.isLowQuality, isTrue);
      expect(photo.qualityReasons, ['too_bright']);
      expect(photo.source, 'gallery');
    });

    test('fromJson tolerates a missing quality_reasons key without crashing', () {
      final json = {
        'id': 'photo-1',
        'session_id': 'session-1',
        'crop_cycle_id': 'cycle-1',
        'mime_type': 'image/jpeg',
        'file_size_bytes': 1024,
        'width_px': 800,
        'height_px': 600,
        'upload_timestamp': '2026-01-01T00:00:00Z',
        'source': 'camera',
        'upload_status': 'uploaded',
        'image_quality_status': 'accepted',
      };
      final photo = CropPhoto.fromJson(json);
      expect(photo.qualityReasons, isEmpty);
    });
  });

  group('qualityFriendlyMessages mapping (shared between camera and detail screens)', () {
    test('maps each known reason code to the correct l10n key name', () {
      expect(qualityReasonMessageKeys['too_dark'], 'photoTooDark');
      expect(qualityReasonMessageKeys['too_bright'], 'photoTooBright');
      expect(qualityReasonMessageKeys['too_blurry'], 'photoTooBlurry');
    });
  });
}
