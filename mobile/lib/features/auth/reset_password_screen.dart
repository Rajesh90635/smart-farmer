import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/app_localizations.dart';
import 'auth_state.dart';
import 'validators.dart';

/// Lets a farmer set a new password from their phone number, verified by a
/// one-time SMS code (see backend/app/services/sms/) before the reset is
/// allowed - step 1 requests the code, step 2 submits it with the new
/// password. On success the backend logs the farmer straight in, so this
/// screen navigates directly to home rather than back to login.
class ResetPasswordScreen extends StatefulWidget {
  const ResetPasswordScreen({super.key, this.initialPhoneNumber});

  final String? initialPhoneNumber;

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _phoneFormKey = GlobalKey<FormState>();
  final _resetFormKey = GlobalKey<FormState>();
  late final _phoneController = TextEditingController(text: widget.initialPhoneNumber);
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  bool _submitting = false;
  bool _otpRequested = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _requestOtp() async {
    if (!_phoneFormKey.currentState!.validate()) return;

    setState(() => _submitting = true);
    final l10n = AppLocalizations.of(context)!;
    final authState = context.read<AuthState>();
    final success = await authState.requestPasswordResetOtp(phoneNumber: _phoneController.text.trim());

    if (!mounted) return;
    setState(() {
      _submitting = false;
      if (success) _otpRequested = true;
    });
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.otpSentMessage)));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authState.errorMessage(l10n) ?? l10n.requestOtpFailedMessage)),
      );
    }
  }

  Future<void> _submit() async {
    if (!_resetFormKey.currentState!.validate()) return;

    setState(() => _submitting = true);
    final authState = context.read<AuthState>();
    final success = await authState.resetPassword(
      phoneNumber: _phoneController.text.trim(),
      newPassword: _newPasswordController.text,
      otpCode: _otpController.text.trim(),
    );

    if (!mounted) return;
    if (success) {
      Navigator.of(context).pushNamedAndRemoveUntil('/home', (route) => false);
    } else {
      final l10n = AppLocalizations.of(context)!;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authState.errorMessage(l10n) ?? l10n.resetPasswordFailedMessage)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.resetPasswordScreenTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _otpRequested ? _buildResetForm(l10n) : _buildPhoneForm(l10n),
        ),
      ),
    );
  }

  Widget _buildPhoneForm(AppLocalizations l10n) {
    return Form(
      key: _phoneFormKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _phoneController,
            decoration: InputDecoration(labelText: l10n.phoneNumberLabel),
            keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.done,
            validator: Validators.phoneNumber(l10n),
          ),
          const SizedBox(height: 32),
          if (_submitting)
            const Center(child: CircularProgressIndicator())
          else
            ElevatedButton(onPressed: _requestOtp, child: Text(l10n.sendCodeButton)),
        ],
      ),
    );
  }

  Widget _buildResetForm(AppLocalizations l10n) {
    return Form(
      key: _resetFormKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(l10n.otpSentMessage),
          const SizedBox(height: 16),
          TextFormField(
            controller: _otpController,
            decoration: InputDecoration(labelText: l10n.otpCodeLabel),
            keyboardType: TextInputType.number,
            textInputAction: TextInputAction.next,
            validator: (v) => (v == null || v.trim().isEmpty) ? l10n.otpCodeRequiredError : null,
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
            validator: Validators.password(l10n),
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
          const SizedBox(height: 16),
          if (!_submitting)
            TextButton(onPressed: _requestOtp, child: Text(l10n.resendCodeButton)),
          const SizedBox(height: 16),
          if (_submitting)
            const Center(child: CircularProgressIndicator())
          else
            ElevatedButton(onPressed: _submit, child: Text(l10n.resetPasswordButton)),
        ],
      ),
    );
  }
}
