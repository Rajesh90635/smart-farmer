import 'package:flutter/material.dart';

/// Central theme definition. Business screens must reference these values
/// (or MaterialTheme defaults derived from them) rather than hard-coding
/// colors/text styles, so large-tap-target and contrast rules from the
/// approved UX spec stay consistent app-wide instead of being redone per
/// screen.
class AppTheme {
  AppTheme._();

  static const Color primaryGreen = Color(0xFF2E7D32);
  static const Color accentAmber = Color(0xFFFFA000);
  static const Color errorRed = Color(0xFFC62828);

  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        error: errorRed,
      ),
    );

    return base.copyWith(
      // Large tap targets per the accessibility principle in the approved
      // UX spec - minimum 48dp touch targets, generous default padding.
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size.fromHeight(56),
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      textTheme: _scaleTextTheme(base.textTheme, 1.1),
    );
  }

  static TextTheme _scaleTextTheme(TextTheme theme, double factor) {
    TextStyle? scale(TextStyle? style) {
      if (style == null || style.fontSize == null) return style;
      return style.copyWith(fontSize: style.fontSize! * factor);
    }

    return TextTheme(
      displayLarge: scale(theme.displayLarge),
      displayMedium: scale(theme.displayMedium),
      displaySmall: scale(theme.displaySmall),
      headlineLarge: scale(theme.headlineLarge),
      headlineMedium: scale(theme.headlineMedium),
      headlineSmall: scale(theme.headlineSmall),
      titleLarge: scale(theme.titleLarge),
      titleMedium: scale(theme.titleMedium),
      titleSmall: scale(theme.titleSmall),
      bodyLarge: scale(theme.bodyLarge),
      bodyMedium: scale(theme.bodyMedium),
      bodySmall: scale(theme.bodySmall),
      labelLarge: scale(theme.labelLarge),
      labelMedium: scale(theme.labelMedium),
      labelSmall: scale(theme.labelSmall),
    );
  }
}