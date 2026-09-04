import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/auth/validators.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations_en.dart';

void main() {
  final l10n = AppLocalizationsEn();

  group('Validators.phoneNumber', () {
    test('rejects empty', () {
      expect(Validators.phoneNumber(l10n)(''), isNotNull);
    });
    test('rejects too short', () {
      expect(Validators.phoneNumber(l10n)('123'), isNotNull);
    });
    test('accepts a valid 10-digit number', () {
      expect(Validators.phoneNumber(l10n)('9876543210'), isNull);
    });
    test('accepts a leading +', () {
      expect(Validators.phoneNumber(l10n)('+919876543210'), isNull);
    });
  });

  group('Validators.password', () {
    test('rejects too short', () {
      expect(Validators.password(l10n)('abc123'), isNotNull);
    });
    test('rejects no digit', () {
      expect(Validators.password(l10n)('alllettersnodigit'), isNotNull);
    });
    test('rejects no letter', () {
      expect(Validators.password(l10n)('12345678'), isNotNull);
    });
    test('accepts a strong password', () {
      expect(Validators.password(l10n)('Str0ngPass!'), isNull);
    });
  });

  group('Validators.fullName', () {
    test('rejects empty', () {
      expect(Validators.fullName(l10n)(''), isNotNull);
    });
    test('rejects single character', () {
      expect(Validators.fullName(l10n)('A'), isNotNull);
    });
    test('accepts a real name', () {
      expect(Validators.fullName(l10n)('Farmer Name'), isNull);
    });
  });
}
