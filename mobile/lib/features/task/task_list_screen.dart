import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/friendly_error.dart';
import '../../core/voice_service.dart';
import '../../l10n/app_localizations.dart';
import 'task_models.dart';
import 'task_repository.dart';

/// Every task shown here is either a farmer-created task or a real
/// weather advisory reused unchanged from Step 15 - nothing on this
/// screen is auto-generated agronomy. Grouping (Overdue/Upcoming/
/// Completed/Cancelled) is derived purely from the backend's own
/// `displayStatus` - never recomputed independently of what the backend
/// already decided.
class TaskListScreen extends StatefulWidget {
  final String cropCycleId;
  const TaskListScreen({super.key, required this.cropCycleId});

  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  List<Task> _tasks = [];
  bool _loading = true;
  String? _error;
  bool _voiceUnavailableMessageShown = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final tasks = await context.read<TaskRepository>().listTasksForCropCycle(widget.cropCycleId);
      if (!mounted) return;
      setState(() {
        _tasks = tasks;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = FriendlyError.from(e, AppLocalizations.of(context)!);
        _loading = false;
      });
    }
  }

  Future<void> _completeTask(Task task) async {
    try {
      await context.read<TaskRepository>().completeTask(task.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  Future<void> _cancelTask(Task task) async {
    try {
      await context.read<TaskRepository>().cancelTask(task.id);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
    }
  }

  Future<void> _showAddTaskSheet(AppLocalizations l10n) async {
    final titleController = TextEditingController();
    String selectedType = 'general';
    DateTime? selectedDate;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.addTaskTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 12),
              TextField(controller: titleController, decoration: InputDecoration(labelText: l10n.taskTitleLabel)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedType,
                items: taskTypeOptions.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (v) => setSheetState(() => selectedType = v ?? 'general'),
                decoration: InputDecoration(labelText: l10n.taskTypeLabel),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: sheetContext,
                    initialDate: DateTime.now(),
                    firstDate: DateTime.now().subtract(const Duration(days: 1)),
                    lastDate: DateTime.now().add(const Duration(days: 365)),
                  );
                  if (picked != null) setSheetState(() => selectedDate = picked);
                },
                child: Text(selectedDate == null ? l10n.pickDueDateButton : selectedDate!.toIso8601String().split('T').first),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  if (titleController.text.trim().isEmpty) return;
                  Navigator.of(sheetContext).pop();
                  try {
                    await context.read<TaskRepository>().createTask(
                          cropCycleId: widget.cropCycleId,
                          taskType: selectedType,
                          title: titleController.text.trim(),
                          dueDate: selectedDate?.toIso8601String().split('T').first,
                        );
                    await _load();
                  } catch (e) {
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(FriendlyError.from(e, AppLocalizations.of(context)!))));
                  }
                },
                child: Text(l10n.saveTaskButton),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _lookupAdvisoryMessage(AppLocalizations l10n, String messageKey) {
    switch (messageKey) {
      case 'sprayConditionWarning':
        return l10n.sprayConditionWarning;
      default:
        return messageKey;
    }
  }

  Future<void> _speakTask(Task task, AppLocalizations l10n) async {
    final parts = <String>[task.title];
    if (task.weatherAdvisory != null) {
      final key = taskWeatherAdvisoryMessageKeys[task.weatherAdvisory!.reasonMessageKey] ?? task.weatherAdvisory!.reasonMessageKey;
      parts.add(_lookupAdvisoryMessage(l10n, key));
    }
    final voice = context.read<VoiceService>();
    final started = await voice.speak(parts.join('. '), languageCode: 'en');
    if (!mounted) return;
    if (!started) setState(() => _voiceUnavailableMessageShown = true);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.tasksTitle)),
      floatingActionButton: FloatingActionButton(onPressed: () => _showAddTaskSheet(l10n), child: const Icon(Icons.add)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody(l10n)),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_loading) {
      return ListView(children: const [SizedBox(height: 120), Center(child: CircularProgressIndicator())]);
    }
    if (_error != null) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(child: Text(_error!)),
          const SizedBox(height: 12),
          Center(child: ElevatedButton(onPressed: _load, child: Text(l10n.tryAgainButton))),
        ],
      );
    }
    if (_tasks.isEmpty) {
      return ListView(children: [const SizedBox(height: 100), Center(child: Text(l10n.noTasksYet))]);
    }

    final overdue = _tasks.where((t) => t.displayStatus == 'overdue').toList();
    final pending = _tasks.where((t) => t.displayStatus == 'pending').toList();
    final completed = _tasks.where((t) => t.isCompleted).toList();
    final cancelled = _tasks.where((t) => t.isCancelled).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (overdue.isNotEmpty) ..._buildSection(l10n.overdueTasksLabel, overdue, l10n, isOverdueSection: true),
        if (pending.isNotEmpty) ..._buildSection(l10n.upcomingTasksLabel, pending, l10n),
        if (completed.isNotEmpty) ..._buildSection(l10n.completedTasksLabel, completed, l10n),
        if (cancelled.isNotEmpty) ..._buildSection(l10n.cancelledTasksLabel, cancelled, l10n),
        if (_voiceUnavailableMessageShown)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(l10n.voiceUnavailable, style: const TextStyle(fontSize: 12, color: Colors.grey))),
      ],
    );
  }

  List<Widget> _buildSection(String label, List<Task> tasks, AppLocalizations l10n, {bool isOverdueSection = false}) {
    return [
      Padding(
        padding: const EdgeInsets.only(top: 8, bottom: 4),
        child: Text(label, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: isOverdueSection ? Colors.red : null)),
      ),
      ...tasks.map((task) => _buildTaskCard(task, l10n)),
    ];
  }

  Widget _buildTaskCard(Task task, AppLocalizations l10n) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(task.title, style: const TextStyle(fontWeight: FontWeight.bold))),
                IconButton(icon: const Icon(Icons.volume_up, size: 20), onPressed: () => _speakTask(task, l10n)),
              ],
            ),
            if (task.dueDate != null) Text('${l10n.dueDateLabel}: ${task.dueDate}', style: const TextStyle(fontSize: 12)),
            if (task.weatherAdvisory != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber, color: Colors.orange, size: 16),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        _lookupAdvisoryMessage(l10n, taskWeatherAdvisoryMessageKeys[task.weatherAdvisory!.reasonMessageKey] ?? task.weatherAdvisory!.reasonMessageKey),
                        style: const TextStyle(fontSize: 12, color: Colors.orange),
                      ),
                    ),
                  ],
                ),
              ),
            if (task.status == 'pending')
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(onPressed: () => _cancelTask(task), child: Text(l10n.cancelTaskButton)),
                  TextButton(onPressed: () => _completeTask(task), child: Text(l10n.completeTaskButton)),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
