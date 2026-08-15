import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/auth/auth_repository.dart';
import 'package:smart_farmer_mobile/features/auth/auth_state.dart';

/// Overrides every network-touching method so AuthState's own logic
/// (status transitions, error surfacing) can be tested without a real
/// backend, secure storage plugin, or HTTP stack - none of which are
/// available in a plain widget-test environment.
class FakeAuthRepository extends AuthRepository {
  bool shouldSucceed;
  FakeAuthRepository({this.shouldSucceed = true}) : super(apiClient: ApiClient());

  @override
  Future<AuthTokens> login({required String phoneNumber, required String password}) async {
    if (!shouldSucceed) {
      throw ApiException('Invalid credentials', statusCode: 401, code: 'INVALID_CREDENTIALS');
    }
    return AuthTokens(accessToken: 'fake-access', refreshToken: 'fake-refresh');
  }

  @override
  Future<AuthTokens> register({
    required String phoneNumber,
    required String password,
    required String fullName,
    required String preferredLanguageCode,
    String? preferredVoiceLanguageCode,
    required List<ConsentInput> consents,
  }) async {
    if (!shouldSucceed) {
      throw ApiException('Duplicate account', statusCode: 409, code: 'DUPLICATE_ACCOUNT');
    }
    return AuthTokens(accessToken: 'fake-access', refreshToken: 'fake-refresh');
  }

  @override
  Future<AuthTokens?> restoreSession() async => shouldSucceed ? AuthTokens(accessToken: 'a', refreshToken: 'r') : null;

  @override
  Future<void> logout() async {}
}

void main() {
  group('AuthState.login', () {
    test('transitions to authenticated on success', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      final result = await state.login(phoneNumber: '9876543210', password: 'Str0ngPass');
      expect(result, isTrue);
      expect(state.status, AuthStatus.authenticated);
      expect(state.lastErrorMessage, isNull);
    });

    test('transitions to unauthenticated with a friendly error on failure', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      final result = await state.login(phoneNumber: '9876543210', password: 'wrong');
      expect(result, isFalse);
      expect(state.status, AuthStatus.unauthenticated);
      expect(state.lastErrorMessage, isNotNull);
      expect(state.lastErrorMessage!.toLowerCase(), contains('phone number or password'));
    });
  });

  group('AuthState.register', () {
    test('transitions to authenticated on success', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      final result = await state.register(
        phoneNumber: '9876543210',
        password: 'Str0ngPass',
        fullName: 'Test Farmer',
        preferredLanguageCode: 'en',
        consents: [ConsentInput('terms_of_service', '1.0'), ConsentInput('privacy_policy', '1.0')],
      );
      expect(result, isTrue);
      expect(state.status, AuthStatus.authenticated);
    });

    test('surfaces duplicate-account error on failure', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      final result = await state.register(
        phoneNumber: '9876543210',
        password: 'Str0ngPass',
        fullName: 'Test Farmer',
        preferredLanguageCode: 'en',
        consents: [ConsentInput('terms_of_service', '1.0'), ConsentInput('privacy_policy', '1.0')],
      );
      expect(result, isFalse);
      expect(state.lastErrorMessage!.toLowerCase(), contains('already exists'));
    });
  });

  group('AuthState.restoreSession', () {
    test('authenticated when a session can be restored', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      await state.restoreSession();
      expect(state.status, AuthStatus.authenticated);
    });

    test('unauthenticated when no session exists', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      await state.restoreSession();
      expect(state.status, AuthStatus.unauthenticated);
    });
  });

  group('AuthState.logout', () {
    test('transitions to unauthenticated', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      await state.login(phoneNumber: '9876543210', password: 'Str0ngPass');
      await state.logout();
      expect(state.status, AuthStatus.unauthenticated);
    });
  });
}
