import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/voice_service.dart';
import '../../l10n/app_localizations.dart';
import 'assistant_models.dart';
import 'assistant_repository.dart';

/// The farmer-wide AI Assistant chat screen - wires the long-existing,
/// fully persisted backend (POST /assistant/chat, GET /assistant/history)
/// to a real UI for the first time. Every assistant bubble shows exactly
/// the backend's own content/sources/confidence verbatim - this screen
/// never generates, edits, or upgrades an answer.
class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final Set<String> _feedbackGiven = {};

  List<ChatMessage> _messages = [];
  String? _conversationId;
  bool _historyLoading = true;
  String? _historyError;
  bool _sending = false;
  String? _sendError;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _historyLoading = true;
      _historyError = null;
    });
    try {
      final history = await context.read<AssistantRepository>().getActiveHistory();
      if (!mounted) return;
      setState(() {
        _messages = history.messages;
        _conversationId = history.conversationId;
        _historyLoading = false;
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _historyError = FriendlyError.from(e);
        _historyLoading = false;
      });
    }
  }

  Future<void> _send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _sendError = null;
    });
    try {
      final result = await context.read<AssistantRepository>().sendMessage(trimmed, conversationId: _conversationId);
      if (!mounted) return;
      setState(() {
        _messages = [..._messages, result.farmerMessage, result.assistantMessage];
        _conversationId = result.conversationId;
        _sending = false;
        _controller.clear();
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sendError = FriendlyError.from(e);
        _sending = false;
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
    });
  }

  /// Speaks EXACTLY this message's own content - never a separately
  /// composed summary (same rule as every other VoiceService call site).
  Future<void> _speak(ChatMessage message) async {
    final voice = context.read<VoiceService>();
    final started = await voice.speak(message.content, languageCode: message.languageCode);
    if (!mounted || started) return;
    final l10n = AppLocalizations.of(context)!;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.voiceUnavailable)));
  }

  Future<void> _giveFeedback(ChatMessage message, bool helpful) async {
    final l10n = AppLocalizations.of(context)!;
    try {
      await context.read<AssistantRepository>().submitFeedback(message.id, helpful: helpful);
      if (!mounted) return;
      setState(() => _feedbackGiven.add(message.id));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.assistantFeedbackThanksMessage)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e))));
    }
  }

  List<String> _suggestedQuestions(AppLocalizations l10n) => [
        l10n.assistantChatSuggestionCropStatus,
        l10n.assistantChatSuggestionWeather,
        l10n.assistantChatSuggestionHarvest,
        l10n.assistantChatSuggestionOrders,
      ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.assistantChatTitle)),
      body: Column(
        children: [
          Expanded(child: _buildBody(l10n)),
          if (_sendError != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Text(_sendError!, style: const TextStyle(color: Colors.red, fontSize: 12)),
            ),
          _buildComposer(l10n),
        ],
      ),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_historyLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_historyError != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_historyError!),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _loadHistory, child: Text(l10n.genericErrorRetry)),
          ],
        ),
      );
    }
    if (_messages.isEmpty && !_sending) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.assistantEmptyStateHint, style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _suggestedQuestions(l10n).map((q) => ActionChip(label: Text(q), onPressed: () => _send(q))).toList(),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(12),
      itemCount: _messages.length + (_sending ? 1 : 0),
      itemBuilder: (context, index) {
        if (index >= _messages.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Align(alignment: Alignment.centerLeft, child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }
        return _buildBubble(_messages[index], l10n);
      },
    );
  }

  Widget _buildBubble(ChatMessage message, AppLocalizations l10n) {
    final isFarmer = message.isFromFarmer;
    final bubble = Container(
      constraints: const BoxConstraints(maxWidth: 320),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isFarmer ? Theme.of(context).colorScheme.primaryContainer : Colors.grey.shade200,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(message.content),
          if (!isFarmer && (message.sources?.isNotEmpty ?? false)) ...[
            const SizedBox(height: 6),
            Text(message.sources!.join(', '), style: const TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic)),
          ],
          if (!isFarmer) ...[
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.volume_up, size: 18),
                  onPressed: () => _speak(message),
                ),
                if (!_feedbackGiven.contains(message.id)) ...[
                  IconButton(
                    visualDensity: VisualDensity.compact,
                    icon: const Icon(Icons.thumb_up_outlined, size: 18),
                    tooltip: l10n.assistantMarkHelpfulTooltip,
                    onPressed: () => _giveFeedback(message, true),
                  ),
                  IconButton(
                    visualDensity: VisualDensity.compact,
                    icon: const Icon(Icons.thumb_down_outlined, size: 18),
                    tooltip: l10n.assistantMarkNotHelpfulTooltip,
                    onPressed: () => _giveFeedback(message, false),
                  ),
                ],
              ],
            ),
          ],
        ],
      ),
    );

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Align(
        alignment: isFarmer ? Alignment.centerRight : Alignment.centerLeft,
        child: bubble,
      ),
    );
  }

  Widget _buildComposer(AppLocalizations l10n) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                enabled: !_sending,
                decoration: InputDecoration(hintText: l10n.typeYourQuestionHint, border: const OutlineInputBorder()),
                onSubmitted: _send,
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              tooltip: l10n.assistantSendButtonTooltip,
              icon: const Icon(Icons.send),
              onPressed: _sending ? null : () => _send(_controller.text),
            ),
          ],
        ),
      ),
    );
  }
}
