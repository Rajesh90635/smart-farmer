/// Client-side validation mirrors the backend's rules (see
/// backend/app/schemas/auth.py) so a farmer sees feedback immediately
/// rather than waiting for a round trip - but the backend re-validates
/// everything regardless, since client-side validation is never trusted
/// as the actual security/data-integrity boundary.
class Validators {
  static final _phonePattern = RegExp(r'^\+?[0-9]{7,15}$');

  static String? phoneNumber(String? value) {
    if (value == null || value.isEmpty) return 'Please enter your phone number.';
    if (!_phonePattern.hasMatch(value)) return 'Please enter a valid phone number (7-15 digits).';
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Please enter a password.';
    if (value.length < 8) return 'Password must be at least 8 characters.';
    final hasLetter = value.contains(RegExp(r'[A-Za-z]'));
    final hasDigit = value.contains(RegExp(r'[0-9]'));
    if (!hasLetter || !hasDigit) return 'Password must contain a letter and a number.';
    return null;
  }

  static String? fullName(String? value) {
    if (value == null || value.trim().length < 2) return 'Please enter your name.';
    return null;
  }
}
