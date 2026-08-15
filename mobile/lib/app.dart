import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'core/flutter_tts_voice_service.dart';
import 'core/voice_service.dart';
import 'features/auth/auth_repository.dart';
import 'features/auth/auth_state.dart';
import 'features/auth/farmer_repository.dart';
import 'features/auth/register_screen.dart';
import 'features/farm/crop_repository.dart';
import 'features/farm/farm_repository.dart';
import 'features/farm/plot_repository.dart';
import 'features/crop_photo/crop_photo_repository.dart';
import 'features/daily_briefing/daily_briefing_repository.dart';
import 'features/expert_case/case_repository.dart';
import 'features/task/task_repository.dart';
import 'features/crop_photo/network_status_checker.dart';
import 'features/crop_photo/pending_upload_queue.dart';
import 'l10n/app_localizations.dart';
import 'main_navigation_shell.dart';
import 'screens/login_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/welcome_screen.dart';
import 'theme/app_theme.dart';

class SmartFarmerApp extends StatelessWidget {
  const SmartFarmerApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Single shared ApiClient instance so the access token set by
    // AuthRepository is visible to every other repository (e.g.
    // FarmerRepository) built on top of it.
    final apiClient = ApiClient();
    final authRepository = AuthRepository(apiClient: apiClient);

    return MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: apiClient),
        Provider<AuthRepository>.value(value: authRepository),
        Provider<FarmerRepository>(create: (_) => FarmerRepository(apiClient: apiClient)),
        Provider<FarmRepository>(create: (_) => FarmRepository(apiClient: apiClient)),
        Provider<PlotRepository>(create: (_) => PlotRepository(apiClient: apiClient)),
        Provider<CropRepository>(create: (_) => CropRepository(apiClient: apiClient)),
        Provider<CropPhotoRepository>(create: (_) => CropPhotoRepository(apiClient: apiClient)),
        Provider<CaseRepository>(create: (_) => CaseRepository(apiClient: apiClient)),
        Provider<TaskRepository>(create: (_) => TaskRepository(apiClient: apiClient)),
        Provider<DailyBriefingRepository>(create: (_) => DailyBriefingRepository(apiClient: apiClient)),
        Provider<VoiceService>(create: (_) => FlutterTtsVoiceService()),
        Provider<NetworkStatusChecker>(create: (_) => NetworkStatusChecker()),
        ChangeNotifierProvider<PendingUploadQueue>(create: (_) => PendingUploadQueue()),
        ChangeNotifierProvider<AuthState>(create: (_) => AuthState(repository: authRepository)),
      ],
      child: MaterialApp(
        title: 'Smart Farmer',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [Locale('en')],
        initialRoute: '/splash',
        routes: {
          '/splash': (_) => const SplashScreen(),
          '/welcome': (_) => const WelcomeScreen(),
          '/register': (_) => const RegisterScreen(),
          '/login': (_) => const LoginScreen(),
          '/home': (_) => const MainNavigationShell(),
        },
      ),
    );
  }
}
