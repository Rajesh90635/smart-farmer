import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/locale_controller.dart';
import '../../l10n/app_localizations.dart';
import 'auth_repository.dart';
import 'auth_state.dart';
import 'consent_screen.dart';
import 'language_selection_screen.dart';
import 'validators.dart';

/// Collects phone, password, and name, then hands off to language
/// selection and consent before actually calling the register API - the
/// full chain matches the approved flow: Register -> Language -> Consent
/// -> Home.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nameController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _continue() async {
    if (!_formKey.currentState!.validate()) return;

    final languageCode = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const LanguageSelectionScreen()),
    );
    if (languageCode == null || !mounted) return;

    // Apply immediately so the rest of registration (consent, and the app
    // beyond it) renders in the chosen language right away, not just after
    // the account is created.
    await context.read<LocaleController>().setLocale(languageCode);
    if (!mounted) return;

    final consents = await Navigator.of(context).push<List<ConsentInput>>(
      MaterialPageRoute(builder: (_) => const ConsentScreen()),
    );
    if (consents == null || !mounted) return;

    final authState = context.read<AuthState>();
    final success = await authState.register(
      phoneNumber: _phoneController.text.trim(),
      password: _passwordController.text,
      fullName: _nameController.text.trim(),
      preferredLanguageCode: languageCode,
      consents: consents,
    );

    if (!mounted) return;
    final l10n = AppLocalizations.of(context)!;
    if (success) {
      Navigator.of(context).pushNamedAndRemoveUntil('/home', (route) => false);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authState.errorMessage(l10n) ?? l10n.registrationFailedMessage)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final authState = context.watch<AuthState>();
    final isBusy = authState.status == AuthStatus.authenticating;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.createAccountTitle)),
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
                  decoration: InputDecoration(labelText: l10n.yourNameLabel),
                  textInputAction: TextInputAction.next,
                  validator: Validators.fullName(l10n),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _phoneController,
                  decoration: InputDecoration(labelText: l10n.phoneNumberLabel),
                  keyboardType: TextInputType.phone,
                  textInputAction: TextInputAction.next,
                  validator: Validators.phoneNumber(l10n),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: l10n.passwordLabel,
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  obscureText: _obscurePassword,
                  validator: Validators.password(l10n),
                ),
                const SizedBox(height: 32),
                if (isBusy)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: _continue, child: Text(l10n.registerContinueButton)),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/login'),
                  child: Text(l10n.alreadyHaveAccountLoginButton),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
