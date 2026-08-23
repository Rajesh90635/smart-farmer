import 'package:flutter/material.dart';

/// Navigation placeholder only - per the foundation-phase rule, no business
/// logic or farmer-facing functionality lives here yet. Implemented in its
/// owning epic (see PROJECT_STATUS.md).
class AssistantScreen extends StatelessWidget {
  const AssistantScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Assistant')),
      body: const Center(
        child: Text('Assistant screen — placeholder, not yet implemented.'),
      ),
    );
  }
}
