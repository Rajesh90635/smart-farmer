import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import '../features/auth/farmer_repository.dart';
import 'locale_controller.dart';

/// Applies the farmer's backend-saved `preferred_language_code` to this
/// device's [LocaleController]. Needed because [LocaleController] only
/// knows about this device's own on-device saved choice (or the English
/// default) - a farmer who chose a language on a different device, or is
/// logging into this device for the first time, would otherwise see the
/// app in the wrong language until they manually revisit the Profile
/// screen. Call after session restoration and after a fresh login.
///
/// Best-effort: never throws. A failed/offline profile fetch simply leaves
/// whichever locale is already active (on-device saved choice, or English).
Future<void> syncLocaleFromBackendProfile(BuildContext context) async {
  try {
    final profile = await context.read<FarmerRepository>().getMyProfile();
    if (!context.mounted) return;
    await context.read<LocaleController>().setLocale(profile.preferredLanguageCode);
  } catch (_) {
    // Offline or transient failure - not fatal to login/session restoration.
  }
}
