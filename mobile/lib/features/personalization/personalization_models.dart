/// Mirrors backend/app/schemas/personalization.py exactly.
///
/// confidence/observation are null together whenever evidence is below
/// the documented minimum threshold - this model never renders a
/// preference statement without real supporting evidence.
/// mlTrainingJustified is always false - stated explicitly, matching
/// the backend's own honest disclosure.
library;

class LearnedPreference {
  final String signalName;
  final String? observation;
  final int evidenceCount;
  final String? confidence;
  final String? lastObservedAt;
  final String explanation;

  LearnedPreference({
    required this.signalName,
    this.observation,
    required this.evidenceCount,
    this.confidence,
    this.lastObservedAt,
    required this.explanation,
  });

  factory LearnedPreference.fromJson(Map<String, dynamic> json) => LearnedPreference(
        signalName: json['signal_name'] as String,
        observation: json['observation'] as String?,
        evidenceCount: json['evidence_count'] as int,
        confidence: json['confidence'] as String?,
        lastObservedAt: json['last_observed_at'] as String?,
        explanation: json['explanation'] as String,
      );
}

class PersonalizationProfile {
  final String farmerId;
  final List<LearnedPreference> preferences;

  PersonalizationProfile({required this.farmerId, required this.preferences});

  factory PersonalizationProfile.fromJson(Map<String, dynamic> json) => PersonalizationProfile(
        farmerId: json['farmer_id'] as String,
        preferences: (json['preferences'] as List).map((e) => LearnedPreference.fromJson(e as Map<String, dynamic>)).toList(),
      );
}

class AdvisoryFeedback {
  final String id;
  final String cropCycleId;
  final String sourceType;
  final String? sourceReference;
  final String feedbackType;
  final String? note;
  final String createdAt;

  AdvisoryFeedback({
    required this.id,
    required this.cropCycleId,
    required this.sourceType,
    this.sourceReference,
    required this.feedbackType,
    this.note,
    required this.createdAt,
  });

  factory AdvisoryFeedback.fromJson(Map<String, dynamic> json) => AdvisoryFeedback(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        sourceType: json['source_type'] as String,
        sourceReference: json['source_reference'] as String?,
        feedbackType: json['feedback_type'] as String,
        note: json['note'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class FeatureSnapshot {
  final String featureVersion;
  final String cropCycleId;
  final String extractedAt;
  final Map<String, dynamic> availableAtTime;
  final Map<String, dynamic>? outcomeLabel;
  final String? outcomeKnownOnlyAfter;

  FeatureSnapshot({
    required this.featureVersion,
    required this.cropCycleId,
    required this.extractedAt,
    required this.availableAtTime,
    this.outcomeLabel,
    this.outcomeKnownOnlyAfter,
  });

  factory FeatureSnapshot.fromJson(Map<String, dynamic> json) => FeatureSnapshot(
        featureVersion: json['feature_version'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        extractedAt: json['extracted_at'] as String,
        availableAtTime: (json['available_at_time'] as Map).cast<String, dynamic>(),
        outcomeLabel: json['outcome_label'] != null ? (json['outcome_label'] as Map).cast<String, dynamic>() : null,
        outcomeKnownOnlyAfter: json['outcome_known_only_after'] as String?,
      );
}

class LearningSummary {
  final String cropCycleId;
  final FeatureSnapshot featureSnapshot;
  final bool mlTrainingJustified;
  final String mlReadinessNote;

  LearningSummary({
    required this.cropCycleId,
    required this.featureSnapshot,
    required this.mlTrainingJustified,
    required this.mlReadinessNote,
  });

  factory LearningSummary.fromJson(Map<String, dynamic> json) => LearningSummary(
        cropCycleId: json['crop_cycle_id'] as String,
        featureSnapshot: FeatureSnapshot.fromJson(json['feature_snapshot'] as Map<String, dynamic>),
        mlTrainingJustified: json['ml_training_justified'] as bool,
        mlReadinessNote: json['ml_readiness_note'] as String,
      );
}
