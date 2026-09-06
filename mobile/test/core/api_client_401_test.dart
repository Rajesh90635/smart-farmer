import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';

/// D84-01 (docs/audit/FINAL_CANONICAL_group_D.md): a mid-session 401 must
/// trigger exactly one silent refresh attempt and either transparently
/// retry (on success) or surface a single, uniform SessionExpiredException
/// (on failure) - never the raw, farmer-facing "Request failed with status
/// 401" ApiException a screen previously had no uniform way to handle.
void main() {
  test('a 401 followed by a successful silent refresh transparently retries and succeeds', () async {
    var callCount = 0;
    final client = MockClient((request) async {
      callCount++;
      if (callCount == 1) {
        return http.Response('{"error": {"code": "UNAUTHORIZED", "message": "expired"}}', 401);
      }
      expect(request.headers['Authorization'], 'Bearer new-token');
      return http.Response('{"ok": true}', 200);
    });
    final apiClient = ApiClient(client: client, baseUrl: 'http://test');
    apiClient.setAccessToken('old-token');
    apiClient.onSessionExpired = () async => 'new-token';

    final result = await apiClient.get('/protected');

    expect(result['ok'], true);
    expect(callCount, 2);
  });

  test('a 401 with a failed silent refresh throws SessionExpiredException, not the raw 401', () async {
    final client = MockClient((request) async {
      return http.Response('{"error": {"code": "UNAUTHORIZED", "message": "expired"}}', 401);
    });
    final apiClient = ApiClient(client: client, baseUrl: 'http://test');
    apiClient.onSessionExpired = () async => null; // refresh token itself expired/revoked

    await expectLater(apiClient.get('/protected'), throwsA(isA<SessionExpiredException>()));
  });

  test('a 401 with no interceptor wired throws the raw ApiException, unchanged legacy behavior', () async {
    final client = MockClient((request) async {
      return http.Response('{"error": {"code": "UNAUTHORIZED", "message": "expired"}}', 401);
    });
    final apiClient = ApiClient(client: client, baseUrl: 'http://test');
    // onSessionExpired left unset.

    await expectLater(apiClient.get('/protected'), throwsA(isA<ApiException>()));
  });

  test('interceptSessionExpiry: false (login/register/refresh) never attempts a silent refresh', () async {
    var refreshAttempted = false;
    final client = MockClient((request) async {
      return http.Response('{"error": {"code": "INVALID_CREDENTIALS", "message": "wrong password"}}', 401);
    });
    final apiClient = ApiClient(client: client, baseUrl: 'http://test');
    apiClient.onSessionExpired = () async {
      refreshAttempted = true;
      return 'new-token';
    };

    await expectLater(
      apiClient.post('/auth/login', interceptSessionExpiry: false, body: {'phone_number': '1', 'password': 'x'}),
      throwsA(isA<ApiException>().having((e) => e.code, 'code', 'INVALID_CREDENTIALS')),
    );
    expect(refreshAttempted, isFalse);
  });
}
