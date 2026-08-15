import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/features/auth/validators.dart';

void main() {
  group('Validators.phoneNumber', () {
    test('rejects empty', () {
      expect(Validators.phoneNumber(''), isNotNull);
    });
    test('rejects too short', () {
      expect(Validators.phoneNumber('123'), isNotNull);
    });
    test('accepts a valid 10-digit number', () {
      expect(Validators.phoneNumber('9876543210'), isNull);
    });
    test('accepts a leading +', () {
      expect(Validators.phoneNumber('+919876543210'), isNull);
    });
  });

  group('Validators.password', () {
    test('rejects too short', () {
      expect(Validators.password('abc123'), isNotNull);
    });
    test('rejects no digit', () {
      expect(Validators.password('alllettersnodigit'), isNotNull);
    });
    test('rejects no letter', () {
      expect(Validators.password('12345678'), isNotNull);
    });
    test('accepts a strong password', () {
      expect(Validators.password('Str0ngPass'), isNull);
    });
  });

  group('Validators.fullName', () {
    test('rejects empty', () {
      expect(Validators.fullName(''), isNotNull);
    });
    test('rejects single character', () {
      expect(Validators.fullName('A'), isNotNull);
    });
    test('accepts a real name', () {
      expect(Validators.fullName('Farmer Name'), isNull);
    });
  });
}
