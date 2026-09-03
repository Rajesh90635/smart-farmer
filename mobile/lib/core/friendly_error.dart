import 'api_client.dart';

/// Converts backend error codes (see backend docs/API_CONVENTIONS.md) into
/// plain-language messages a farmer can act on. The raw technical message
/// from the backend is never shown directly in the UI — only used for
/// developer logs.
class FriendlyError {
  static String from(Object error) {
    if (error is ApiException) {
      switch (error.code) {
        case 'INVALID_CREDENTIALS':
          return 'That phone number or password isn\'t right. Please try again.';
        case 'ACCOUNT_DISABLED':
          return 'This account is not active. Please contact support.';
        case 'DUPLICATE_ACCOUNT':
          return 'An account with this phone number already exists. Try logging in instead.';
        case 'VALIDATION_ERROR':
          return 'Please check the information you entered and try again.';
        case 'SESSION_EXPIRED':
          return 'Your session has ended. Please log in again.';
        case 'RATE_LIMITED':
          return 'Too many attempts. Please wait a few minutes and try again.';
        case 'UNAUTHORIZED':
        case 'FORBIDDEN':
          return 'You need to log in again to continue.';
        default:
          return 'Something went wrong. Please try again.';
      }
    }
    return 'Something went wrong. Please check your connection and try again.';
  }
}
