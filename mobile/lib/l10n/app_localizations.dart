import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en')];

  /// Displayed app name
  ///
  /// In en, this message translates to:
  /// **'Smart Farmer'**
  String get appTitle;

  /// No description provided for @welcomeTitle.
  ///
  /// In en, this message translates to:
  /// **'Welcome to Smart Farmer'**
  String get welcomeTitle;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navCamera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get navCamera;

  /// No description provided for @navMyFarm.
  ///
  /// In en, this message translates to:
  /// **'My Farm'**
  String get navMyFarm;

  /// No description provided for @navMarket.
  ///
  /// In en, this message translates to:
  /// **'Market'**
  String get navMarket;

  /// No description provided for @navAssistant.
  ///
  /// In en, this message translates to:
  /// **'Assistant'**
  String get navAssistant;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @loadingLabel.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loadingLabel;

  /// No description provided for @offlineBannerText.
  ///
  /// In en, this message translates to:
  /// **'You\'re offline. We\'ll save this and sync it later.'**
  String get offlineBannerText;

  /// No description provided for @genericErrorTitle.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong'**
  String get genericErrorTitle;

  /// No description provided for @genericErrorRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get genericErrorRetry;

  /// No description provided for @checkCropTitle.
  ///
  /// In en, this message translates to:
  /// **'Check Crop'**
  String get checkCropTitle;

  /// No description provided for @guidanceKeepLeafInFrame.
  ///
  /// In en, this message translates to:
  /// **'Keep the leaf inside the frame'**
  String get guidanceKeepLeafInFrame;

  /// No description provided for @guidanceAvoidShadows.
  ///
  /// In en, this message translates to:
  /// **'Avoid strong shadows'**
  String get guidanceAvoidShadows;

  /// No description provided for @guidanceAvoidSunlight.
  ///
  /// In en, this message translates to:
  /// **'Avoid extreme sunlight'**
  String get guidanceAvoidSunlight;

  /// No description provided for @guidanceHoldSteady.
  ///
  /// In en, this message translates to:
  /// **'Keep the camera steady'**
  String get guidanceHoldSteady;

  /// No description provided for @guidanceCaptureAffectedArea.
  ///
  /// In en, this message translates to:
  /// **'Capture the affected part clearly'**
  String get guidanceCaptureAffectedArea;

  /// No description provided for @guidanceAvoidWaterDroplets.
  ///
  /// In en, this message translates to:
  /// **'Avoid water droplets on the lens'**
  String get guidanceAvoidWaterDroplets;

  /// No description provided for @guidanceCloseButComplete.
  ///
  /// In en, this message translates to:
  /// **'Take a close but complete photo'**
  String get guidanceCloseButComplete;

  /// No description provided for @takePhotoButton.
  ///
  /// In en, this message translates to:
  /// **'Take Photo'**
  String get takePhotoButton;

  /// No description provided for @chooseFromGalleryButton.
  ///
  /// In en, this message translates to:
  /// **'Choose from Gallery'**
  String get chooseFromGalleryButton;

  /// No description provided for @retakeButton.
  ///
  /// In en, this message translates to:
  /// **'Retake'**
  String get retakeButton;

  /// No description provided for @usePhotoButton.
  ///
  /// In en, this message translates to:
  /// **'Use Photo'**
  String get usePhotoButton;

  /// No description provided for @uploadingPhoto.
  ///
  /// In en, this message translates to:
  /// **'Uploading...'**
  String get uploadingPhoto;

  /// No description provided for @uploadSuccess.
  ///
  /// In en, this message translates to:
  /// **'Uploaded successfully.'**
  String get uploadSuccess;

  /// No description provided for @uploadFailed.
  ///
  /// In en, this message translates to:
  /// **'Upload failed.'**
  String get uploadFailed;

  /// No description provided for @photoNeedsAnotherTry.
  ///
  /// In en, this message translates to:
  /// **'Photo needs another try.'**
  String get photoNeedsAnotherTry;

  /// No description provided for @analyzeCropButton.
  ///
  /// In en, this message translates to:
  /// **'Analyze Crop'**
  String get analyzeCropButton;

  /// No description provided for @analyzingCrop.
  ///
  /// In en, this message translates to:
  /// **'Analyzing your crop photo...'**
  String get analyzingCrop;

  /// No description provided for @qualityRejectedCannotAnalyze.
  ///
  /// In en, this message translates to:
  /// **'Please retake the photo before requesting AI analysis.'**
  String get qualityRejectedCannotAnalyze;

  /// No description provided for @analyzeAgainButton.
  ///
  /// In en, this message translates to:
  /// **'Analyze Again'**
  String get analyzeAgainButton;

  /// No description provided for @requestExpertReviewButton.
  ///
  /// In en, this message translates to:
  /// **'Request Expert Review'**
  String get requestExpertReviewButton;

  /// No description provided for @requestingExpertReview.
  ///
  /// In en, this message translates to:
  /// **'Sending your request...'**
  String get requestingExpertReview;

  /// No description provided for @expertReviewSectionTitle.
  ///
  /// In en, this message translates to:
  /// **'Expert Review'**
  String get expertReviewSectionTitle;

  /// No description provided for @refreshStatusButton.
  ///
  /// In en, this message translates to:
  /// **'Check for Updates'**
  String get refreshStatusButton;

  /// No description provided for @finalFindingLabel.
  ///
  /// In en, this message translates to:
  /// **'Finding'**
  String get finalFindingLabel;

  /// No description provided for @reviewedByLabel.
  ///
  /// In en, this message translates to:
  /// **'Reviewed by'**
  String get reviewedByLabel;

  /// No description provided for @caseStatusOpen.
  ///
  /// In en, this message translates to:
  /// **'Your request has been received.'**
  String get caseStatusOpen;

  /// No description provided for @caseStatusWaitingForAssignment.
  ///
  /// In en, this message translates to:
  /// **'Your expert review request is waiting to be assigned.'**
  String get caseStatusWaitingForAssignment;

  /// No description provided for @caseStatusAssigned.
  ///
  /// In en, this message translates to:
  /// **'An expert has been assigned to review your case.'**
  String get caseStatusAssigned;

  /// No description provided for @caseStatusInReview.
  ///
  /// In en, this message translates to:
  /// **'An expert is currently reviewing your case.'**
  String get caseStatusInReview;

  /// No description provided for @caseStatusNeedsMoreInformation.
  ///
  /// In en, this message translates to:
  /// **'The expert needs more information. Please check for details.'**
  String get caseStatusNeedsMoreInformation;

  /// No description provided for @caseStatusVerified.
  ///
  /// In en, this message translates to:
  /// **'Your expert review is complete.'**
  String get caseStatusVerified;

  /// No description provided for @caseStatusRejected.
  ///
  /// In en, this message translates to:
  /// **'Your expert review is complete.'**
  String get caseStatusRejected;

  /// No description provided for @caseStatusEscalated.
  ///
  /// In en, this message translates to:
  /// **'Your case has been escalated for further review.'**
  String get caseStatusEscalated;

  /// No description provided for @caseStatusClosed.
  ///
  /// In en, this message translates to:
  /// **'This case is closed.'**
  String get caseStatusClosed;

  /// No description provided for @caseStatusCancelled.
  ///
  /// In en, this message translates to:
  /// **'This case was cancelled.'**
  String get caseStatusCancelled;

  /// No description provided for @listenButton.
  ///
  /// In en, this message translates to:
  /// **'Listen'**
  String get listenButton;

  /// No description provided for @voiceUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Voice is not available right now. Please read the message above.'**
  String get voiceUnavailable;

  /// No description provided for @dailyBriefingTitle.
  ///
  /// In en, this message translates to:
  /// **'Today\'s Briefing'**
  String get dailyBriefingTitle;

  /// No description provided for @weatherTitle.
  ///
  /// In en, this message translates to:
  /// **'Weather'**
  String get weatherTitle;

  /// No description provided for @weatherUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Weather information is currently unavailable.'**
  String get weatherUnavailable;

  /// No description provided for @weatherStale.
  ///
  /// In en, this message translates to:
  /// **'Showing the last available weather update - it may not be current.'**
  String get weatherStale;

  /// No description provided for @forecastLabel.
  ///
  /// In en, this message translates to:
  /// **'Forecast'**
  String get forecastLabel;

  /// No description provided for @cropActionsLabel.
  ///
  /// In en, this message translates to:
  /// **'Crop Actions'**
  String get cropActionsLabel;

  /// No description provided for @sprayConditionWarning.
  ///
  /// In en, this message translates to:
  /// **'Weather conditions may not be suitable for spraying right now.'**
  String get sprayConditionWarning;

  /// No description provided for @tasksTitle.
  ///
  /// In en, this message translates to:
  /// **'Tasks'**
  String get tasksTitle;

  /// No description provided for @addTaskTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Task'**
  String get addTaskTitle;

  /// No description provided for @taskTitleLabel.
  ///
  /// In en, this message translates to:
  /// **'Task'**
  String get taskTitleLabel;

  /// No description provided for @taskTypeLabel.
  ///
  /// In en, this message translates to:
  /// **'Type'**
  String get taskTypeLabel;

  /// No description provided for @pickDueDateButton.
  ///
  /// In en, this message translates to:
  /// **'Pick due date (optional)'**
  String get pickDueDateButton;

  /// No description provided for @saveTaskButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveTaskButton;

  /// No description provided for @noTasksYet.
  ///
  /// In en, this message translates to:
  /// **'No tasks yet. Tap + to add one.'**
  String get noTasksYet;

  /// No description provided for @overdueTasksLabel.
  ///
  /// In en, this message translates to:
  /// **'Overdue'**
  String get overdueTasksLabel;

  /// No description provided for @upcomingTasksLabel.
  ///
  /// In en, this message translates to:
  /// **'Upcoming'**
  String get upcomingTasksLabel;

  /// No description provided for @completedTasksLabel.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get completedTasksLabel;

  /// No description provided for @cancelledTasksLabel.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get cancelledTasksLabel;

  /// No description provided for @dueDateLabel.
  ///
  /// In en, this message translates to:
  /// **'Due'**
  String get dueDateLabel;

  /// No description provided for @completeTaskButton.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get completeTaskButton;

  /// No description provided for @cancelTaskButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancelTaskButton;

  /// No description provided for @retryUploadButton.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retryUploadButton;

  /// No description provided for @waitingForNetwork.
  ///
  /// In en, this message translates to:
  /// **'Waiting for network...'**
  String get waitingForNetwork;

  /// No description provided for @photoTooDark.
  ///
  /// In en, this message translates to:
  /// **'Photo is too dark. Please take another photo.'**
  String get photoTooDark;

  /// No description provided for @photoTooBright.
  ///
  /// In en, this message translates to:
  /// **'Photo is too bright. Please take another photo.'**
  String get photoTooBright;

  /// No description provided for @photoTooBlurry.
  ///
  /// In en, this message translates to:
  /// **'Photo may be blurry. Please take another photo.'**
  String get photoTooBlurry;

  /// No description provided for @sharePhotoLocationQuestion.
  ///
  /// In en, this message translates to:
  /// **'Share this photo\'s location?'**
  String get sharePhotoLocationQuestion;

  /// No description provided for @myCropPhotosTitle.
  ///
  /// In en, this message translates to:
  /// **'Crop Photos'**
  String get myCropPhotosTitle;

  /// No description provided for @noPhotosYet.
  ///
  /// In en, this message translates to:
  /// **'No photos yet. Tap below to check your crop.'**
  String get noPhotosYet;

  /// No description provided for @photoDetailTitle.
  ///
  /// In en, this message translates to:
  /// **'Photo'**
  String get photoDetailTitle;

  /// No description provided for @deletePhotoConfirm.
  ///
  /// In en, this message translates to:
  /// **'Remove this photo?'**
  String get deletePhotoConfirm;

  /// No description provided for @photoDeleted.
  ///
  /// In en, this message translates to:
  /// **'Photo removed.'**
  String get photoDeleted;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
