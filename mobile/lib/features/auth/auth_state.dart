import 'package:flutter/foundation.dart';

import '../../core/friendly_error.dart';
import '../../l10n/app_localizations.dart';
import 'auth_repository.dart';

enum AuthStatus { unknown, authenticating, authenticated, unauthenticated }

/// App-wide auth state. Screens read this via Provider rather than each
/// managing their own "am I logged in" flag - one source of truth avoids
/// the splash/login/home screens disagreeing about session state.
class AuthState extends ChangeNotifier {
  final AuthRepository _repository;

  AuthState({required AuthRepository repository}) : _repository = repository;

  AuthStatus status = AuthStatus.unknown;

  /// The raw error from the last failed auth call, kept unformatted since
  /// this class has no BuildContext/AppLocalizations of its own - callers
  /// format it via [errorMessage] using their own screen's l10n instance.
  Object? lastError;

  String? errorMessage(AppLocalizations l10n) => lastError == null ? null : FriendlyError.from(lastError!, l10n);

  /// Called once at app startup (from the splash screen) to attempt
  /// restoring a previous session before deciding whether to show login.
  Future<void> restoreSession() async {
    status = AuthStatus.authenticating;
    notifyListeners();

    final tokens = await _repository.restoreSession();
    status = tokens != null ? AuthStatus.authenticated : AuthStatus.unauthenticated;
    notifyListeners();
  }

  Future<bool> login({required String phoneNumber, required String password}) async {
    status = AuthStatus.authenticating;
    lastError = null;
    notifyListeners();

    try {
      await _repository.login(phoneNumber: phoneNumber, password: password);
      status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      status = AuthStatus.unauthenticated;
      lastError = e;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String phoneNumber,
    required String password,
    required String fullName,
    required String preferredLanguageCode,
    required List<ConsentInput> consents,
  }) async {
    status = AuthStatus.authenticating;
    lastError = null;
    notifyListeners();

    try {
      await _repository.register(
        phoneNumber: phoneNumber,
        password: password,
        fullName: fullName,
        preferredLanguageCode: preferredLanguageCode,
        consents: consents,
      );
      status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      status = AuthStatus.unauthenticated;
      lastError = e;
      notifyListeners();
      return false;
    }
  }

  Future<bool> resetPassword({required String phoneNumber, required String newPassword}) async {
    status = AuthStatus.authenticating;
    lastError = null;
    notifyListeners();

    try {
      await _repository.resetPassword(phoneNumber: phoneNumber, newPassword: newPassword);
      status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      status = AuthStatus.unauthenticated;
      lastError = e;
      notifyListeners();
      return false;
    }
  }

  Future<bool> changePassword({required String currentPassword, required String newPassword}) async {
    lastError = null;
    try {
      await _repository.changePassword(currentPassword: currentPassword, newPassword: newPassword);
      return true;
    } catch (e) {
      lastError = e;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
