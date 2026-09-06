import 'dart:math';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// A random, per-install identifier — NOT a hardware fingerprint — used only
/// so the backend can tell "this exact app install has logged in here
/// before" (D78-13, docs/audit/FINAL_CANONICAL_group_D.md's new-device-login
/// alerting). Persists across logout (SecureTokenStorage.clear() only
/// touches its own two keys, not this one) since a later login from the
/// same install must still be recognized as the same device; naturally
/// resets on reinstall or if the OS clears app storage, which is correct -
/// that genuinely is a new install as far as this signal is concerned.
class DeviceIdentity {
  static const _deviceIdKey = 'device_id';

  final FlutterSecureStorage _storage;

  DeviceIdentity({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  Future<String> readOrCreate() async {
    final existing = await _storage.read(key: _deviceIdKey);
    if (existing != null) return existing;
    final generated = _generate();
    await _storage.write(key: _deviceIdKey, value: generated);
    return generated;
  }

  static String _generate() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }
}
