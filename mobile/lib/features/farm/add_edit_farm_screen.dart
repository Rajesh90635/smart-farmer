import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/nominatim_reverse_geocoder.dart';
import '../../l10n/app_localizations.dart';
import 'farm_models.dart';
import 'farm_repository.dart';
import 'location_models.dart';
import 'location_repository.dart';

/// Add or edit a farm. Location is captured as raw GPS coordinates plus an
/// optional State -> District -> Mandal -> Village selection (see
/// backend/app/models/location.py) - no paid map SDK either way.
///
/// "Use Current Location" reads the device's real GPS position (via the
/// `geolocator` plugin) and then makes a best-effort attempt to match that
/// position, through the free public OpenStreetMap Nominatim reverse-geocoding
/// API, against this app's own State/District/Mandal/Village master data.
/// That match is never assumed correct: Mandal/Village have no seed data in
/// this project yet, India has no standard OSM tag for "mandal", and even
/// state/district name matching is a plain-text comparison - every level the
/// lookup can't confidently match is simply left for the farmer to pick
/// manually, exactly as if they had opened the screen with no GPS at all.
///
/// As before, this location section (and hence the dropdowns and the GPS
/// button) is only offered when creating a new farm - editing an existing
/// farm's location was never wired into FarmRepository.updateFarm and
/// remains out of scope here, unchanged from the prior behavior.
class AddEditFarmScreen extends StatefulWidget {
  final Farm? existingFarm;
  const AddEditFarmScreen({super.key, this.existingFarm});

  @override
  State<AddEditFarmScreen> createState() => _AddEditFarmScreenState();
}

