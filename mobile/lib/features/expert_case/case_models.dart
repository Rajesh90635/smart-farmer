/// Mirrors backend/app/schemas/case.py:CaseResponse exactly - the
/// farmer-facing case detail. Deliberately has NO field for the assigned
/// expert's identity/name/location/rating, because CaseResponse itself
/// has none - confirmed by reading the actual backend schema and
/// service code before writing this class, not assumed. finalVerifiedClass
/// and finalVerificationSource are the only "result" fields a farmer can
/// see; finalVerificationSource is a ROLE string ("expert"/"field_agent"),
/// never a person's name.
library;

class ExpertCase {
  final String id;
  final String cropCycleId;
  final String? cropPhotoId;
  final String? aiAnalysisId;
  final String requestedProfessionalRole;
  final String reason;
  final String status;
  final String priority;
  final String? finalVerifiedClass;
  final String? finalVerificationSource;
  final int secondOpinionCount;
  final String createdAt;
  final String? closedAt;

  ExpertCase({
    required this.id,
    required this.cropCycleId,
    this.cropPhotoId,
    this.aiAnalysisId,
    required this.requestedProfessionalRole,
    required this.reason,
    required this.status,
    required this.priority,
    this.finalVerifiedClass,
    this.finalVerificationSource,
    required this.secondOpinionCount,
    required this.createdAt,
    this.closedAt,
  });

  bool get isCompleted => status == 'verified' || status == 'rejected' || status == 'closed';

  factory ExpertCase.fromJson(Map<String, dynamic> json) => ExpertCase(
        id: json['id'] as String,
        cropCycleId: json['crop_cycle_id'] as String,
        cropPhotoId: json['crop_photo_id'] as String?,
        aiAnalysisId: json['ai_analysis_id'] as String?,
        requestedProfessionalRole: json['requested_professional_role'] as String,
        reason: json['reason'] as String,
        status: json['status'] as String,
        priority: json['priority'] as String,
        finalVerifiedClass: json['final_verified_class'] as String?,
        finalVerificationSource: json['final_verification_source'] as String?,
        secondOpinionCount: json['second_opinion_count'] as int? ?? 0,
        createdAt: json['created_at'] as String,
        closedAt: json['closed_at'] as String?,
      );
}

/// One entry from GET /cases/{id}/audit - the ONLY farmer-visible history
/// of what happened to a case. Confirmed by reading the actual endpoint:
/// it returns only action/actor_role/occurred_at - no notes, no outcome
/// text, no identity.
class CaseAuditEntry {
  final String action;
  final String actorRole;
  final String occurredAt;

  CaseAuditEntry({required this.action, required this.actorRole, required this.occurredAt});

  factory CaseAuditEntry.fromJson(Map<String, dynamic> json) => CaseAuditEntry(
        action: json['action'] as String,
        actorRole: json['actor_role'] as String,
        occurredAt: json['occurred_at'] as String,
      );
}

/// Maps the ACTUAL backend CaseStatus enum values (open,
/// waiting_for_assignment, assigned, in_review, needs_more_information,
/// verified, rejected, escalated, closed, cancelled - confirmed from
/// backend/app/models/crop_health_case.py, none invented) to the l10n key
/// name for the farmer-friendly sentence. An unrecognized status falls
/// back to the raw value itself, same convention as
/// qualityReasonMessageKeys - never invents wording for a status that
/// doesn't match a known value.
const Map<String, String> caseStatusMessageKeys = {
  'open': 'caseStatusOpen',
  'waiting_for_assignment': 'caseStatusWaitingForAssignment',
  'assigned': 'caseStatusAssigned',
  'in_review': 'caseStatusInReview',
  'needs_more_information': 'caseStatusNeedsMoreInformation',
  'verified': 'caseStatusVerified',
  'rejected': 'caseStatusRejected',
  'escalated': 'caseStatusEscalated',
  'closed': 'caseStatusClosed',
  'cancelled': 'caseStatusCancelled',
};
