import '../../l10n/app_localizations.dart';

/// Client-side validation mirrors the backend's rules (see
/// backend/app/schemas/auth.py) so a farmer sees feedback immediately
/// rather than waiting for a round trip - but the backend re-validates
/// everything regardless, since client-side validation is never trusted
/// as the actual security/data-integrity boundary.
class Validators {
  static final _phonePattern = RegExp(r'^\+?[0-9]{7,15}$');

  static String? Function(String?) phoneNumber(AppLocalizations l10n) {
    return (value) {
      if (value == null || value.isEmpty) return l10n.validatorPhoneRequiredError;
      if (!_phonePattern.hasMatch(value)) return l10n.validatorPhoneInvalidError;
      return null;
    };
  }

  static String? Function(String?) password(AppLocalizations l10n) {
    return (value) {
      if (value == null || value.isEmpty) return l10n.passwordRequiredError;
      if (value.length < 8) return l10n.validatorPasswordTooShortError;
      final hasLetter = value.contains(RegExp(r'[A-Za-z]'));
      final hasDigit = value.contains(RegExp(r'[0-9]'));
      if (!hasLetter || !hasDigit) return l10n.validatorPasswordNeedsLetterAndNumberError;
      final hasUpper = value.contains(RegExp(r'[A-Z]'));
      if (!hasUpper) return l10n.validatorPasswordNeedsUppercaseError;
      final hasSpecial = value.contains(RegExp(r'[^A-Za-z0-9]'));
      if (!hasSpecial) return l10n.validatorPasswordNeedsSpecialCharError;
      return null;
    };
  }

  static String? Function(String?) fullName(AppLocalizations l10n) {
    return (value) {
      if (value == null || value.trim().length < 2) return l10n.validatorNameRequiredError;
      return null;
    };
  }
}
