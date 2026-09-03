import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/app_localizations.dart';
import 'auth_state.dart';
import 'validators.dart';

/// Lets an already-logged-in farmer change their own password by
/// confirming their current one first. This is the self-service path;
/// a farmer who has forgotten their password entirely still has to go
/// through support (see LoginScreen's "Forgot password?" dialog) since
/// there is no OTP/email channel to verify identity out of band.
class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscureCurrent = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  bool _submitting = false;

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _submitting = true);
    final authState = context.read<AuthState>();
    final success = await authState.changePassword(
      currentPassword: _currentPasswordController.text,
      newPassword: _newPasswordController.text,
    );

    if (!mounted) return;
    final l10n = AppLocalizations.of(context)!;
    setState(() => _submitting = false);

    if (success) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.passwordChangedMessage)),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authState.lastErrorMessage ?? l10n.incorrectCurrentPasswordError)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.changePasswordTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _currentPasswordController,
                  decoration: InputDecoration(
                    labelText: l10n.currentPasswordLabel,
                    suffixIcon: IconButton(
                      icon: Icon(_obscureCurrent ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscureCurrent = !_obscureCurrent),
                    ),
                  ),
                  obscureText: _obscureCurrent,
                  validator: (v) => (v == null || v.isEmpty) ? l10n.passwordRequiredError : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _newPasswordController,
                  decoration: InputDecoration(
                    labelText: l10n.newPasswordLabel,
                    suffixIcon: IconButton(
                      icon: Icon(_obscureNew ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscureNew = !_obscureNew),
                    ),
                  ),
                  obscureText: _obscureNew,
                  validator: Validators.password,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _confirmPasswordController,
                  decoration: InputDecoration(
                    labelText: l10n.confirmNewPasswordLabel,
                    suffixIcon: IconButton(
                      icon: Icon(_obscureConfirm ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                    ),
                  ),
                  obscureText: _obscureConfirm,
                  validator: (v) =>
                      (v != _newPasswordController.text) ? l10n.confirmNewPasswordMismatchError : null,
                ),
                const SizedBox(height: 32),
                if (_submitting)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(onPressed: _submit, child: Text(l10n.saveButton)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
