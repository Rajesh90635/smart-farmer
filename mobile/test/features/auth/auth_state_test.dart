import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/auth/auth_repository.dart';
import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations_en.dart';

/// Overrides every network-touching method so AuthState's own logic
/// (status transitions, error surfacing) can be tested without a real
/// backend, secure storage plugin, or HTTP stack - none of which are
/// available in a plain widget-test environment.
class FakeAuthRepository extends AuthRepository {
  bool shouldSucceed;
  // Independent of shouldSucceed only so a test can exercise "OTP request
  // succeeded, but the final reset itself failed (e.g. wrong code)" -
  // every other method here still follows shouldSucceed alone.
  final bool? resetPasswordSucceeds;
  FakeAuthRepository({this.shouldSucceed = true, this.resetPasswordSucceeds}) : super(apiClient: ApiClient());

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

  @override
  Future<void> requestPasswordResetOtp({required String phoneNumber}) async {
    if (!shouldSucceed) {
      throw ApiException('No account found', statusCode: 404, code: 'NOT_FOUND');
    }
  }

  @override
  Future<AuthTokens> resetPassword({
    required String phoneNumber,
    required String newPassword,
    required String otpCode,
  }) async {
    if (!(resetPasswordSucceeds ?? shouldSucceed)) {
      throw ApiException('Invalid or expired code', statusCode: 401, code: 'INVALID_OTP');
    }
    return AuthTokens(accessToken: 'fake-access', refreshToken: 'fake-refresh');
  }
}

void main() {
  final l10n = AppLocalizationsEn();

  group('AuthState.login', () {
    test('transitions to authenticated on success', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      final result = await state.login(phoneNumber: '9876543210', password: 'Str0ngPass');
      expect(result, isTrue);
      expect(state.status, AuthStatus.authenticated);
      expect(state.errorMessage(l10n), isNull);
    });

    test('transitions to unauthenticated with a friendly error on failure', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      final result = await state.login(phoneNumber: '9876543210', password: 'wrong');
      expect(result, isFalse);
      expect(state.status, AuthStatus.unauthenticated);
      expect(state.errorMessage(l10n), isNotNull);
      expect(state.errorMessage(l10n)!.toLowerCase(), contains('phone number or password'));
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
      expect(state.errorMessage(l10n)!.toLowerCase(), contains('already exists'));
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

  group('AuthState.requestPasswordResetOtp', () {
    test('succeeds without changing auth status', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      final result = await state.requestPasswordResetOtp(phoneNumber: '9876543210');
      expect(result, isTrue);
      expect(state.errorMessage(l10n), isNull);
    });

    test('surfaces a friendly error on failure', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      final result = await state.requestPasswordResetOtp(phoneNumber: '9876543210');
      expect(result, isFalse);
      expect(state.errorMessage(l10n), isNotNull);
    });
  });

  group('AuthState.resetPassword', () {
    test('transitions to authenticated on a valid OTP', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: true));
      final result = await state.resetPassword(phoneNumber: '9876543210', newPassword: 'NewPass1!', otpCode: '123456');
      expect(result, isTrue);
      expect(state.status, AuthStatus.authenticated);
    });

    test('surfaces an invalid-OTP error on failure', () async {
      final state = AuthState(repository: FakeAuthRepository(shouldSucceed: false));
      final result = await state.resetPassword(phoneNumber: '9876543210', newPassword: 'NewPass1!', otpCode: 'wrong');
      expect(result, isFalse);
      expect(state.status, AuthStatus.unauthenticated);
      expect(state.errorMessage(l10n), isNotNull);
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
