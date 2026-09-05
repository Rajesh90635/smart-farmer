import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/locale_sync.dart';
import '../features/auth/auth_state.dart';
import '../features/crop_photo/pending_upload_queue.dart';
import '../features/crop_photo/sync_coordinator.dart';
import '../features/auth/reset_password_screen.dart';
import '../features/auth/validators.dart';
import '../l10n/app_localizations.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _goToResetPassword() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ResetPasswordScreen(initialPhoneNumber: _phoneController.text)),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final authState = context.read<AuthState>();
    final success = await authState.login(
      phoneNumber: _phoneController.text.trim(),
      password: _passwordController.text,
    );

    if (!mounted) return;
    final l10n = AppLocalizations.of(context)!;
    if (success) {
      // Cross-device language sync: this device may never have seen this
      // farmer before, so apply their backend-saved language now rather
      // than showing Home in the on-device default (English).
      await syncLocaleFromBackendProfile(context);
      if (!mounted) return;

      // Real bug fixed here: an upload that hit `authenticationRequired`
      // (session expired mid-upload) was never revived by anything,
      // including a fresh, successful re-login - it stayed permanently
      // stuck. Logging back in is exactly the moment it becomes safe to
      // retry, so do it here rather than requiring the farmer to find a
      // separate "retry" control.
      await context.read<PendingUploadQueue>().reviveAuthRequiredItems();
      if (!mounted) return;
      context.read<SyncCoordinator>().syncNow();

      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil('/home', (route) => false);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authState.errorMessage(l10n) ?? l10n.loginFailedMessage)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final authState = context.watch<AuthState>();
    final isBusy = authState.status == AuthStatus.authenticating;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.loginScreenTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
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
                  validator: (v) => (v == null || v.isEmpty) ? l10n.passwordRequiredError : null,
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: _goToResetPassword,
                    child: Text(l10n.forgotPasswordButton),
                  ),
                ),
                const SizedBox(height: 16),
                if (isBusy)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: _submit, child: Text(l10n.loginButton)),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/register'),
                  child: Text(l10n.newHereCreateAccountButton),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
