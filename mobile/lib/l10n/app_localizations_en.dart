// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Smart Farmer';

  @override
  String get welcomeTitle => 'Welcome to Smart Farmer';

  @override
  String get navHome => 'Home';

  @override
  String get navCamera => 'Camera';

  @override
  String get navMyFarm => 'My Farm';

  @override
  String get navMarket => 'Market';

  @override
  String get navAssistant => 'Assistant';

  @override
  String get navProfile => 'Profile';

  @override
  String get loadingLabel => 'Loading...';

  @override
  String get offlineBannerText =>
      'You\'re offline. We\'ll save this and sync it later.';

  @override
  String get genericErrorTitle => 'Something went wrong';

  @override
  String get genericErrorRetry => 'Try again';

  @override
  String get checkCropTitle => 'Check Crop';

  @override
  String get guidanceKeepLeafInFrame => 'Keep the leaf inside the frame';

  @override
  String get guidanceAvoidShadows => 'Avoid strong shadows';

  @override
  String get guidanceAvoidSunlight => 'Avoid extreme sunlight';

  @override
  String get guidanceHoldSteady => 'Keep the camera steady';

  @override
  String get guidanceCaptureAffectedArea => 'Capture the affected part clearly';

  @override
  String get guidanceAvoidWaterDroplets => 'Avoid water droplets on the lens';

  @override
  String get guidanceCloseButComplete => 'Take a close but complete photo';

  @override
  String get takePhotoButton => 'Take Photo';

  @override
  String get chooseFromGalleryButton => 'Choose from Gallery';

  @override
  String get retakeButton => 'Retake';

  @override
  String get usePhotoButton => 'Use Photo';

  @override
  String get uploadingPhoto => 'Uploading...';

  @override
  String get uploadSuccess => 'Uploaded successfully.';

  @override
  String get uploadFailed => 'Upload failed.';

  @override
  String get photoNeedsAnotherTry => 'Photo needs another try.';

  @override
  String get analyzeCropButton => 'Analyze Crop';

  @override
  String get analyzingCrop => 'Analyzing your crop photo...';

  @override
  String get qualityRejectedCannotAnalyze =>
      'Please retake the photo before requesting AI analysis.';

  @override
  String get analyzeAgainButton => 'Analyze Again';

  @override
  String get requestExpertReviewButton => 'Request Expert Review';

  @override
  String get requestingExpertReview => 'Sending your request...';

  @override
  String get expertReviewSectionTitle => 'Expert Review';

  @override
  String get refreshStatusButton => 'Check for Updates';

  @override
  String get finalFindingLabel => 'Finding';

  @override
  String get reviewedByLabel => 'Reviewed by';

  @override
  String get caseStatusOpen => 'Your request has been received.';

  @override
  String get caseStatusWaitingForAssignment =>
      'Your expert review request is waiting to be assigned.';

  @override
  String get caseStatusAssigned =>
      'An expert has been assigned to review your case.';

  @override
  String get caseStatusInReview =>
      'An expert is currently reviewing your case.';

  @override
  String get caseStatusNeedsMoreInformation =>
      'The expert needs more information. Please check for details.';

  @override
  String get caseStatusVerified => 'Your expert review is complete.';

  @override
  String get caseStatusRejected => 'Your expert review is complete.';

  @override
  String get caseStatusEscalated =>
      'Your case has been escalated for further review.';

  @override
  String get caseStatusClosed => 'This case is closed.';

  @override
  String get caseStatusCancelled => 'This case was cancelled.';

  @override
  String get listenButton => 'Listen';

  @override
  String get voiceUnavailable =>
      'Voice is not available right now. Please read the message above.';

  @override
  String get dailyBriefingTitle => 'Today\'s Briefing';

  @override
  String get weatherTitle => 'Weather';

  @override
  String get weatherUnavailable =>
      'Weather information is currently unavailable.';

  @override
  String get weatherStale =>
      'Showing the last available weather update - it may not be current.';

  @override
  String get forecastLabel => 'Forecast';

  @override
  String get cropActionsLabel => 'Crop Actions';

  @override
  String get sprayConditionWarning =>
      'Weather conditions may not be suitable for spraying right now.';

  @override
  String get tasksTitle => 'Tasks';

  @override
  String get addTaskTitle => 'Add Task';

  @override
  String get taskTitleLabel => 'Task';

  @override
  String get taskTypeLabel => 'Type';

  @override
  String get pickDueDateButton => 'Pick due date (optional)';

  @override
  String get saveTaskButton => 'Save';

  @override
  String get noTasksYet => 'No tasks yet. Tap + to add one.';

  @override
  String get overdueTasksLabel => 'Overdue';

  @override
  String get upcomingTasksLabel => 'Upcoming';

  @override
  String get completedTasksLabel => 'Completed';

  @override
  String get cancelledTasksLabel => 'Cancelled';

  @override
  String get dueDateLabel => 'Due';

  @override
  String get completeTaskButton => 'Done';

  @override
  String get cancelTaskButton => 'Cancel';

  @override
  String get ledgerTitle => 'Financial Ledger';

  @override
  String get addLedgerEntryTitle => 'Add Entry';

  @override
  String get expenseLabel => 'Expense';

  @override
  String get revenueLabel => 'Revenue';

  @override
  String get categoryLabel => 'Category';

  @override
  String get amountLabel => 'Amount';

  @override
  String get descriptionOptionalLabel => 'Description (optional)';

  @override
  String get saveEntryButton => 'Save';

  @override
  String get totalExpenseLabel => 'Total Expense';

  @override
  String get totalRevenueLabel => 'Total Revenue';

  @override
  String get netLabel => 'Net';

  @override
  String get importSalesButton => 'Import Completed Sales';

  @override
  String get salesImportedMessage => 'Sales imported';

  @override
  String get noNewSalesToImport => 'No new completed sales to import.';

  @override
  String get noLedgerEntriesYet => 'No entries yet. Tap + to add one.';

  @override
  String get linkedFromSaleTooltip =>
      'Linked from a completed sale - cannot be edited or deleted here.';

  @override
  String get invoicesTitle => 'Invoices';

  @override
  String get reviewInvoiceTitle => 'Review Invoice';

  @override
  String get reviewInvoiceHint =>
      'These values were read automatically from your photo. Please check and correct them before saving.';

  @override
  String get ocrConfidenceLabel => 'Reading confidence';

  @override
  String get vendorNameOptionalLabel => 'Vendor name (optional)';

  @override
  String get confirmAndAddToLedgerButton => 'Confirm and Add to Ledger';

  @override
  String get invoiceConfirmedMessage => 'Added to your financial ledger.';

  @override
  String get ocrFailedMessage =>
      'Could not read this invoice photo. You can still add the expense manually from the ledger screen.';

  @override
  String get takePhotoOption => 'Take Photo';

  @override
  String get chooseFromGalleryOption => 'Choose from Gallery';

  @override
  String get noInvoicesYet =>
      'No invoices yet. Tap the camera button to add one.';

  @override
  String get confirmedLabel => 'Confirmed';

  @override
  String get notYetConfirmedLabel => 'Not yet confirmed';

  @override
  String get noAmountFoundLabel => 'No amount found';

  @override
  String get financialSummaryTitle => 'Financial Summary';

  @override
  String get addEstimateTitle => 'Add Estimated Cost';

  @override
  String get addEstimateHint =>
      'Enter what you expect to spend. This is your own estimate, not a calculated prediction.';

  @override
  String get estimatedAmountLabel => 'Estimated Amount';

  @override
  String get saveEstimateButton => 'Save';

  @override
  String get costAnalysisLabel => 'Cost Analysis';

  @override
  String get estimatedCostLabel => 'Estimated Cost';

  @override
  String get actualCostLabel => 'Actual Cost';

  @override
  String get costVarianceLabel => 'Cost Variance';

  @override
  String get revenueAndProfitLabel => 'Revenue and Profit';

  @override
  String get expectedRevenueLabel => 'Expected Revenue';

  @override
  String get actualRevenueLabel => 'Actual Revenue';

  @override
  String get estimatedProfitLabel => 'Estimated Profit';

  @override
  String get actualProfitLossLabel => 'Actual Profit/Loss';

  @override
  String get noRevenueYetHint =>
      'No sale recorded yet - this reflects costs so far, not a confirmed loss.';

  @override
  String get notAvailableLabel => 'Not available';

  @override
  String get stageWiseBreakdownTitle => 'Stage-wise Breakdown';

  @override
  String get stageLabel => 'Stage';

  @override
  String get estimatedShortLabel => 'Est.';

  @override
  String get actualShortLabel => 'Actual';

  @override
  String get varianceShortLabel => 'Variance';

  @override
  String get profitForecastTitle => 'Profit Forecast';

  @override
  String get costProjectionLabel => 'Cost Projection';

  @override
  String get actualCostSoFarLabel => 'Actual Cost So Far';

  @override
  String get remainingEstimatedCostLabel => 'Remaining Estimated Cost';

  @override
  String get projectedTotalCostLabel => 'Projected Total Cost';

  @override
  String get revenueProjectionLabel => 'Revenue Projection';

  @override
  String get actualRevenueReceivedLabel => 'Actual Revenue Received';

  @override
  String get committedRevenueLabel =>
      'Committed Revenue (agreed, not yet completed)';

  @override
  String get potentialAdditionalRevenueLabel => 'Potential Additional Revenue';

  @override
  String get projectedTotalRevenueLabel => 'Projected Total Revenue';

  @override
  String get partialRevenueProjectionHint =>
      'This may not include unsold or unlisted harvest - see notes below.';

  @override
  String get projectedProfitLossLabel => 'Projected Profit/Loss';

  @override
  String get projectedProfitLossPercentLabel => 'Projected Profit/Loss %';

  @override
  String get whatsMissingLabel => 'What\'s missing';

  @override
  String get cropRiskTitle => 'Crop Risk';

  @override
  String get overallRiskLabel => 'Overall Risk';

  @override
  String get contributingFactorsLabel => 'Contributing Factors';

  @override
  String get sourceLabel => 'Source';

  @override
  String get suggestionLabel => 'Suggestion';

  @override
  String get riskHighLabel => 'HIGH';

  @override
  String get riskMediumLabel => 'MEDIUM';

  @override
  String get riskLowLabel => 'LOW';

  @override
  String get riskUnknownLabel => 'UNKNOWN';

  @override
  String get riskInsufficientDataLabel => 'INSUFFICIENT DATA';

  @override
  String get treatmentsTitle => 'Treatments';

  @override
  String get recordTreatmentTitle => 'Record Treatment';

  @override
  String get saveTreatmentButton => 'Save';

  @override
  String get notesOptionalLabel => 'Notes (optional)';

  @override
  String get noTreatmentsYet => 'No treatments recorded yet. Tap + to add one.';

  @override
  String get appliedOnLabel => 'Applied on';

  @override
  String get recordFollowUpButton => 'Record Follow-up';

  @override
  String get recordFollowUpTitle => 'Record Follow-up';

  @override
  String get recordFollowUpHint =>
      'To compare crop health, analyze a new crop photo first, then link it here.';

  @override
  String get saveFollowUpButton => 'Save';

  @override
  String get effectivenessImprovedLabel => 'IMPROVED';

  @override
  String get effectivenessWorsenedLabel => 'WORSENED';

  @override
  String get effectivenessNoChangeLabel => 'NO SIGNIFICANT CHANGE';

  @override
  String get effectivenessInsufficientEvidenceLabel => 'INSUFFICIENT EVIDENCE';

  @override
  String get healthTimelineTitle => 'Health Timeline';

  @override
  String get noHealthObservationsYet => 'No health observations recorded yet.';

  @override
  String get timelineCropStartedLabel => 'Crop cycle started';

  @override
  String get timelineStageChangedLabel => 'Growth stage changed';

  @override
  String get timelinePhotoCapturedLabel => 'Photo captured';

  @override
  String get timelineHealthCheckLabel => 'Health check';

  @override
  String get timelineExpertReviewRequestedLabel => 'Expert review requested';

  @override
  String get timelineExpertReviewCompletedLabel => 'Expert review completed';

  @override
  String get timelineTreatmentAppliedLabel => 'Treatment applied';

  @override
  String get timelineFollowUpRecordedLabel => 'Follow-up recorded';

  @override
  String get timelineHarvestedLabel => 'Harvested';

  @override
  String get cropAssistantTitle => 'AI Crop Assistant';

  @override
  String get askAboutYourCropLabel => 'Ask about your crop';

  @override
  String get typeYourQuestionHint => 'Type your question...';

  @override
  String get basedOnYourCropRecordsLabel => 'Based on your crop records:';

  @override
  String get assistantSuggestionCropStatus => 'What is happening to my crop?';

  @override
  String get assistantSuggestionDisease =>
      'What was my last health observation?';

  @override
  String get assistantSuggestionTreatment => 'Did the treatment help?';

  @override
  String get assistantSuggestionFinancial => 'How much have I spent?';

  @override
  String get weatherActionAdvisorTitle => 'Weather Action Advisor';

  @override
  String get weatherActionSafeLabel => 'SAFE';

  @override
  String get weatherActionCautionLabel => 'CAUTION';

  @override
  String get weatherActionUnsafeLabel => 'UNSAFE';

  @override
  String get weatherActionUnknownLabel => 'UNKNOWN';

  @override
  String get weatherActionSprayLabel => 'Spraying';

  @override
  String get weatherActionIrrigationLabel => 'Irrigation';

  @override
  String get weatherActionHarvestLabel => 'Harvest';

  @override
  String get weatherDataInsufficientMessage =>
      'Weather data is insufficient to safely determine recommendations right now.';

  @override
  String get weatherStaleWarning => 'This weather data may be out of date.';

  @override
  String get recommendedSprayWindowLabel => 'Recommended spray window';

  @override
  String get retryUploadButton => 'Retry';

  @override
  String get waitingForNetwork => 'Waiting for network...';

  @override
  String get photoTooDark => 'Photo is too dark. Please take another photo.';

  @override
  String get photoTooBright =>
      'Photo is too bright. Please take another photo.';

  @override
  String get photoTooBlurry =>
      'Photo may be blurry. Please take another photo.';

  @override
  String get sharePhotoLocationQuestion => 'Share this photo\'s location?';

  @override
  String get myCropPhotosTitle => 'Crop Photos';

  @override
  String get noPhotosYet => 'No photos yet. Tap below to check your crop.';

  @override
  String get photoDetailTitle => 'Photo';

  @override
  String get deletePhotoConfirm => 'Remove this photo?';

  @override
  String get photoDeleted => 'Photo removed.';
}
