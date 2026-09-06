import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';

void main() {
  group('CropPhoto.fromJson', () {
    test('parses an accepted-quality photo', () {
      final photo = CropPhoto.fromJson({
        'id': 'p1',
        'session_id': 's1',
        'crop_cycle_id': 'c1',
        'original_filename': 'leaf.jpg',
        'mime_type': 'image/jpeg',
        'file_size_bytes': 12345,
        'width_px': 600,
        'height_px': 600,
        'upload_timestamp': '2026-06-01T10:00:00Z',
        'source': 'camera',
        'upload_status': 'ready',
        'image_quality_status': 'accepted',
        'quality_reasons': [],
      });
      expect(photo.isLowQuality, isFalse);
      expect(photo.qualityReasons, isEmpty);
    });

    test('parses a rejected-quality photo with reasons', () {
      final photo = CropPhoto.fromJson({
        'id': 'p2',
        'session_id': 's1',
        'crop_cycle_id': 'c1',
        'original_filename': null,
        'mime_type': 'image/jpeg',
        'file_size_bytes': 500,
        'width_px': 600,
        'height_px': 600,
        'upload_timestamp': '2026-06-01T10:00:00Z',
        'source': 'gallery',
        'upload_status': 'ready',
        'image_quality_status': 'rejected',
        'quality_reasons': ['too_dark', 'too_blurry'],
      });
      expect(photo.isLowQuality, isTrue);
      expect(photo.qualityReasons, ['too_dark', 'too_blurry']);
    });

    test('D30-05/D30-06: possible_duplicate/old_photo are warnings, never a hard block', () {
      final photo = CropPhoto.fromJson({
        'id': 'p3',
        'session_id': 's1',
        'crop_cycle_id': 'c1',
        'original_filename': null,
        'mime_type': 'image/jpeg',
        'file_size_bytes': 500,
        'width_px': 600,
        'height_px': 600,
        'capture_timestamp': '2026-01-01T10:00:00Z',
        'upload_timestamp': '2026-06-01T10:00:00Z',
        'source': 'camera',
        'upload_status': 'ready',
        'image_quality_status': 'accepted',
        'quality_reasons': ['possible_duplicate', 'old_photo'],
      });
      expect(photo.isLowQuality, isFalse);
      expect(photo.qualityReasons, ['possible_duplicate', 'old_photo']);
      expect(photo.captureTimestamp, '2026-01-01T10:00:00Z');
    });

    test('captureTimestamp is null when the backend never received one', () {
      final photo = CropPhoto.fromJson({
        'id': 'p4',
        'session_id': 's1',
        'crop_cycle_id': 'c1',
        'original_filename': null,
        'mime_type': 'image/jpeg',
        'file_size_bytes': 500,
        'width_px': 600,
        'height_px': 600,
        'upload_timestamp': '2026-06-01T10:00:00Z',
        'source': 'camera',
        'upload_status': 'ready',
        'image_quality_status': 'accepted',
        'quality_reasons': [],
      });
      expect(photo.captureTimestamp, isNull);
    });
  });

  group('qualityFriendlyMessages', () {
    test('maps possible_duplicate and old_photo to real l10n keys, not the raw code', () {
      expect(qualityReasonMessageKeys['possible_duplicate'], 'photoPossibleDuplicate');
      expect(qualityReasonMessageKeys['old_photo'], 'photoOldPhoto');
    });
  });

  group('CropPhotoSession.fromJson', () {
    test('parses a session with a label', () {
      final session = CropPhotoSession.fromJson({'id': 's1', 'crop_cycle_id': 'c1', 'label': 'Leaf check'});
      expect(session.label, 'Leaf check');
    });

    test('parses a session without a label', () {
      final session = CropPhotoSession.fromJson({'id': 's1', 'crop_cycle_id': 'c1', 'label': null});
      expect(session.label, isNull);
    });
  });
}
