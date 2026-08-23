/// Environment configuration, read at build time via --dart-define so the
/// same codebase points at local Docker Compose, a pilot host, or
/// production without a code change.
///
/// Example (local dev, backend running via docker-compose on the same
/// machine, Android emulator's special loopback address):
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
class AppConfig {
  AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  static const String environment = String.fromEnvironment(
    'APP_ENV',
    defaultValue: 'development',
  );

  static bool get isDevelopment => environment == 'development';
}
