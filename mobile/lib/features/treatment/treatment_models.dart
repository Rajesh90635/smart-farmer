/// Mirrors backend/app/schemas/treatment.py exactly. Effectiveness is
/// computed server-side ONLY from real AIAnalysis.result_status values -
/// this Flutter model has no method that could derive a result from
/// notes or any other source. `result` is always one of exactly four
/// values: 'improved' | 'no_significant_change' | 'worsened' |
/// 'insufficient_evidence' - never a fabricated fifth state.
library;

class TreatmentRecord {
  final String id;
  final String cropCycleId;
  final String? caseId;
  final String? productId;
  final String? beforeAnalysisId;
  final String? beforeResultStatus;
  final String applicationDate;
  final String? notes;
  final String createdAt;

  TreatmentRecord({
    required this.id,
    required this.cropCycleId,
    this.caseId,
    this.productId,
    this.beforeAnalysisId,
    this.beforeResultStatus,
    required this.applicationDate,
    this.notes,
    required this.createdAt,
  });

  factory TreatmentRecord.fromJson(Map<String, dynamic> json) => TreatmentRecord(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        caseId: json['case_id'] as String?,
        productId: json['product_id'] as String?,
        beforeAnalysisId: json['before_analysis_id'] as String?,
        beforeResultStatus: json['before_result_status'] as String?,
        applicationDate: json['application_date'] as String,
        notes: json['notes'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class TreatmentFollowUp {
  final String id;
  final String treatmentId;
  final String? afterAnalysisId;
  final String? afterResultStatus;
  final String observationDate;
  final String? notes;
  final String createdAt;

  TreatmentFollowUp({
    required this.id,
    required this.treatmentId,
    this.afterAnalysisId,
    this.afterResultStatus,
    required this.observationDate,
    this.notes,
    required this.createdAt,
  });

  factory TreatmentFollowUp.fromJson(Map<String, dynamic> json) => TreatmentFollowUp(
        id: json['id'] as String,
        treatmentId: json['treatment_id'] as String,
        afterAnalysisId: json['after_analysis_id'] as String?,
        afterResultStatus: json['after_result_status'] as String?,
        observationDate: json['observation_date'] as String,
        notes: json['notes'] as String?,
        createdAt: json['created_at'] as String,
      );
}

class TreatmentEffectiveness {
  final String treatmentId;
  final String result;
  final String basis;
  final String? beforeResultStatus;
  final String? afterResultStatus;
  final bool hasFollowUp;

  TreatmentEffectiveness({
    required this.treatmentId,
    required this.result,
    required this.basis,
    this.beforeResultStatus,
    this.afterResultStatus,
    required this.hasFollowUp,
  });

  factory TreatmentEffectiveness.fromJson(Map<String, dynamic> json) => TreatmentEffectiveness(
        treatmentId: json['treatment_id'] as String,
        result: json['result'] as String,
        basis: json['basis'] as String,
        beforeResultStatus: json['before_result_status'] as String?,
        afterResultStatus: json['after_result_status'] as String?,
        hasFollowUp: json['has_follow_up'] as bool,
      );
}
