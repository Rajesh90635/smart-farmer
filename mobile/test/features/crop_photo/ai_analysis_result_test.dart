import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_models.dart';

Map<String, dynamic> _json({
  required String resultStatus,
  String title = 'Some title',
  String? confidenceWording,
  String? nextAction,
}) =>
    {
      'analysis_id': 'analysis-1',
      'language_code': 'en',
      'result_status': resultStatus,
      'title': title,
      'confidence_wording': confidenceWording,
      'next_action': nextAction,
    };

void main() {
  group('FarmerFriendlyAnalysisResult (Step 12 Flutter integration)', () {
    test('high-confidence healthy result parses with no next_action required', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(
        resultStatus: 'healthy',
        title: 'Your tomato crop looks healthy.',
      ));
      expect(result.resultStatus, 'healthy');
      expect(result.nextAction, isNull);
    });

    test('disease_detected result carries confidence wording and title verbatim - never recomputed client-side', () {
      final json = _json(
        resultStatus: 'disease_detected',
        title: 'Your tomato crop may have early blight.',
        confidenceWording: 'We are fairly confident about this.',
      );
      final result = FarmerFriendlyAnalysisResult.fromJson(json);
      expect(result.title, json['title']);
      expect(result.confidenceWording, json['confidence_wording']);
    });

    test('medium-confidence result surfaces next_action for review, exactly as the backend provided it', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(
        resultStatus: 'disease_detected',
        confidenceWording: 'We are somewhat confident - a second photo may help confirm this.',
        nextAction: 'An agriculture expert should review this photo.',
      ));
      expect(result.nextAction, 'An agriculture expert should review this photo.');
    });

    test('low_confidence result never carries a disease name field at all - the model has none to carry', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(
        resultStatus: 'low_confidence',
        title: 'We could not identify the problem confidently.',
        nextAction: 'Please take another clear photo or ask an expert.',
      ));
      expect(result.resultStatus, 'low_confidence');
      expect(result.title, isNot(contains('disease')));
    });

    test('ai_unavailable result is distinguishable from a real result by result_status alone', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(
        resultStatus: 'ai_unavailable',
        title: 'AI analysis is currently unavailable.',
      ));
      expect(result.resultStatus, 'ai_unavailable');
    });

    test('crop_mismatch result is parsed without inventing a diagnosis', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(
        resultStatus: 'crop_mismatch',
        title: 'This photo does not appear to match the selected crop.',
        nextAction: 'Please check the selected crop or retake the photo.',
      ));
      expect(result.resultStatus, 'crop_mismatch');
    });

    test('unknown result is parsed as its own distinct status, not silently treated as healthy or diseased', () {
      final result = FarmerFriendlyAnalysisResult.fromJson(_json(resultStatus: 'unknown'));
      expect(result.resultStatus, 'unknown');
    });

    test('missing optional fields (confidence_wording/next_action) do not crash parsing', () {
      final json = {
        'analysis_id': 'analysis-1',
        'language_code': 'en',
        'result_status': 'healthy',
        'title': 'Looks healthy.',
      };
      final result = FarmerFriendlyAnalysisResult.fromJson(json);
      expect(result.confidenceWording, isNull);
      expect(result.nextAction, isNull);
    });

    test('audioText is captured from the real backend field (Step 14 fix - previously discarded entirely)', () {
      final json = _json(resultStatus: 'healthy', title: 'Looks healthy.');
      json['audio_text'] = 'Looks healthy. We are fairly confident about this.';
      final result = FarmerFriendlyAnalysisResult.fromJson(json);
      expect(result.audioText, 'Looks healthy. We are fairly confident about this.');
    });

    test('audioText falls back to title if an unexpected response omits it', () {
      final json = {
        'analysis_id': 'analysis-1',
        'language_code': 'en',
        'result_status': 'healthy',
        'title': 'Looks healthy.',
      };
      final result = FarmerFriendlyAnalysisResult.fromJson(json);
      expect(result.audioText, 'Looks healthy.');
    });
  });
}
