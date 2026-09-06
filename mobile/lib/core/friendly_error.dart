import 'api_client.dart';
import 'offline/pending_write_queue.dart';
import '../l10n/app_localizations.dart';

/// Converts backend error codes (see backend docs/API_CONVENTIONS.md) into
/// plain-language messages a farmer can act on. The raw technical message
/// from the backend is never shown directly in the UI — only used for
/// developer logs.
class FriendlyError {
  static String from(Object error, AppLocalizations l10n) {
    // D84-01 (docs/audit/FINAL_CANONICAL_group_D.md): the uniform outcome
    // of ApiClient's 401 -> silent-refresh interceptor once that refresh
    // has already failed - reuses the SAME wording as the backend's own
    // SESSION_EXPIRED error code (see the ApiException branch below), one
    // wording for the same underlying farmer-facing fact either way.
    if (error is SessionExpiredException) {
      return l10n.errorSessionExpired;
    }
    // D81-01 (docs/audit/FINAL_CANONICAL_group_D.md): a deliberately
    // distinct, reassuring message - this is NOT a failure, the write was
    // saved locally and will be sent automatically once back online.
    if (error is QueuedForSyncException) {
      return l10n.errorQueuedForSync;
    }
    if (error is ApiException) {
      switch (error.code) {
        case 'INVALID_CREDENTIALS':
          return l10n.errorInvalidCredentials;
        case 'ACCOUNT_DISABLED':
          return l10n.errorAccountDisabled;
        case 'DUPLICATE_ACCOUNT':
          return l10n.errorDuplicateAccount;
        case 'INCORRECT_CURRENT_PASSWORD':
          return l10n.errorIncorrectCurrentPassword;
        case 'VALIDATION_ERROR':
          return l10n.errorValidation;
        case 'SESSION_EXPIRED':
          return l10n.errorSessionExpired;
        case 'RATE_LIMITED':
          return l10n.errorRateLimited;
        case 'INVALID_OTP':
          return l10n.errorInvalidOtp;
        case 'OTP_DELIVERY_FAILED':
          return l10n.errorOtpDeliveryFailed;
        case 'UNAUTHORIZED':
        case 'FORBIDDEN':
          return l10n.errorUnauthorized;
        default:
          return l10n.errorGeneric;
      }
    }
    return l10n.errorGenericConnection;
  }
}
