import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/core/friendly_error.dart';

void main() {
  test('maps INVALID_CREDENTIALS to a farmer-friendly message', () {
    final error = ApiException('raw backend message', statusCode: 401, code: 'INVALID_CREDENTIALS');
    final message = FriendlyError.from(error);
    expect(message, isNot(contains('raw backend message')));
    expect(message.toLowerCase(), contains('phone number or password'));
  });

  test('maps unknown codes to a generic message rather than exposing them', () {
    final error = ApiException('some internal detail', statusCode: 500, code: 'SOME_UNMAPPED_CODE');
    final message = FriendlyError.from(error);
    expect(message, isNot(contains('SOME_UNMAPPED_CODE')));
    expect(message, isNot(contains('some internal detail')));
  });

  test('maps a plain network exception to a connectivity-oriented message', () {
    final message = FriendlyError.from(Exception('socket closed'));
    expect(message.toLowerCase(), contains('connection'));
  });
}
