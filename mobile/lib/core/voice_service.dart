/// VoiceService: the ONLY abstraction any screen should depend on for
/// speech output - never flutter_tts directly. This is what lets a future
/// swap (a different TTS package, or a genuinely offline neural TTS if
/// one is ever vetted) happen behind one interface, matching the same
/// pattern already established for ApiClient/AIProvider/WeatherProvider
/// throughout this project.
///
/// THE ABSOLUTE SAFETY RULE: this class NEVER generates or selects what
/// text to speak - every caller passes in text that ALREADY came from an
/// authoritative source (a backend response, or a static localized UI
/// string). There is no method on this interface that takes anything
/// other than a plain String to speak verbatim - structurally, this
/// class cannot "invent" a diagnosis, price, or weather reading, because
/// it has no code path that produces text on its own.
abstract class VoiceService {
  /// True if the device's TTS engine reports itself ready to speak at
  /// all - checked once at startup, not before every single speak() call
  /// (mirroring how NetworkStatusChecker is used elsewhere).
  Future<bool> isAvailable();

  /// Returns true if speech was actually started. False (not an
  /// exception) means the caller should fall back to text-only display -
  /// this mirrors the same "available: bool, don't raise" convention
  /// already used by every provider abstraction in this codebase.
  Future<bool> speak(String text, {required String languageCode});

  Future<void> stop();
}
