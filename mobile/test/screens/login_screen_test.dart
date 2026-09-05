import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/auth/auth_state.dart';
import 'package:smart_farmer_mobile/features/crop_photo/crop_photo_repository.dart';
import 'package:smart_farmer_mobile/features/crop_photo/network_status_checker.dart';
import 'package:smart_farmer_mobile/features/crop_photo/pending_upload_queue.dart';
import 'package:smart_farmer_mobile/features/crop_photo/sync_coordinator.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';
import 'package:smart_farmer_mobile/screens/login_screen.dart';

import '../features/auth/auth_state_test.dart' show FakeAuthRepository;

/// Login success (see login_screen.dart) reads NetworkStatusChecker via
/// SyncCoordinator, which delegates to connectivity_plus's platform
/// channel - unavailable in a widget test. Faking the federated-plugin
/// interface (the same seam real platform implementations register
/// through) reports "offline", so syncNow() returns immediately without
/// ever touching CropPhotoRepository/ApiClient.
class FakeOfflineConnectivityPlatform extends ConnectivityPlatform {
  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => [ConnectivityResult.none];

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged => const Stream.empty();
}

Widget _wrap(AuthState authState, Map<String, WidgetBuilder> routes) {
  final queue = PendingUploadQueue();
  return MultiProvider(
    providers: [
      ChangeNotifierProvider<AuthState>.value(value: authState),
      ChangeNotifierProvider<PendingUploadQueue>.value(value: queue),
      Provider<SyncCoordinator>(
        create: (_) => SyncCoordinator(
          queue: queue,
          networkChecker: NetworkStatusChecker(),
          repository: CropPhotoRepository(apiClient: ApiClient()),
        ),
      ),
    ],
    child: MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('en')],
      home: const LoginScreen(),
      routes: routes,
    ),
  );
}

void main() {
  ConnectivityPlatform.instance = FakeOfflineConnectivityPlatform();

  testWidgets('renders phone and password fields', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), const {}));

    expect(find.text('Phone number'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Log in'), findsWidgets);
  });

  testWidgets('shows validation error when password is empty', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.text('Please enter your password.'), findsOneWidget);
  });

  testWidgets('successful login navigates to /home', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: true)), {
      '/home': (_) => const Scaffold(body: Text('Home Screen Placeholder')),
    }));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'Str0ngPass');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.text('Home Screen Placeholder'), findsOneWidget);
  });

  testWidgets('failed login shows a snackbar with the friendly error', (tester) async {
    await tester.pumpWidget(_wrap(AuthState(repository: FakeAuthRepository(shouldSucceed: false)), const {}));

    await tester.enterText(find.widgetWithText(TextFormField, 'Phone number'), '9876543210');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'wrong');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log in'));
    await tester.pumpAndSettle();

    expect(find.byType(SnackBar), findsOneWidget);
  });
}
