import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../features/auth/auth_state.dart';
import '../features/auth/farmer_repository.dart';
import '../features/auth/language_selection_screen.dart';
import '../core/friendly_error.dart';
import '../core/locale_controller.dart';
import '../l10n/app_localizations.dart';

/// Farmer profile screen: view, edit, change language, logout. Kept
/// deliberately simple and uncrowded per the UX rule - one screen, large
/// tap targets, no nested settings maze.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  FarmerProfile? _profile;
  bool _loading = true;
  String? _error;
  bool _editing = false;
  final _nameController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final profile = await context.read<FarmerRepository>().getMyProfile();
      setState(() {
        _profile = profile;
        _nameController.text = profile.fullName;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = FriendlyError.from(e);
        _loading = false;
      });
    }
  }

  Future<void> _saveName() async {
    try {
      final updated = await context
          .read<FarmerRepository>()
          .updateMyProfile(fullName: _nameController.text.trim());
      setState(() {
        _profile = updated;
        _editing = false;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _changeLanguage() async {
    final languageCode = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const LanguageSelectionScreen()),
    );
    if (languageCode == null || !mounted) return;

    // Switch the app's displayed language immediately - this must not wait
    // on (or fail because of) the network call below. Syncing the choice to
    // the farmer's backend profile is best-effort on top of that.
    final localeController = context.read<LocaleController>();
    await localeController.setLocale(languageCode);
    if (!mounted) return;

    try {
      final updated =
          await context.read<FarmerRepository>().updateMyProfile(preferredLanguageCode: languageCode);
      setState(() => _profile = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  Future<void> _logout() async {
    await context.read<AuthState>().logout();
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.profileScreenTitle)),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: Text(l10n.genericErrorRetry)),
          ],
        ),
      );
    }

    final profile = _profile!;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Center(child: const Icon(Icons.account_circle, size: 96)),
          const SizedBox(height: 24),
          if (_editing)
            TextField(controller: _nameController, decoration: InputDecoration(labelText: l10n.nameLabel))
          else
            ListTile(
              title: Text(l10n.nameLabel),
              subtitle: Text(profile.fullName, style: const TextStyle(fontSize: 18)),
            ),
          const SizedBox(height: 8),
          ListTile(
            title: Text(l10n.phoneNumberDisplayLabel),
            subtitle: Text(profile.phoneNumber, style: const TextStyle(fontSize: 18)),
          ),
          ListTile(
            title: Text(l10n.languageLabel),
            subtitle: Text(
              LanguageSelectionScreen.labelForCode(profile.preferredLanguageCode),
              style: const TextStyle(fontSize: 18),
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: _changeLanguage,
          ),
          const SizedBox(height: 32),
          if (_editing)
            ElevatedButton(onPressed: _saveName, child: Text(l10n.saveButton))
          else
            ElevatedButton(onPressed: () => setState(() => _editing = true), child: Text(l10n.editProfileButton)),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: _logout, child: Text(l10n.logOutButton)),
        ],
      ),
    );
  }
}
