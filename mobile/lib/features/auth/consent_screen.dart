import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import 'auth_repository.dart';

/// Collects the two consents required at registration (see
/// backend/app/models/consent_record.py's REQUIRED_CONSENTS_AT_REGISTRATION).
/// Both must be explicitly checked - per the "never assume consent" rule,
/// there is no pre-checked box and no way to continue without both.
class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  bool _acceptedTerms = false;
  bool _acceptedPrivacy = false;

  static const _consentVersion = '1.0';

  bool get _canContinue => _acceptedTerms && _acceptedPrivacy;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.consentScreenTitle)),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              CheckboxListTile(
                value: _acceptedTerms,
                onChanged: (v) => setState(() => _acceptedTerms = v ?? false),
                title: Text(l10n.agreeTermsOfServiceLabel),
                controlAffinity: ListTileControlAffinity.leading,
              ),
              CheckboxListTile(
                value: _acceptedPrivacy,
                onChanged: (v) => setState(() => _acceptedPrivacy = v ?? false),
                title: Text(l10n.agreePrivacyPolicyLabel),
                controlAffinity: ListTileControlAffinity.leading,
              ),
              const Spacer(),
              ElevatedButton(
                onPressed: _canContinue
                    ? () => Navigator.of(context).pop([
                          ConsentInput('terms_of_service', _consentVersion),
                          ConsentInput('privacy_policy', _consentVersion),
                        ])
                    : null,
                child: Text(l10n.consentContinueButton),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
