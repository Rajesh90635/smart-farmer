import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import 'camera_capture_screen.dart';

/// Shown once, before the farmer opens the camera - simple, icon-led
/// guidance (Requirement 8), all text from AppLocalizations, never
/// hard-coded (Requirement 33/38).
class PhotoGuidanceScreen extends StatelessWidget {
  final String sessionId;
  const PhotoGuidanceScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final tips = <(IconData, String)>[
      (Icons.crop_free, l10n.guidanceKeepLeafInFrame),
      (Icons.wb_shade, l10n.guidanceAvoidShadows),
      (Icons.wb_sunny, l10n.guidanceAvoidSunlight),
      (Icons.pan_tool_alt, l10n.guidanceHoldSteady),
      (Icons.center_focus_strong, l10n.guidanceCaptureAffectedArea),
      (Icons.water_drop, l10n.guidanceAvoidWaterDroplets),
      (Icons.photo_camera, l10n.guidanceCloseButComplete),
    ];

    return Scaffold(
      appBar: AppBar(title: Text(l10n.checkCropTitle)),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: tips
                    .map((tip) => ListTile(
                          leading: Icon(tip.$1, size: 32),
                          title: Text(tip.$2, style: const TextStyle(fontSize: 16)),
                        ))
                    .toList(),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: ElevatedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => CameraCaptureScreen(sessionId: sessionId)),
                ),
                icon: const Icon(Icons.camera_alt),
                label: Text(l10n.takePhotoButton),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
