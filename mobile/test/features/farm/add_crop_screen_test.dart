import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_farmer_mobile/core/api_client.dart';
import 'package:smart_farmer_mobile/features/farm/add_crop_screen.dart';
import 'package:smart_farmer_mobile/features/farm/crop_repository.dart';
import 'package:smart_farmer_mobile/features/farm/farm_models.dart';
import 'package:smart_farmer_mobile/l10n/app_localizations.dart';

/// D11-02 (docs/audit/FINAL_CANONICAL_group_A.md): a re-sow-aware
/// confirmation distinct from generic crop creation.
class FakeCropRepository extends CropRepository {
  final List<CropCycle> cyclesForPlot;
  FakeCropRepository({this.cyclesForPlot = const []}) : super(apiClient: ApiClient());

  @override
  Future<List<CropCycle>> listCropCyclesForPlot(String plotId) async => cyclesForPlot;

  @override
  Future<List<CropMaster>> searchCropMaster(String? query) async => [];
}

CropCycle _cycleWithStatus(String status) => CropCycle.fromJson({
      'id': 'cycle-1',
      'plot_id': 'plot-1',
      'crop': {'id': 'crop-1', 'name': 'Tomato'},
      'season': null,
      'sowing_date': '2026-01-01',
      'expected_harvest_date': null,
      'actual_harvest_date': null,
      'cultivation_status': status,
      'seed_variety': null,
      'variety_id': null,
      'lessons_learned': null,
    });

Widget _wrap(CropRepository repo) {
  return MultiProvider(
    providers: [Provider<CropRepository>.value(value: repo)],
    child: const MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: AddCropScreen(plotId: 'plot-1'),
    ),
  );
}

void main() {
  testWidgets('prompts to confirm re-sow when the plot has a recent cancelled cycle', (tester) async {
    await tester.pumpWidget(_wrap(FakeCropRepository(cyclesForPlot: [_cycleWithStatus('cancelled')])));
    await tester.pumpAndSettle();

    expect(find.text('Re-sow after failure?'), findsOneWidget);
    expect(find.textContaining('Tomato'), findsWidgets);
  });

  testWidgets('does not prompt when the plot has no cancelled cycle', (tester) async {
    await tester.pumpWidget(_wrap(FakeCropRepository(cyclesForPlot: [_cycleWithStatus('planned')])));
    await tester.pumpAndSettle();

    expect(find.text('Re-sow after failure?'), findsNothing);
  });

  testWidgets('confirming the prompt shows the linked indicator', (tester) async {
    await tester.pumpWidget(_wrap(FakeCropRepository(cyclesForPlot: [_cycleWithStatus('cancelled')])));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Yes, link it'));
    await tester.pumpAndSettle();

    expect(find.text('Linked as re-sow of the previous cycle'), findsOneWidget);
  });

  testWidgets('declining the prompt does not show the linked indicator', (tester) async {
    await tester.pumpWidget(_wrap(FakeCropRepository(cyclesForPlot: [_cycleWithStatus('cancelled')])));
    await tester.pumpAndSettle();

    await tester.tap(find.text('No'));
    await tester.pumpAndSettle();

    expect(find.text('Linked as re-sow of the previous cycle'), findsNothing);
  });
}
