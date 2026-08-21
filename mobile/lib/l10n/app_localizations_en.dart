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
