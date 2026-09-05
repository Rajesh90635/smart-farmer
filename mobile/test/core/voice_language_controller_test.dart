import 'package:flutter_test/flutter_test.dart';
import 'package:smart_farmer_mobile/core/location_language_resolver.dart';
import 'package:smart_farmer_mobile/core/storage/voice_language_storage.dart';
import 'package:smart_farmer_mobile/core/voice_language_controller.dart';

class _FakeStorage implements VoiceLanguageStorage {
  String? saved;
  @override
  Future<String?> readMode() async => saved;
  @override
  Future<void> saveMode(String mode) async => saved = mode;
}

class _FakeLocationResolver implements LocationLanguageResolver {
  final String? result;
  int callCount = 0;
  _FakeLocationResolver(this.result);

  @override
  Future<String?> resolveLanguageCode() async {
    callCount++;
    return result;
  }
}

void main() {
  group('VoiceLanguageController', () {
    test('defaults to manual mode', () {
      final controller = VoiceLanguageController(storage: _FakeStorage());
      expect(controller.mode, VoiceLanguageMode.manual);
    });

    test('loadSaved restores a previously persisted location mode', () async {
      final storage = _FakeStorage()..saved = VoiceLanguageMode.location.name;
      final controller = VoiceLanguageController(storage: storage);
      await controller.loadSaved();
      expect(controller.mode, VoiceLanguageMode.location);
    });

    test('setMode persists the choice and notifies listeners', () async {
      final storage = _FakeStorage();
      final controller = VoiceLanguageController(storage: storage);
      var notified = false;
      controller.addListener(() => notified = true);

      await controller.setMode(VoiceLanguageMode.location);

      expect(controller.mode, VoiceLanguageMode.location);
      expect(storage.saved, VoiceLanguageMode.location.name);
      expect(notified, isTrue);
    });

    test('manual mode never consults the location resolver, always returns the content language as-is', () async {
      final locationResolver = _FakeLocationResolver('te');
      final controller = VoiceLanguageController(storage: _FakeStorage(), locationResolver: locationResolver);

      final result = await controller.resolveLanguageCode(contentLanguageCode: 'hi');

      expect(result, 'hi');
      expect(locationResolver.callCount, 0);
    });

    test('location mode returns the detected language when detection succeeds', () async {
      final controller = VoiceLanguageController(storage: _FakeStorage(), locationResolver: _FakeLocationResolver('kn'));
      await controller.setMode(VoiceLanguageMode.location);

      final result = await controller.resolveLanguageCode(contentLanguageCode: 'en');

      expect(result, 'kn');
    });

    test('location mode falls back to the content language when detection fails, never blocks Listen', () async {
      final controller = VoiceLanguageController(storage: _FakeStorage(), locationResolver: _FakeLocationResolver(null));
      await controller.setMode(VoiceLanguageMode.location);

      final result = await controller.resolveLanguageCode(contentLanguageCode: 'ml');

      expect(result, 'ml');
    });
  });
}
