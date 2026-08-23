import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/crop_assistant/crop_assistant_models.dart';

void main() {
  group('CropAssistantResponse (Phase 36)', () {
    test('parses a response with context and no limitations', () {
      final response = CropAssistantResponse.fromJson({
        'crop_cycle_id': 'cycle-1',
        'intent': 'crop_status',
        'answer': 'Your Tomato on Farm A is currently at the flowering stage.',
        'context_used': ["This crop's record"],
        'limitations': [],
      });
      expect(response.intent, 'crop_status');
      expect(response.contextUsed, ["This crop's record"]);
      expect(response.limitations, isEmpty);
    });

    test('parses a response with limitations when data is missing - never hidden', () {
      final response = CropAssistantResponse.fromJson({
        'crop_cycle_id': 'cycle-1',
        'intent': 'disease_status',
        'answer': "I don't have disease detection information for this crop yet.",
        'context_used': [],
        'limitations': ['No data was available in Smart Farmer for this specific question.'],
      });
      expect(response.limitations, isNotEmpty);
      expect(response.contextUsed, isEmpty);
    });

    test('prescription_blocked intent parses correctly and never carries context', () {
      final response = CropAssistantResponse.fromJson({
        'crop_cycle_id': 'cycle-1',
        'intent': 'prescription_blocked',
        'answer': "I can't recommend a specific pesticide.",
        'context_used': [],
        'limitations': [],
      });
      expect(response.intent, 'prescription_blocked');
      expect(response.contextUsed, isEmpty);
    });

    test('empty context_used and limitations lists parse without crashing', () {
      final response = CropAssistantResponse.fromJson({
        'crop_cycle_id': 'cycle-1',
        'intent': 'general_agriculture',
        'answer': 'x',
        'context_used': [],
        'limitations': [],
      });
      expect(response.contextUsed, isEmpty);
      expect(response.limitations, isEmpty);
    });

    test('multiple limitations all parse correctly', () {
      final response = CropAssistantResponse.fromJson({
        'crop_cycle_id': 'cycle-1',
        'intent': 'disease_status',
        'answer': 'x',
        'context_used': ['AI disease detection (this crop)'],
        'limitations': ['No data was available.', 'Low confidence.'],
      });
      expect(response.limitations.length, 2);
    });
  });
}
