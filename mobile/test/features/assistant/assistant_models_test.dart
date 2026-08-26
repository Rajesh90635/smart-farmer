import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/assistant/assistant_models.dart';

void main() {
  group('ChatMessage', () {
    test('parses a farmer message with no intent/sources/confidence', () {
      final message = ChatMessage.fromJson({
        'id': 'msg-1',
        'role': 'farmer',
        'content': 'What is happening to my crop?',
        'language_code': 'en',
        'intent': null,
        'tools_called': null,
        'sources': null,
        'confidence': null,
        'created_at': '2026-01-01T00:00:00Z',
      });
      expect(message.isFromFarmer, isTrue);
      expect(message.intent, isNull);
      expect(message.sources, isNull);
    });

    test('parses an assistant message carrying real provenance', () {
      final message = ChatMessage.fromJson({
        'id': 'msg-2',
        'role': 'assistant',
        'content': 'Your Tomato is at the flowering stage.',
        'language_code': 'en',
        'intent': 'crop_status',
        'tools_called': ['get_crop_status'],
        'sources': ["This crop's record"],
        'confidence': 'high_confidence',
        'created_at': '2026-01-01T00:00:05Z',
      });
      expect(message.isFromFarmer, isFalse);
      expect(message.toolsCalled, ['get_crop_status']);
      expect(message.sources, ["This crop's record"]);
      expect(message.confidence, 'high_confidence');
    });
  });

  group('ConversationHistory', () {
    test('a farmer who never sent a message parses to a null conversationId and no messages', () {
      final history = ConversationHistory.fromJson({'conversation_id': null, 'messages': []});
      expect(history.conversationId, isNull);
      expect(history.messages, isEmpty);
    });

    test('parses multiple messages in order', () {
      final history = ConversationHistory.fromJson({
        'conversation_id': 'conv-1',
        'messages': [
          {
            'id': 'msg-1',
            'role': 'farmer',
            'content': 'help',
            'language_code': 'en',
            'intent': null,
            'tools_called': null,
            'sources': null,
            'confidence': null,
            'created_at': '2026-01-01T00:00:00Z',
          },
          {
            'id': 'msg-2',
            'role': 'assistant',
            'content': 'I can help with crop, weather, and order questions.',
            'language_code': 'en',
            'intent': 'help',
            'tools_called': [],
            'sources': [],
            'confidence': null,
            'created_at': '2026-01-01T00:00:01Z',
          },
        ],
      });
      expect(history.conversationId, 'conv-1');
      expect(history.messages.length, 2);
      expect(history.messages[0].isFromFarmer, isTrue);
      expect(history.messages[1].isFromFarmer, isFalse);
    });
  });

  group('ChatTurnResult', () {
    test('parses a full chat POST response', () {
      final result = ChatTurnResult.fromJson({
        'conversation_id': 'conv-1',
        'farmer_message': {
          'id': 'msg-1',
          'role': 'farmer',
          'content': 'Will it rain today?',
          'language_code': 'en',
          'intent': null,
          'tools_called': null,
          'sources': null,
          'confidence': null,
          'created_at': '2026-01-01T00:00:00Z',
        },
        'assistant_message': {
          'id': 'msg-2',
          'role': 'assistant',
          'content': "I don't have weather data for your farm yet.",
          'language_code': 'en',
          'intent': 'weather',
          'tools_called': ['get_weather_status'],
          'sources': [],
          'confidence': null,
          'created_at': '2026-01-01T00:00:01Z',
        },
      });
      expect(result.conversationId, 'conv-1');
      expect(result.farmerMessage.isFromFarmer, isTrue);
      expect(result.assistantMessage.intent, 'weather');
      expect(result.assistantMessage.toolsCalled, ['get_weather_status']);
    });
  });
}