class _AddEditFarmScreenState extends State<AddEditFarmScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _areaController;
  late final TextEditingController _latController;
  late final TextEditingController _lngController;
  String _areaUnit = 'acre';
  bool _saving = false;
  bool _detectingLocation = false;

  static const _areaUnits = ['acre', 'hectare', 'gunta', 'cent', 'square_meter'];

  List<LocationOption> _states = [];
  List<LocationOption> _districts = [];
  List<LocationOption> _mandals = [];
  List<LocationOption> _villages = [];
  bool _loadingStates = false;
  bool _loadingDistricts = false;
  bool _loadingMandals = false;
  bool _loadingVillages = false;
  int? _selectedStateId;
  int? _selectedDistrictId;
  int? _selectedMandalId;
  int? _selectedVillageId;

  bool get _isEditing => widget.existingFarm != null;

  @override
  void initState() {
    super.initState();
    final farm = widget.existingFarm;
    _nameController = TextEditingController(text: farm?.farmName ?? '');
    _areaController = TextEditingController(text: farm?.areaValue.toString() ?? '');
    _latController = TextEditingController(text: farm?.latitude?.toString() ?? '');
    _lngController = TextEditingController(text: farm?.longitude?.toString() ?? '');
    if (farm != null) _areaUnit = farm.areaUnit;
    if (!_isEditing) _loadStates();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _areaController.dispose();
    _latController.dispose();
    _lngController.dispose();
    super.dispose();
  }

  LocationRepository get _locationRepository => context.read<LocationRepository>();

  Future<void> _loadStates() async {
    setState(() => _loadingStates = true);
    try {
      final states = await _locationRepository.listStates();
      if (!mounted) return;
      setState(() => _states = states);
    } catch (_) {
      // Dropdown just stays empty/disabled - the farmer can still submit
      // the rest of the form with no state/district chosen.
    } finally {
      if (mounted) setState(() => _loadingStates = false);
    }
  }

  Future<void> _onStateChanged(int? stateId) async {
    setState(() {
      _selectedStateId = stateId;
      _selectedDistrictId = null;
      _selectedMandalId = null;
      _selectedVillageId = null;
      _districts = [];
      _mandals = [];
      _villages = [];
    });
    if (stateId == null) return;
    setState(() => _loadingDistricts = true);
    try {
      final districts = await _locationRepository.listDistricts(stateId);
      if (!mounted) return;
      setState(() => _districts = districts);
    } catch (_) {
      // Leave the districts dropdown empty rather than blocking the form.
    } finally {
      if (mounted) setState(() => _loadingDistricts = false);
    }
  }

  Future<void> _onDistrictChanged(int? districtId) async {
    setState(() {
      _selectedDistrictId = districtId;
      _selectedMandalId = null;
      _selectedVillageId = null;
      _mandals = [];
      _villages = [];
    });
    if (districtId == null) return;
    setState(() => _loadingMandals = true);
    try {
      final mandals = await _locationRepository.listMandals(districtId);
      if (!mounted) return;
      setState(() => _mandals = mandals);
    } catch (_) {
      // No mandal master data exists yet for most districts - an empty
      // list here is expected, not an error to surface to the farmer.
    } finally {
      if (mounted) setState(() => _loadingMandals = false);
    }
  }

  Future<void> _onMandalChanged(int? mandalId) async {
    setState(() {
      _selectedMandalId = mandalId;
      _selectedVillageId = null;
      _villages = [];
    });
    if (mandalId == null) return;
    setState(() => _loadingVillages = true);
    try {
      final villages = await _locationRepository.listVillages(mandalId);
      if (!mounted) return;
      setState(() => _villages = villages);
    } catch (_) {
      // Same as mandals - an empty village list is expected, not an error.
    } finally {
      if (mounted) setState(() => _loadingVillages = false);
    }
  }

  void _onVillageChanged(int? villageId) {
    setState(() => _selectedVillageId = villageId);
  }

  /// Case-insensitive exact match first, then a loose substring match -
  /// Nominatim's wording ("East Godavari" vs this app's "East Godavari
  /// district", etc.) doesn't always match our master data verbatim.
  /// Returns null (never a wrong guess) when nothing reasonably matches.
  LocationOption? _bestMatch(List<LocationOption> options, String? guess) {
    if (guess == null || guess.trim().isEmpty) return null;
    final normalized = guess.trim().toLowerCase();
    for (final option in options) {
      if (option.name.trim().toLowerCase() == normalized) return option;
    }
    for (final option in options) {
      final optionName = option.name.trim().toLowerCase();
      if (optionName.contains(normalized) || normalized.contains(optionName)) return option;
    }
    return null;
  }

  Future<void> _useCurrentLocation(AppLocalizations l10n) async {
    setState(() => _detectingLocation = true);
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.addEditFarmLocationPermissionRequiredMessage)),
        );
        return;
      }
      if (!await Geolocator.isLocationServiceEnabled()) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.addEditFarmEnableLocationMessage)),
        );
        return;
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      );
      if (!mounted) return;
      setState(() {
        _latController.text = position.latitude.toStringAsFixed(6);
        _lngController.text = position.longitude.toStringAsFixed(6);
      });

      await _autoFillLocationFromGps(position.latitude, position.longitude, l10n);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _detectingLocation = false);
    }
  }

  Future<void> _autoFillLocationFromGps(double latitude, double longitude, AppLocalizations l10n) async {
    ReverseGeocodeGuess? guess;
    try {
      guess = await NominatimReverseGeocoder().reverseGeocode(latitude: latitude, longitude: longitude);
    } catch (_) {
      guess = null; // No internet or the service is unreachable - coordinates are still captured above.
    }

    if (guess == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.addEditFarmLocationCapturedNoAreaMessage)),
      );
      return;
    }

    if (_states.isEmpty) await _loadStates();
    final matchedState = _bestMatch(_states, guess.stateName);
    if (matchedState == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.addEditFarmLocationCapturedSelectManuallyMessage)),
      );
      return;
    }
    await _onStateChanged(matchedState.id);
    if (!mounted) return;

    final matchedDistrict = _bestMatch(_districts, guess.districtName);
    if (matchedDistrict == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.addEditFarmDetectedStateMessage(matchedState.name))),
      );
      return;
    }
    await _onDistrictChanged(matchedDistrict.id);
    if (!mounted) return;

    final matchedMandal = _bestMatch(_mandals, guess.mandalName);
    if (matchedMandal == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(l10n.addEditFarmDetectedStateDistrictMessage(matchedState.name, matchedDistrict.name)),
        ),
      );
      return;
    }
    await _onMandalChanged(matchedMandal.id);
    if (!mounted) return;

    final matchedVillage = _bestMatch(_villages, guess.villageName);
    if (matchedVillage != null) _onVillageChanged(matchedVillage.id);

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          matchedVillage != null
              ? l10n.addEditFarmDetectedFullLocationWithVillageMessage(
                  matchedState.name, matchedDistrict.name, matchedMandal.name, matchedVillage.name)
              : l10n.addEditFarmDetectedFullLocationMessage(matchedState.name, matchedDistrict.name, matchedMandal.name),
        ),
      ),
    );
  }

  Future<void> _save(AppLocalizations l10n) async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final repo = context.read<FarmRepository>();
    try {
      final areaValue = double.parse(_areaController.text.trim());
      final lat = _latController.text.trim().isEmpty ? null : double.parse(_latController.text.trim());
      final lng = _lngController.text.trim().isEmpty ? null : double.parse(_lngController.text.trim());

      if (_isEditing) {
        await repo.updateFarm(
          widget.existingFarm!.id,
          farmName: _nameController.text.trim(),
          areaValue: areaValue,
          areaUnit: _areaUnit,
        );
      } else {
        await repo.createFarm(
          farmName: _nameController.text.trim(),
          areaValue: areaValue,
          areaUnit: _areaUnit,
          latitude: lat,
          longitude: lng,
          stateId: _selectedStateId,
          districtId: _selectedDistrictId,
          mandalId: _selectedMandalId,
          villageId: _selectedVillageId,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_isEditing ? l10n.addEditFarmUpdatedMessage : l10n.addEditFarmAddedMessage)),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Widget _buildLocationDropdown({
    required String label,
    required List<LocationOption> options,
    required int? value,
    required bool loading,
    required bool enabled,
    required ValueChanged<int?> onChanged,
    required AppLocalizations l10n,
  }) {
    final hasOptions = options.isNotEmpty;
    return DropdownButtonFormField<int>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        helperText: enabled && !loading && !hasOptions ? l10n.addEditFarmNoDataAvailableLabel : null,
        suffixIcon: loading
            ? const Padding(
                padding: EdgeInsets.all(12),
                child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
              )
            : null,
      ),
      items: options.map((o) => DropdownMenuItem(value: o.id, child: Text(o.name))).toList(),
      onChanged: enabled && hasOptions && !loading ? onChanged : null,
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? l10n.addEditFarmEditTitle : l10n.addEditFarmAddTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _nameController,
                  decoration: InputDecoration(labelText: l10n.addEditFarmNameLabel),
                  validator: (v) => (v == null || v.trim().length < 2) ? l10n.addEditFarmNameRequiredError : null,
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextFormField(
                        controller: _areaController,
                        decoration: InputDecoration(labelText: l10n.addEditFarmAreaLabel),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        validator: (v) {
                          final trimmed = v?.trim() ?? '';
                          if (trimmed.isEmpty) return l10n.addEditFarmAreaRequiredError;
                          final value = double.tryParse(trimmed);
                          if (value == null || value <= 0) return l10n.addEditFarmAreaInvalidError;
                          return null;
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _areaUnit,
                        decoration: InputDecoration(labelText: l10n.addEditFarmUnitLabel),
                        items: _areaUnits
                            .map((u) => DropdownMenuItem(value: u, child: Text(u.replaceAll('_', ' '))))
                            .toList(),
                        onChanged: (v) => setState(() => _areaUnit = v ?? _areaUnit),
                      ),
                    ),
                  ],
                ),
                if (!_isEditing) ...[
                  const SizedBox(height: 24),
                  Text(l10n.addEditFarmLocationSectionLabel, style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _detectingLocation ? null : () => _useCurrentLocation(l10n),
                    icon: _detectingLocation
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.my_location),
                    label: Text(_detectingLocation ? l10n.addEditFarmDetectingLocationLabel : l10n.addEditFarmUseCurrentLocationButton),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _latController,
                          decoration: InputDecoration(labelText: l10n.addEditFarmLatitudeLabel),
                          keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextFormField(
                          controller: _lngController,
                          decoration: InputDecoration(labelText: l10n.addEditFarmLongitudeLabel),
                          keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildLocationDropdown(
                    label: l10n.addEditFarmStateLabel,
                    options: _states,
                    value: _selectedStateId,
                    loading: _loadingStates,
                    enabled: true,
                    onChanged: _onStateChanged,
                    l10n: l10n,
                  ),
                  const SizedBox(height: 12),
                  _buildLocationDropdown(
                    label: l10n.addEditFarmDistrictLabel,
                    options: _districts,
                    value: _selectedDistrictId,
                    loading: _loadingDistricts,
                    enabled: _selectedStateId != null,
                    onChanged: _onDistrictChanged,
                    l10n: l10n,
                  ),
                  const SizedBox(height: 12),
                  _buildLocationDropdown(
                    label: l10n.addEditFarmMandalLabel,
                    options: _mandals,
                    value: _selectedMandalId,
                    loading: _loadingMandals,
                    enabled: _selectedDistrictId != null,
                    onChanged: _onMandalChanged,
                    l10n: l10n,
                  ),
                  const SizedBox(height: 12),
                  _buildLocationDropdown(
                    label: l10n.addEditFarmVillageLabel,
                    options: _villages,
                    value: _selectedVillageId,
                    loading: _loadingVillages,
                    enabled: _selectedMandalId != null,
                    onChanged: _onVillageChanged,
                    l10n: l10n,
                  ),
                ],
                const SizedBox(height: 32),
                if (_saving)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: () => _save(l10n), child: Text(_isEditing ? l10n.addEditFarmSaveChangesButton : l10n.addEditFarmAddFarmButton)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
