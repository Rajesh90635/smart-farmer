import '../../core/api_client.dart';
import '../../core/storage/secure_token_storage.dart';

class AuthTokens {
  final String accessToken;
  final String refreshToken;
  AuthTokens({required this.accessToken, required this.refreshToken});
}

class ConsentInput {
  final String consentType;
  final String version;
  ConsentInput(this.consentType, this.version);

  Map<String, dynamic> toJson() => {'consent_type': consentType, 'version': version};
}

class AuthRepository {
  final ApiClient _apiClient;
  final SecureTokenStorage _tokenStorage;

  AuthRepository({required ApiClient apiClient, SecureTokenStorage? tokenStorage})
      : _apiClient = apiClient,
        _tokenStorage = tokenStorage ?? SecureTokenStorage();

  Future<AuthTokens> register({
    required String phoneNumber,
    required String password,
    required String fullName,
    required String preferredLanguageCode,
    String? preferredVoiceLanguageCode,
    required List<ConsentInput> consents,
  }) async {
    final response = await _apiClient.post('/auth/register', body: {
      'phone_number': phoneNumber,
      'password': password,
      'full_name': fullName,
      'preferred_language_code': preferredLanguageCode,
      if (preferredVoiceLanguageCode != null) 'preferred_voice_language_code': preferredVoiceLanguageCode,
      'consents': consents.map((c) => c.toJson()).toList(),
    });
    return _persistTokens(response);
  }

  Future<AuthTokens> login({required String phoneNumber, required String password}) async {
    final response = await _apiClient.post('/auth/login', body: {
      'phone_number': phoneNumber,
      'password': password,
    });
    return _persistTokens(response);
  }

  /// Attempts to restore a session from secure storage. Returns null if
  /// there is no stored session or the refresh call fails (e.g. the
  /// refresh token was revoked or expired) - the caller should treat null
  /// as "show the login screen," never assume a stale token is still good.
  Future<AuthTokens?> restoreSession() async {
    final storedRefreshToken = await _tokenStorage.readRefreshToken();
    if (storedRefreshToken == null) return null;

    try {
      final response = await _apiClient.post('/auth/refresh', body: {'refresh_token': storedRefreshToken});
      return _persistTokens(response);
    } on ApiException {
      await _tokenStorage.clear();
      return null;
    }
  }

  Future<void> changePassword({required String currentPassword, required String newPassword}) async {
    await _apiClient.post('/auth/change-password', body: {
      'current_password': currentPassword,
      'new_password': newPassword,
    });
  }

  Future<void> logout() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken != null) {
      try {
        await _apiClient.post('/auth/logout', body: {'refresh_token': refreshToken});
      } on ApiException {
        // Even if the server call fails (e.g. already offline), clear the
        // local session - a farmer tapping "logout" must always end up
        // logged out on this device.
      }
    }
    await _tokenStorage.clear();
    _apiClient.setAccessToken(null);
  }

  Future<AuthTokens> _persistTokens(Map<String, dynamic> response) async {
    final accessToken = response['access_token'] as String;
    final refreshToken = response['refresh_token'] as String;
    await _tokenStorage.saveTokens(accessToken: accessToken, refreshToken: refreshToken);
    _apiClient.setAccessToken(accessToken);
    return AuthTokens(accessToken: accessToken, refreshToken: refreshToken);
  }
}
