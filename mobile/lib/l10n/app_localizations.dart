import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_kn.dart';
import 'app_localizations_ml.dart';
import 'app_localizations_mr.dart';
import 'app_localizations_ta.dart';
import 'app_localizations_te.dart';

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
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('kn'),
    Locale('ml'),
    Locale('mr'),
    Locale('ta'),
    Locale('te')
  ];

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

  /// No description provided for @welcomeTagline.
  ///
  /// In en, this message translates to:
  /// **'Your farm, understood.'**
  String get welcomeTagline;

  /// No description provided for @getStartedButton.
  ///
  /// In en, this message translates to:
  /// **'Get started'**
  String get getStartedButton;

  /// No description provided for @alreadyHaveAccountButton.
  ///
  /// In en, this message translates to:
  /// **'I already have an account'**
  String get alreadyHaveAccountButton;

  /// No description provided for @loginScreenTitle.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get loginScreenTitle;

  /// No description provided for @phoneNumberLabel.
  ///
  /// In en, this message translates to:
  /// **'Phone number'**
  String get phoneNumberLabel;

  /// No description provided for @passwordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get passwordLabel;

  /// No description provided for @passwordRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter your password.'**
  String get passwordRequiredError;

  /// No description provided for @loginButton.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get loginButton;

  /// No description provided for @newHereCreateAccountButton.
  ///
  /// In en, this message translates to:
  /// **'New here? Create an account'**
  String get newHereCreateAccountButton;

  /// No description provided for @forgotPasswordButton.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPasswordButton;

  /// No description provided for @resetPasswordScreenTitle.
  ///
  /// In en, this message translates to:
  /// **'Reset your password'**
  String get resetPasswordScreenTitle;

  /// No description provided for @resetPasswordButton.
  ///
  /// In en, this message translates to:
  /// **'Reset password'**
  String get resetPasswordButton;

  /// No description provided for @resetPasswordFailedMessage.
  ///
  /// In en, this message translates to:
  /// **'Could not reset your password. Please check the phone number and try again.'**
  String get resetPasswordFailedMessage;

  /// No description provided for @loginFailedMessage.
  ///
  /// In en, this message translates to:
  /// **'Login failed.'**
  String get loginFailedMessage;

  /// No description provided for @createAccountTitle.
  ///
  /// In en, this message translates to:
  /// **'Create your account'**
  String get createAccountTitle;

  /// No description provided for @yourNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Your name'**
  String get yourNameLabel;

  /// No description provided for @registerContinueButton.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get registerContinueButton;

  /// No description provided for @alreadyHaveAccountLoginButton.
  ///
  /// In en, this message translates to:
  /// **'Already have an account? Log in'**
  String get alreadyHaveAccountLoginButton;

  /// No description provided for @registrationFailedMessage.
  ///
  /// In en, this message translates to:
  /// **'Registration failed.'**
  String get registrationFailedMessage;

  /// No description provided for @consentScreenTitle.
  ///
  /// In en, this message translates to:
  /// **'Before you continue'**
  String get consentScreenTitle;

  /// No description provided for @agreeTermsOfServiceLabel.
  ///
  /// In en, this message translates to:
  /// **'I agree to the Terms of Service'**
  String get agreeTermsOfServiceLabel;

  /// No description provided for @agreePrivacyPolicyLabel.
  ///
  /// In en, this message translates to:
  /// **'I agree to the Privacy Policy'**
  String get agreePrivacyPolicyLabel;

  /// No description provided for @consentContinueButton.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get consentContinueButton;

  /// No description provided for @chooseYourLanguageTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get chooseYourLanguageTitle;

  /// No description provided for @profileScreenTitle.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profileScreenTitle;

  /// No description provided for @nameLabel.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get nameLabel;

  /// No description provided for @phoneNumberDisplayLabel.
  ///
  /// In en, this message translates to:
  /// **'Phone number'**
  String get phoneNumberDisplayLabel;

  /// No description provided for @languageLabel.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get languageLabel;

  /// No description provided for @saveButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveButton;

  /// No description provided for @editProfileButton.
  ///
  /// In en, this message translates to:
  /// **'Edit profile'**
  String get editProfileButton;

  /// No description provided for @changePasswordButton.
  ///
  /// In en, this message translates to:
  /// **'Change password'**
  String get changePasswordButton;

  /// No description provided for @changePasswordTitle.
  ///
  /// In en, this message translates to:
  /// **'Change Password'**
  String get changePasswordTitle;

  /// No description provided for @currentPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Current password'**
  String get currentPasswordLabel;

  /// No description provided for @newPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'New password'**
  String get newPasswordLabel;

  /// No description provided for @confirmNewPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Confirm new password'**
  String get confirmNewPasswordLabel;

  /// No description provided for @confirmNewPasswordMismatchError.
  ///
  /// In en, this message translates to:
  /// **'Passwords do not match.'**
  String get confirmNewPasswordMismatchError;

  /// No description provided for @passwordChangedMessage.
  ///
  /// In en, this message translates to:
  /// **'Your password has been changed.'**
  String get passwordChangedMessage;

  /// No description provided for @incorrectCurrentPasswordError.
  ///
  /// In en, this message translates to:
  /// **'Your current password is incorrect.'**
  String get incorrectCurrentPasswordError;

  /// No description provided for @logOutButton.
  ///
  /// In en, this message translates to:
  /// **'Log out'**
  String get logOutButton;

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

  /// No description provided for @ledgerTitle.
  ///
  /// In en, this message translates to:
  /// **'Financial Ledger'**
  String get ledgerTitle;

  /// No description provided for @addLedgerEntryTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Entry'**
  String get addLedgerEntryTitle;

  /// No description provided for @expenseLabel.
  ///
  /// In en, this message translates to:
  /// **'Expense'**
  String get expenseLabel;

  /// No description provided for @revenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Revenue'**
  String get revenueLabel;

  /// No description provided for @categoryLabel.
  ///
  /// In en, this message translates to:
  /// **'Category'**
  String get categoryLabel;

  /// No description provided for @amountLabel.
  ///
  /// In en, this message translates to:
  /// **'Amount'**
  String get amountLabel;

  /// No description provided for @descriptionOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Description (optional)'**
  String get descriptionOptionalLabel;

  /// No description provided for @saveEntryButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveEntryButton;

  /// No description provided for @totalExpenseLabel.
  ///
  /// In en, this message translates to:
  /// **'Total Expense'**
  String get totalExpenseLabel;

  /// No description provided for @totalRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Total Revenue'**
  String get totalRevenueLabel;

  /// No description provided for @netLabel.
  ///
  /// In en, this message translates to:
  /// **'Net'**
  String get netLabel;

  /// No description provided for @importSalesButton.
  ///
  /// In en, this message translates to:
  /// **'Import Completed Sales'**
  String get importSalesButton;

  /// No description provided for @salesImportedMessage.
  ///
  /// In en, this message translates to:
  /// **'Sales imported'**
  String get salesImportedMessage;

  /// No description provided for @noNewSalesToImport.
  ///
  /// In en, this message translates to:
  /// **'No new completed sales to import.'**
  String get noNewSalesToImport;

  /// No description provided for @noLedgerEntriesYet.
  ///
  /// In en, this message translates to:
  /// **'No entries yet. Tap + to add one.'**
  String get noLedgerEntriesYet;

  /// No description provided for @linkedFromSaleTooltip.
  ///
  /// In en, this message translates to:
  /// **'Linked from a completed sale - cannot be edited or deleted here.'**
  String get linkedFromSaleTooltip;

  /// No description provided for @invoicesTitle.
  ///
  /// In en, this message translates to:
  /// **'Invoices'**
  String get invoicesTitle;

  /// No description provided for @reviewInvoiceTitle.
  ///
  /// In en, this message translates to:
  /// **'Review Invoice'**
  String get reviewInvoiceTitle;

  /// No description provided for @reviewInvoiceHint.
  ///
  /// In en, this message translates to:
  /// **'These values were read automatically from your photo. Please check and correct them before saving.'**
  String get reviewInvoiceHint;

  /// No description provided for @ocrConfidenceLabel.
  ///
  /// In en, this message translates to:
  /// **'Reading confidence'**
  String get ocrConfidenceLabel;

  /// No description provided for @vendorNameOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Vendor name (optional)'**
  String get vendorNameOptionalLabel;

  /// No description provided for @confirmAndAddToLedgerButton.
  ///
  /// In en, this message translates to:
  /// **'Confirm and Add to Ledger'**
  String get confirmAndAddToLedgerButton;

  /// No description provided for @invoiceConfirmedMessage.
  ///
  /// In en, this message translates to:
  /// **'Added to your financial ledger.'**
  String get invoiceConfirmedMessage;

  /// No description provided for @ocrFailedMessage.
  ///
  /// In en, this message translates to:
  /// **'Could not read this invoice photo. You can still add the expense manually from the ledger screen.'**
  String get ocrFailedMessage;

  /// No description provided for @takePhotoOption.
  ///
  /// In en, this message translates to:
  /// **'Take Photo'**
  String get takePhotoOption;

  /// No description provided for @chooseFromGalleryOption.
  ///
  /// In en, this message translates to:
  /// **'Choose from Gallery'**
  String get chooseFromGalleryOption;

  /// No description provided for @noInvoicesYet.
  ///
  /// In en, this message translates to:
  /// **'No invoices yet. Tap the camera button to add one.'**
  String get noInvoicesYet;

  /// No description provided for @confirmedLabel.
  ///
  /// In en, this message translates to:
  /// **'Confirmed'**
  String get confirmedLabel;

  /// No description provided for @notYetConfirmedLabel.
  ///
  /// In en, this message translates to:
  /// **'Not yet confirmed'**
  String get notYetConfirmedLabel;

  /// No description provided for @noAmountFoundLabel.
  ///
  /// In en, this message translates to:
  /// **'No amount found'**
  String get noAmountFoundLabel;

  /// No description provided for @financialSummaryTitle.
  ///
  /// In en, this message translates to:
  /// **'Financial Summary'**
  String get financialSummaryTitle;

  /// No description provided for @addEstimateTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Estimated Cost'**
  String get addEstimateTitle;

  /// No description provided for @addEstimateHint.
  ///
  /// In en, this message translates to:
  /// **'Enter what you expect to spend. This is your own estimate, not a calculated prediction.'**
  String get addEstimateHint;

  /// No description provided for @estimatedAmountLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated Amount'**
  String get estimatedAmountLabel;

  /// No description provided for @saveEstimateButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveEstimateButton;

  /// No description provided for @myEstimatesTitle.
  ///
  /// In en, this message translates to:
  /// **'My Estimates'**
  String get myEstimatesTitle;

  /// No description provided for @noEstimatesYet.
  ///
  /// In en, this message translates to:
  /// **'No estimates yet. Tap + to add one.'**
  String get noEstimatesYet;

  /// No description provided for @costAnalysisLabel.
  ///
  /// In en, this message translates to:
  /// **'Cost Analysis'**
  String get costAnalysisLabel;

  /// No description provided for @estimatedCostLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated Cost'**
  String get estimatedCostLabel;

  /// No description provided for @actualCostLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual Cost'**
  String get actualCostLabel;

  /// No description provided for @costVarianceLabel.
  ///
  /// In en, this message translates to:
  /// **'Cost Variance'**
  String get costVarianceLabel;

  /// No description provided for @revenueAndProfitLabel.
  ///
  /// In en, this message translates to:
  /// **'Revenue and Profit'**
  String get revenueAndProfitLabel;

  /// No description provided for @expectedRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Expected Revenue'**
  String get expectedRevenueLabel;

  /// No description provided for @actualRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual Revenue'**
  String get actualRevenueLabel;

  /// No description provided for @estimatedProfitLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated Profit'**
  String get estimatedProfitLabel;

  /// No description provided for @actualProfitLossLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual Profit/Loss'**
  String get actualProfitLossLabel;

  /// No description provided for @noRevenueYetHint.
  ///
  /// In en, this message translates to:
  /// **'No sale recorded yet - this reflects costs so far, not a confirmed loss.'**
  String get noRevenueYetHint;

  /// No description provided for @notAvailableLabel.
  ///
  /// In en, this message translates to:
  /// **'Not available'**
  String get notAvailableLabel;

  /// No description provided for @stageWiseBreakdownTitle.
  ///
  /// In en, this message translates to:
  /// **'Stage-wise Breakdown'**
  String get stageWiseBreakdownTitle;

  /// No description provided for @stageLabel.
  ///
  /// In en, this message translates to:
  /// **'Stage'**
  String get stageLabel;

  /// No description provided for @estimatedShortLabel.
  ///
  /// In en, this message translates to:
  /// **'Est.'**
  String get estimatedShortLabel;

  /// No description provided for @actualShortLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual'**
  String get actualShortLabel;

  /// No description provided for @varianceShortLabel.
  ///
  /// In en, this message translates to:
  /// **'Variance'**
  String get varianceShortLabel;

  /// No description provided for @profitForecastTitle.
  ///
  /// In en, this message translates to:
  /// **'Profit Forecast'**
  String get profitForecastTitle;

  /// No description provided for @costProjectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Cost Projection'**
  String get costProjectionLabel;

  /// No description provided for @actualCostSoFarLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual Cost So Far'**
  String get actualCostSoFarLabel;

  /// No description provided for @remainingEstimatedCostLabel.
  ///
  /// In en, this message translates to:
  /// **'Remaining Estimated Cost'**
  String get remainingEstimatedCostLabel;

  /// No description provided for @projectedTotalCostLabel.
  ///
  /// In en, this message translates to:
  /// **'Projected Total Cost'**
  String get projectedTotalCostLabel;

  /// No description provided for @revenueProjectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Revenue Projection'**
  String get revenueProjectionLabel;

  /// No description provided for @actualRevenueReceivedLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual Revenue Received'**
  String get actualRevenueReceivedLabel;

  /// No description provided for @committedRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Committed Revenue (agreed, not yet completed)'**
  String get committedRevenueLabel;

  /// No description provided for @potentialAdditionalRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Potential Additional Revenue'**
  String get potentialAdditionalRevenueLabel;

  /// No description provided for @projectedTotalRevenueLabel.
  ///
  /// In en, this message translates to:
  /// **'Projected Total Revenue'**
  String get projectedTotalRevenueLabel;

  /// No description provided for @partialRevenueProjectionHint.
  ///
  /// In en, this message translates to:
  /// **'This may not include unsold or unlisted harvest - see notes below.'**
  String get partialRevenueProjectionHint;

  /// No description provided for @projectedProfitLossLabel.
  ///
  /// In en, this message translates to:
  /// **'Projected Profit/Loss'**
  String get projectedProfitLossLabel;

  /// No description provided for @projectedProfitLossPercentLabel.
  ///
  /// In en, this message translates to:
  /// **'Projected Profit/Loss %'**
  String get projectedProfitLossPercentLabel;

  /// No description provided for @whatsMissingLabel.
  ///
  /// In en, this message translates to:
  /// **'What\'s missing'**
  String get whatsMissingLabel;

  /// No description provided for @cropRiskTitle.
  ///
  /// In en, this message translates to:
  /// **'Crop Risk'**
  String get cropRiskTitle;

  /// No description provided for @overallRiskLabel.
  ///
  /// In en, this message translates to:
  /// **'Overall Risk'**
  String get overallRiskLabel;

  /// No description provided for @contributingFactorsLabel.
  ///
  /// In en, this message translates to:
  /// **'Contributing Factors'**
  String get contributingFactorsLabel;

  /// No description provided for @sourceLabel.
  ///
  /// In en, this message translates to:
  /// **'Source'**
  String get sourceLabel;

  /// No description provided for @suggestionLabel.
  ///
  /// In en, this message translates to:
  /// **'Suggestion'**
  String get suggestionLabel;

  /// No description provided for @riskHighLabel.
  ///
  /// In en, this message translates to:
  /// **'HIGH'**
  String get riskHighLabel;

  /// No description provided for @riskMediumLabel.
  ///
  /// In en, this message translates to:
  /// **'MEDIUM'**
  String get riskMediumLabel;

  /// No description provided for @riskLowLabel.
  ///
  /// In en, this message translates to:
  /// **'LOW'**
  String get riskLowLabel;

  /// No description provided for @riskUnknownLabel.
  ///
  /// In en, this message translates to:
  /// **'UNKNOWN'**
  String get riskUnknownLabel;

  /// No description provided for @riskInsufficientDataLabel.
  ///
  /// In en, this message translates to:
  /// **'INSUFFICIENT DATA'**
  String get riskInsufficientDataLabel;

  /// No description provided for @treatmentsTitle.
  ///
  /// In en, this message translates to:
  /// **'Treatments'**
  String get treatmentsTitle;

  /// No description provided for @recordTreatmentTitle.
  ///
  /// In en, this message translates to:
  /// **'Record Treatment'**
  String get recordTreatmentTitle;

  /// No description provided for @saveTreatmentButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveTreatmentButton;

  /// No description provided for @notesOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Notes (optional)'**
  String get notesOptionalLabel;

  /// No description provided for @noTreatmentsYet.
  ///
  /// In en, this message translates to:
  /// **'No treatments recorded yet. Tap + to add one.'**
  String get noTreatmentsYet;

  /// No description provided for @appliedOnLabel.
  ///
  /// In en, this message translates to:
  /// **'Applied on'**
  String get appliedOnLabel;

  /// No description provided for @recordFollowUpButton.
  ///
  /// In en, this message translates to:
  /// **'Record Follow-up'**
  String get recordFollowUpButton;

  /// No description provided for @recordFollowUpTitle.
  ///
  /// In en, this message translates to:
  /// **'Record Follow-up'**
  String get recordFollowUpTitle;

  /// No description provided for @recordFollowUpHint.
  ///
  /// In en, this message translates to:
  /// **'To compare crop health, analyze a new crop photo first, then link it here.'**
  String get recordFollowUpHint;

  /// No description provided for @saveFollowUpButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveFollowUpButton;

  /// No description provided for @effectivenessImprovedLabel.
  ///
  /// In en, this message translates to:
  /// **'IMPROVED'**
  String get effectivenessImprovedLabel;

  /// No description provided for @effectivenessWorsenedLabel.
  ///
  /// In en, this message translates to:
  /// **'WORSENED'**
  String get effectivenessWorsenedLabel;

  /// No description provided for @effectivenessNoChangeLabel.
  ///
  /// In en, this message translates to:
  /// **'NO SIGNIFICANT CHANGE'**
  String get effectivenessNoChangeLabel;

  /// No description provided for @effectivenessInsufficientEvidenceLabel.
  ///
  /// In en, this message translates to:
  /// **'INSUFFICIENT EVIDENCE'**
  String get effectivenessInsufficientEvidenceLabel;

  /// No description provided for @harvestsTitle.
  ///
  /// In en, this message translates to:
  /// **'Harvests'**
  String get harvestsTitle;

  /// No description provided for @recordHarvestButton.
  ///
  /// In en, this message translates to:
  /// **'Record Harvest'**
  String get recordHarvestButton;

  /// No description provided for @startAdditionalHarvestButton.
  ///
  /// In en, this message translates to:
  /// **'Start Additional Harvest'**
  String get startAdditionalHarvestButton;

  /// No description provided for @noHarvestsYet.
  ///
  /// In en, this message translates to:
  /// **'No harvests recorded yet for this crop.'**
  String get noHarvestsYet;

  /// No description provided for @harvestStatusPlannedLabel.
  ///
  /// In en, this message translates to:
  /// **'Planned'**
  String get harvestStatusPlannedLabel;

  /// No description provided for @harvestStatusApproachingLabel.
  ///
  /// In en, this message translates to:
  /// **'Approaching'**
  String get harvestStatusApproachingLabel;

  /// No description provided for @harvestStatusReadyLabel.
  ///
  /// In en, this message translates to:
  /// **'Ready'**
  String get harvestStatusReadyLabel;

  /// No description provided for @harvestStatusHarvestedLabel.
  ///
  /// In en, this message translates to:
  /// **'Harvested'**
  String get harvestStatusHarvestedLabel;

  /// No description provided for @harvestStatusListedLabel.
  ///
  /// In en, this message translates to:
  /// **'Listed'**
  String get harvestStatusListedLabel;

  /// No description provided for @harvestStatusPartiallySoldLabel.
  ///
  /// In en, this message translates to:
  /// **'Partially Sold'**
  String get harvestStatusPartiallySoldLabel;

  /// No description provided for @harvestStatusSoldLabel.
  ///
  /// In en, this message translates to:
  /// **'Sold'**
  String get harvestStatusSoldLabel;

  /// No description provided for @harvestStatusCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get harvestStatusCancelledLabel;

  /// No description provided for @markApproachingButton.
  ///
  /// In en, this message translates to:
  /// **'Mark Approaching'**
  String get markApproachingButton;

  /// No description provided for @confirmReadyTitle.
  ///
  /// In en, this message translates to:
  /// **'Confirm Harvest Ready'**
  String get confirmReadyTitle;

  /// No description provided for @actualHarvestDateOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual harvest date (optional)'**
  String get actualHarvestDateOptionalLabel;

  /// No description provided for @estimatedQuantityOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated quantity (optional)'**
  String get estimatedQuantityOptionalLabel;

  /// No description provided for @confirmReadyButton.
  ///
  /// In en, this message translates to:
  /// **'Confirm Ready'**
  String get confirmReadyButton;

  /// No description provided for @createListingTitle.
  ///
  /// In en, this message translates to:
  /// **'Create Harvest Listing'**
  String get createListingTitle;

  /// No description provided for @quantityAvailableLabel.
  ///
  /// In en, this message translates to:
  /// **'Quantity available'**
  String get quantityAvailableLabel;

  /// No description provided for @harvestUnitLabel.
  ///
  /// In en, this message translates to:
  /// **'Unit'**
  String get harvestUnitLabel;

  /// No description provided for @qualityGradeOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Quality grade (optional)'**
  String get qualityGradeOptionalLabel;

  /// No description provided for @deliveryOptionLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery option'**
  String get deliveryOptionLabel;

  /// No description provided for @deliveryOptionBuyerCollectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Buyer collection'**
  String get deliveryOptionBuyerCollectionLabel;

  /// No description provided for @deliveryOptionFarmerDeliveryLabel.
  ///
  /// In en, this message translates to:
  /// **'Farmer delivery'**
  String get deliveryOptionFarmerDeliveryLabel;

  /// No description provided for @deliveryOptionThirdPartyLogisticsLabel.
  ///
  /// In en, this message translates to:
  /// **'Third-party logistics'**
  String get deliveryOptionThirdPartyLogisticsLabel;

  /// No description provided for @preferredPriceOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Preferred price (optional)'**
  String get preferredPriceOptionalLabel;

  /// No description provided for @serviceAreaStateOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'State (optional)'**
  String get serviceAreaStateOptionalLabel;

  /// No description provided for @serviceAreaDistrictOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'District (optional)'**
  String get serviceAreaDistrictOptionalLabel;

  /// No description provided for @listingNotesOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Notes (optional)'**
  String get listingNotesOptionalLabel;

  /// No description provided for @createListingButton.
  ///
  /// In en, this message translates to:
  /// **'Create Listing'**
  String get createListingButton;

  /// No description provided for @duplicateListingTitle.
  ///
  /// In en, this message translates to:
  /// **'Active Listing Already Exists'**
  String get duplicateListingTitle;

  /// No description provided for @duplicateListingMessage.
  ///
  /// In en, this message translates to:
  /// **'You already have an active listing for this harvest.'**
  String get duplicateListingMessage;

  /// No description provided for @createAnotherListingButton.
  ///
  /// In en, this message translates to:
  /// **'Create Another Anyway'**
  String get createAnotherListingButton;

  /// No description provided for @listingCreatedMessage.
  ///
  /// In en, this message translates to:
  /// **'Listing created.'**
  String get listingCreatedMessage;

  /// No description provided for @harvestHistoryTitle.
  ///
  /// In en, this message translates to:
  /// **'Harvest History'**
  String get harvestHistoryTitle;

  /// No description provided for @myHarvestsTabLabel.
  ///
  /// In en, this message translates to:
  /// **'Harvests'**
  String get myHarvestsTabLabel;

  /// No description provided for @myListingsTabLabel.
  ///
  /// In en, this message translates to:
  /// **'Listings'**
  String get myListingsTabLabel;

  /// No description provided for @noHarvestHistoryYet.
  ///
  /// In en, this message translates to:
  /// **'No harvests recorded yet.'**
  String get noHarvestHistoryYet;

  /// No description provided for @noListingsYet.
  ///
  /// In en, this message translates to:
  /// **'No listings yet.'**
  String get noListingsYet;

  /// No description provided for @viewHarvestHistoryButton.
  ///
  /// In en, this message translates to:
  /// **'Harvest History'**
  String get viewHarvestHistoryButton;

  /// No description provided for @listingActiveLabel.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get listingActiveLabel;

  /// No description provided for @listingInactiveLabel.
  ///
  /// In en, this message translates to:
  /// **'Inactive'**
  String get listingInactiveLabel;

  /// No description provided for @marketTitle.
  ///
  /// In en, this message translates to:
  /// **'Market'**
  String get marketTitle;

  /// No description provided for @viewOffersButton.
  ///
  /// In en, this message translates to:
  /// **'View Offers'**
  String get viewOffersButton;

  /// No description provided for @mySalesButton.
  ///
  /// In en, this message translates to:
  /// **'My Sales'**
  String get mySalesButton;

  /// No description provided for @offersTitle.
  ///
  /// In en, this message translates to:
  /// **'Offers'**
  String get offersTitle;

  /// No description provided for @noOffersYet.
  ///
  /// In en, this message translates to:
  /// **'No offers yet for this listing.'**
  String get noOffersYet;

  /// No description provided for @offerStatusActiveLabel.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get offerStatusActiveLabel;

  /// No description provided for @offerStatusExpiredLabel.
  ///
  /// In en, this message translates to:
  /// **'Expired'**
  String get offerStatusExpiredLabel;

  /// No description provided for @offerStatusAcceptedLabel.
  ///
  /// In en, this message translates to:
  /// **'Accepted'**
  String get offerStatusAcceptedLabel;

  /// No description provided for @offerStatusRejectedLabel.
  ///
  /// In en, this message translates to:
  /// **'Rejected'**
  String get offerStatusRejectedLabel;

  /// No description provided for @offerStatusCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get offerStatusCancelledLabel;

  /// No description provided for @offerStatusCompletedLabel.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get offerStatusCompletedLabel;

  /// No description provided for @counterOfferButton.
  ///
  /// In en, this message translates to:
  /// **'Counter Offer'**
  String get counterOfferButton;

  /// No description provided for @acceptOfferButton.
  ///
  /// In en, this message translates to:
  /// **'Accept Offer'**
  String get acceptOfferButton;

  /// No description provided for @rejectOfferButton.
  ///
  /// In en, this message translates to:
  /// **'Reject Offer'**
  String get rejectOfferButton;

  /// No description provided for @counterOfferTitle.
  ///
  /// In en, this message translates to:
  /// **'Send Counter Offer'**
  String get counterOfferTitle;

  /// No description provided for @pricePerUnitLabel.
  ///
  /// In en, this message translates to:
  /// **'Price per unit'**
  String get pricePerUnitLabel;

  /// No description provided for @offerQuantityLabel.
  ///
  /// In en, this message translates to:
  /// **'Quantity'**
  String get offerQuantityLabel;

  /// No description provided for @counterMessageOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Message (optional)'**
  String get counterMessageOptionalLabel;

  /// No description provided for @sendCounterButton.
  ///
  /// In en, this message translates to:
  /// **'Send Counter'**
  String get sendCounterButton;

  /// No description provided for @offerAcceptedMessage.
  ///
  /// In en, this message translates to:
  /// **'Offer accepted. Sale created.'**
  String get offerAcceptedMessage;

  /// No description provided for @offerRejectedMessage.
  ///
  /// In en, this message translates to:
  /// **'Offer rejected.'**
  String get offerRejectedMessage;

  /// No description provided for @counterSentMessage.
  ///
  /// In en, this message translates to:
  /// **'Counter offer sent.'**
  String get counterSentMessage;

  /// No description provided for @salesTitle.
  ///
  /// In en, this message translates to:
  /// **'My Sales'**
  String get salesTitle;

  /// No description provided for @noSalesYet.
  ///
  /// In en, this message translates to:
  /// **'No sales yet.'**
  String get noSalesYet;

  /// No description provided for @saleDetailTitle.
  ///
  /// In en, this message translates to:
  /// **'Sale Details'**
  String get saleDetailTitle;

  /// No description provided for @saleStatusPendingLabel.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get saleStatusPendingLabel;

  /// No description provided for @saleStatusAcceptedLabel.
  ///
  /// In en, this message translates to:
  /// **'Accepted'**
  String get saleStatusAcceptedLabel;

  /// No description provided for @saleStatusPreparingLabel.
  ///
  /// In en, this message translates to:
  /// **'Preparing'**
  String get saleStatusPreparingLabel;

  /// No description provided for @saleStatusReadyForCollectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Ready for Collection'**
  String get saleStatusReadyForCollectionLabel;

  /// No description provided for @saleStatusCollectedLabel.
  ///
  /// In en, this message translates to:
  /// **'Collected'**
  String get saleStatusCollectedLabel;

  /// No description provided for @saleStatusInTransitLabel.
  ///
  /// In en, this message translates to:
  /// **'In Transit'**
  String get saleStatusInTransitLabel;

  /// No description provided for @saleStatusDeliveredLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivered'**
  String get saleStatusDeliveredLabel;

  /// No description provided for @saleStatusPaymentPendingLabel.
  ///
  /// In en, this message translates to:
  /// **'Payment Pending'**
  String get saleStatusPaymentPendingLabel;

  /// No description provided for @saleStatusPaidLabel.
  ///
  /// In en, this message translates to:
  /// **'Paid'**
  String get saleStatusPaidLabel;

  /// No description provided for @saleStatusCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get saleStatusCancelledLabel;

  /// No description provided for @saleStatusDisputedLabel.
  ///
  /// In en, this message translates to:
  /// **'Disputed'**
  String get saleStatusDisputedLabel;

  /// No description provided for @saleStatusCompletedLabel.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get saleStatusCompletedLabel;

  /// No description provided for @grossValueLabel.
  ///
  /// In en, this message translates to:
  /// **'Gross Value'**
  String get grossValueLabel;

  /// No description provided for @chargesLabel.
  ///
  /// In en, this message translates to:
  /// **'Charges'**
  String get chargesLabel;

  /// No description provided for @netValueLabel.
  ///
  /// In en, this message translates to:
  /// **'Net Value'**
  String get netValueLabel;

  /// No description provided for @acceptSaleButton.
  ///
  /// In en, this message translates to:
  /// **'Accept Sale'**
  String get acceptSaleButton;

  /// No description provided for @advanceSaleButton.
  ///
  /// In en, this message translates to:
  /// **'Move to'**
  String get advanceSaleButton;

  /// No description provided for @cancelSaleButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel Sale'**
  String get cancelSaleButton;

  /// No description provided for @cancelSaleTitle.
  ///
  /// In en, this message translates to:
  /// **'Cancel Sale'**
  String get cancelSaleTitle;

  /// No description provided for @cancellationReasonLabel.
  ///
  /// In en, this message translates to:
  /// **'Reason'**
  String get cancellationReasonLabel;

  /// No description provided for @fileDisputeButton.
  ///
  /// In en, this message translates to:
  /// **'File Dispute'**
  String get fileDisputeButton;

  /// No description provided for @fileDisputeTitle.
  ///
  /// In en, this message translates to:
  /// **'File a Dispute'**
  String get fileDisputeTitle;

  /// No description provided for @disputeReasonLabel.
  ///
  /// In en, this message translates to:
  /// **'Reason'**
  String get disputeReasonLabel;

  /// No description provided for @disputeDescriptionOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Description (optional)'**
  String get disputeDescriptionOptionalLabel;

  /// No description provided for @submitDisputeButton.
  ///
  /// In en, this message translates to:
  /// **'Submit Dispute'**
  String get submitDisputeButton;

  /// No description provided for @leaveFeedbackButton.
  ///
  /// In en, this message translates to:
  /// **'Leave Feedback'**
  String get leaveFeedbackButton;

  /// No description provided for @leaveFeedbackTitle.
  ///
  /// In en, this message translates to:
  /// **'Leave Feedback'**
  String get leaveFeedbackTitle;

  /// No description provided for @feedbackRatingOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Rating 1-5 (optional)'**
  String get feedbackRatingOptionalLabel;

  /// No description provided for @feedbackTextOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Comments (optional)'**
  String get feedbackTextOptionalLabel;

  /// No description provided for @submitFeedbackButton.
  ///
  /// In en, this message translates to:
  /// **'Submit Feedback'**
  String get submitFeedbackButton;

  /// No description provided for @saleAcceptedMessage.
  ///
  /// In en, this message translates to:
  /// **'Sale accepted.'**
  String get saleAcceptedMessage;

  /// No description provided for @saleAdvancedMessage.
  ///
  /// In en, this message translates to:
  /// **'Sale updated.'**
  String get saleAdvancedMessage;

  /// No description provided for @saleCancelledMessage.
  ///
  /// In en, this message translates to:
  /// **'Sale cancelled.'**
  String get saleCancelledMessage;

  /// No description provided for @disputeFiledMessage.
  ///
  /// In en, this message translates to:
  /// **'Dispute filed.'**
  String get disputeFiledMessage;

  /// No description provided for @feedbackSubmittedMessage.
  ///
  /// In en, this message translates to:
  /// **'Feedback submitted.'**
  String get feedbackSubmittedMessage;

  /// No description provided for @cancellationReasonPriceDisputeLabel.
  ///
  /// In en, this message translates to:
  /// **'Price dispute'**
  String get cancellationReasonPriceDisputeLabel;

  /// No description provided for @cancellationReasonQuantityChangeLabel.
  ///
  /// In en, this message translates to:
  /// **'Quantity change'**
  String get cancellationReasonQuantityChangeLabel;

  /// No description provided for @cancellationReasonBuyerCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'Buyer cancelled'**
  String get cancellationReasonBuyerCancelledLabel;

  /// No description provided for @cancellationReasonFarmerCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'I want to cancel'**
  String get cancellationReasonFarmerCancelledLabel;

  /// No description provided for @cancellationReasonLogisticsFailureLabel.
  ///
  /// In en, this message translates to:
  /// **'Logistics failure'**
  String get cancellationReasonLogisticsFailureLabel;

  /// No description provided for @cancellationReasonWeatherLabel.
  ///
  /// In en, this message translates to:
  /// **'Weather'**
  String get cancellationReasonWeatherLabel;

  /// No description provided for @disputeReasonWrongQuantityLabel.
  ///
  /// In en, this message translates to:
  /// **'Wrong quantity'**
  String get disputeReasonWrongQuantityLabel;

  /// No description provided for @disputeReasonQualityDisagreementLabel.
  ///
  /// In en, this message translates to:
  /// **'Quality disagreement'**
  String get disputeReasonQualityDisagreementLabel;

  /// No description provided for @disputeReasonPriceDisagreementLabel.
  ///
  /// In en, this message translates to:
  /// **'Price disagreement'**
  String get disputeReasonPriceDisagreementLabel;

  /// No description provided for @disputeReasonPaymentIssueLabel.
  ///
  /// In en, this message translates to:
  /// **'Payment issue'**
  String get disputeReasonPaymentIssueLabel;

  /// No description provided for @disputeReasonDeliveryIssueLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery issue'**
  String get disputeReasonDeliveryIssueLabel;

  /// No description provided for @disputeReasonBuyerCancellationLabel.
  ///
  /// In en, this message translates to:
  /// **'Buyer cancellation'**
  String get disputeReasonBuyerCancellationLabel;

  /// No description provided for @disputeReasonFarmerCancellationLabel.
  ///
  /// In en, this message translates to:
  /// **'Farmer cancellation'**
  String get disputeReasonFarmerCancellationLabel;

  /// No description provided for @disputeReasonDamagedCropLabel.
  ///
  /// In en, this message translates to:
  /// **'Damaged crop'**
  String get disputeReasonDamagedCropLabel;

  /// No description provided for @otherReasonLabel.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get otherReasonLabel;

  /// No description provided for @healthTimelineTitle.
  ///
  /// In en, this message translates to:
  /// **'Health Timeline'**
  String get healthTimelineTitle;

  /// No description provided for @noHealthObservationsYet.
  ///
  /// In en, this message translates to:
  /// **'No health observations recorded yet.'**
  String get noHealthObservationsYet;

  /// No description provided for @timelineCropStartedLabel.
  ///
  /// In en, this message translates to:
  /// **'Crop cycle started'**
  String get timelineCropStartedLabel;

  /// No description provided for @timelineStageChangedLabel.
  ///
  /// In en, this message translates to:
  /// **'Growth stage changed'**
  String get timelineStageChangedLabel;

  /// No description provided for @timelinePhotoCapturedLabel.
  ///
  /// In en, this message translates to:
  /// **'Photo captured'**
  String get timelinePhotoCapturedLabel;

  /// No description provided for @timelineHealthCheckLabel.
  ///
  /// In en, this message translates to:
  /// **'Health check'**
  String get timelineHealthCheckLabel;

  /// No description provided for @timelineExpertReviewRequestedLabel.
  ///
  /// In en, this message translates to:
  /// **'Expert review requested'**
  String get timelineExpertReviewRequestedLabel;

  /// No description provided for @timelineExpertReviewCompletedLabel.
  ///
  /// In en, this message translates to:
  /// **'Expert review completed'**
  String get timelineExpertReviewCompletedLabel;

  /// No description provided for @timelineTreatmentAppliedLabel.
  ///
  /// In en, this message translates to:
  /// **'Treatment applied'**
  String get timelineTreatmentAppliedLabel;

  /// No description provided for @timelineFollowUpRecordedLabel.
  ///
  /// In en, this message translates to:
  /// **'Follow-up recorded'**
  String get timelineFollowUpRecordedLabel;

  /// No description provided for @timelineHarvestedLabel.
  ///
  /// In en, this message translates to:
  /// **'Harvested'**
  String get timelineHarvestedLabel;

  /// No description provided for @cropAssistantTitle.
  ///
  /// In en, this message translates to:
  /// **'AI Crop Assistant'**
  String get cropAssistantTitle;

  /// No description provided for @askAboutYourCropLabel.
  ///
  /// In en, this message translates to:
  /// **'Ask about your crop'**
  String get askAboutYourCropLabel;

  /// No description provided for @typeYourQuestionHint.
  ///
  /// In en, this message translates to:
  /// **'Type your question...'**
  String get typeYourQuestionHint;

  /// No description provided for @basedOnYourCropRecordsLabel.
  ///
  /// In en, this message translates to:
  /// **'Based on your crop records:'**
  String get basedOnYourCropRecordsLabel;

  /// No description provided for @assistantSuggestionCropStatus.
  ///
  /// In en, this message translates to:
  /// **'What is happening to my crop?'**
  String get assistantSuggestionCropStatus;

  /// No description provided for @assistantSuggestionDisease.
  ///
  /// In en, this message translates to:
  /// **'What was my last health observation?'**
  String get assistantSuggestionDisease;

  /// No description provided for @assistantSuggestionTreatment.
  ///
  /// In en, this message translates to:
  /// **'Did the treatment help?'**
  String get assistantSuggestionTreatment;

  /// No description provided for @assistantSuggestionFinancial.
  ///
  /// In en, this message translates to:
  /// **'How much have I spent?'**
  String get assistantSuggestionFinancial;

  /// No description provided for @weatherActionAdvisorTitle.
  ///
  /// In en, this message translates to:
  /// **'Weather Action Advisor'**
  String get weatherActionAdvisorTitle;

  /// No description provided for @weatherActionSafeLabel.
  ///
  /// In en, this message translates to:
  /// **'SAFE'**
  String get weatherActionSafeLabel;

  /// No description provided for @weatherActionCautionLabel.
  ///
  /// In en, this message translates to:
  /// **'CAUTION'**
  String get weatherActionCautionLabel;

  /// No description provided for @weatherActionUnsafeLabel.
  ///
  /// In en, this message translates to:
  /// **'UNSAFE'**
  String get weatherActionUnsafeLabel;

  /// No description provided for @weatherActionUnknownLabel.
  ///
  /// In en, this message translates to:
  /// **'UNKNOWN'**
  String get weatherActionUnknownLabel;

  /// No description provided for @weatherActionSprayLabel.
  ///
  /// In en, this message translates to:
  /// **'Spraying'**
  String get weatherActionSprayLabel;

  /// No description provided for @weatherActionIrrigationLabel.
  ///
  /// In en, this message translates to:
  /// **'Irrigation'**
  String get weatherActionIrrigationLabel;

  /// No description provided for @weatherActionHarvestLabel.
  ///
  /// In en, this message translates to:
  /// **'Harvest'**
  String get weatherActionHarvestLabel;

  /// No description provided for @weatherDataInsufficientMessage.
  ///
  /// In en, this message translates to:
  /// **'Weather data is insufficient to safely determine recommendations right now.'**
  String get weatherDataInsufficientMessage;

  /// No description provided for @weatherStaleWarning.
  ///
  /// In en, this message translates to:
  /// **'This weather data may be out of date.'**
  String get weatherStaleWarning;

  /// No description provided for @recommendedSprayWindowLabel.
  ///
  /// In en, this message translates to:
  /// **'Recommended spray window'**
  String get recommendedSprayWindowLabel;

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

  /// No description provided for @assistantChatTitle.
  ///
  /// In en, this message translates to:
  /// **'Smart Farmer Assistant'**
  String get assistantChatTitle;

  /// No description provided for @assistantEmptyStateHint.
  ///
  /// In en, this message translates to:
  /// **'Ask me about your crops, weather, harvest, orders, and more.'**
  String get assistantEmptyStateHint;

  /// No description provided for @assistantChatSuggestionCropStatus.
  ///
  /// In en, this message translates to:
  /// **'What is happening to my crop?'**
  String get assistantChatSuggestionCropStatus;

  /// No description provided for @assistantChatSuggestionWeather.
  ///
  /// In en, this message translates to:
  /// **'Will it rain today?'**
  String get assistantChatSuggestionWeather;

  /// No description provided for @assistantChatSuggestionHarvest.
  ///
  /// In en, this message translates to:
  /// **'Is my crop ready to harvest?'**
  String get assistantChatSuggestionHarvest;

  /// No description provided for @assistantChatSuggestionOrders.
  ///
  /// In en, this message translates to:
  /// **'Where is my order?'**
  String get assistantChatSuggestionOrders;

  /// No description provided for @assistantSendButtonTooltip.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get assistantSendButtonTooltip;

  /// No description provided for @assistantMarkHelpfulTooltip.
  ///
  /// In en, this message translates to:
  /// **'Helpful'**
  String get assistantMarkHelpfulTooltip;

  /// No description provided for @assistantMarkNotHelpfulTooltip.
  ///
  /// In en, this message translates to:
  /// **'Not helpful'**
  String get assistantMarkNotHelpfulTooltip;

  /// No description provided for @assistantFeedbackThanksMessage.
  ///
  /// In en, this message translates to:
  /// **'Thanks for the feedback.'**
  String get assistantFeedbackThanksMessage;

  /// No description provided for @cameraTabTitle.
  ///
  /// In en, this message translates to:
  /// **'Check a Crop'**
  String get cameraTabTitle;

  /// No description provided for @cameraTabPickCropHint.
  ///
  /// In en, this message translates to:
  /// **'Which crop do you want to check?'**
  String get cameraTabPickCropHint;

  /// No description provided for @cameraTabNoCropsYet.
  ///
  /// In en, this message translates to:
  /// **'You don\'t have any crops yet. Add a farm and crop first from the My Farm tab.'**
  String get cameraTabNoCropsYet;

  /// No description provided for @cameraTabSownOnLabel.
  ///
  /// In en, this message translates to:
  /// **'Sown'**
  String get cameraTabSownOnLabel;

  /// No description provided for @notificationListTitle.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notificationListTitle;

  /// No description provided for @notificationMarkAllReadButton.
  ///
  /// In en, this message translates to:
  /// **'Mark all read'**
  String get notificationMarkAllReadButton;

  /// No description provided for @notificationPreferencesTooltip.
  ///
  /// In en, this message translates to:
  /// **'Preferences'**
  String get notificationPreferencesTooltip;

  /// No description provided for @notificationListEmptyMessage.
  ///
  /// In en, this message translates to:
  /// **'No notifications yet.'**
  String get notificationListEmptyMessage;

  /// No description provided for @notificationPreferencesTitle.
  ///
  /// In en, this message translates to:
  /// **'Notification Preferences'**
  String get notificationPreferencesTitle;

  /// No description provided for @notificationPrefsWeatherAlertsLabel.
  ///
  /// In en, this message translates to:
  /// **'Weather alerts'**
  String get notificationPrefsWeatherAlertsLabel;

  /// No description provided for @notificationPrefsRainAlertsLabel.
  ///
  /// In en, this message translates to:
  /// **'Rain alerts'**
  String get notificationPrefsRainAlertsLabel;

  /// No description provided for @notificationPrefsCropAlertsLabel.
  ///
  /// In en, this message translates to:
  /// **'Crop alerts'**
  String get notificationPrefsCropAlertsLabel;

  /// No description provided for @notificationPrefsDiseaseAlertsLabel.
  ///
  /// In en, this message translates to:
  /// **'Disease alerts'**
  String get notificationPrefsDiseaseAlertsLabel;

  /// No description provided for @notificationPrefsAudioAlertsLabel.
  ///
  /// In en, this message translates to:
  /// **'Audio alerts'**
  String get notificationPrefsAudioAlertsLabel;

  /// No description provided for @notificationPrefsAudioAlertsHint.
  ///
  /// In en, this message translates to:
  /// **'Off by default - opt in to have alerts read aloud'**
  String get notificationPrefsAudioAlertsHint;

  /// No description provided for @notificationPrefsGeneralNotificationsLabel.
  ///
  /// In en, this message translates to:
  /// **'General notifications'**
  String get notificationPrefsGeneralNotificationsLabel;

  /// No description provided for @advisoryFeedbackTitle.
  ///
  /// In en, this message translates to:
  /// **'Give Feedback'**
  String get advisoryFeedbackTitle;

  /// No description provided for @advisoryFeedbackSourcePrompt.
  ///
  /// In en, this message translates to:
  /// **'Which feature is this feedback about?'**
  String get advisoryFeedbackSourcePrompt;

  /// No description provided for @advisorySourceCropAssistantLabel.
  ///
  /// In en, this message translates to:
  /// **'Crop Assistant'**
  String get advisorySourceCropAssistantLabel;

  /// No description provided for @advisorySourceRiskScoreLabel.
  ///
  /// In en, this message translates to:
  /// **'Risk Score'**
  String get advisorySourceRiskScoreLabel;

  /// No description provided for @advisorySourceWeatherActionLabel.
  ///
  /// In en, this message translates to:
  /// **'Weather Action'**
  String get advisorySourceWeatherActionLabel;

  /// No description provided for @advisorySourceIrrigationIntelligenceLabel.
  ///
  /// In en, this message translates to:
  /// **'Irrigation Intelligence'**
  String get advisorySourceIrrigationIntelligenceLabel;

  /// No description provided for @advisorySourceTreatmentRecommendationLabel.
  ///
  /// In en, this message translates to:
  /// **'Treatment Recommendation'**
  String get advisorySourceTreatmentRecommendationLabel;

  /// No description provided for @advisoryFeedbackHelpfulButton.
  ///
  /// In en, this message translates to:
  /// **'Helpful'**
  String get advisoryFeedbackHelpfulButton;

  /// No description provided for @advisoryFeedbackNotHelpfulButton.
  ///
  /// In en, this message translates to:
  /// **'Not Helpful'**
  String get advisoryFeedbackNotHelpfulButton;

  /// No description provided for @advisoryFeedbackWrongButton.
  ///
  /// In en, this message translates to:
  /// **'Wrong'**
  String get advisoryFeedbackWrongButton;

  /// No description provided for @advisoryFeedbackNeedExpertButton.
  ///
  /// In en, this message translates to:
  /// **'Need Expert'**
  String get advisoryFeedbackNeedExpertButton;

  /// No description provided for @advisoryFeedbackThanksMessage.
  ///
  /// In en, this message translates to:
  /// **'Thank you for your feedback.'**
  String get advisoryFeedbackThanksMessage;

  /// No description provided for @learningSummaryTitle.
  ///
  /// In en, this message translates to:
  /// **'Learning Summary'**
  String get learningSummaryTitle;

  /// No description provided for @learningSummaryFeatureVersionLabel.
  ///
  /// In en, this message translates to:
  /// **'Feature version: {version}'**
  String learningSummaryFeatureVersionLabel(String version);

  /// No description provided for @learningSummaryAvailableDataLabel.
  ///
  /// In en, this message translates to:
  /// **'Available data'**
  String get learningSummaryAvailableDataLabel;

  /// No description provided for @learningSummaryOutcomeLabel.
  ///
  /// In en, this message translates to:
  /// **'Outcome'**
  String get learningSummaryOutcomeLabel;

  /// No description provided for @learningSummaryOutcomeNotAvailableMessage.
  ///
  /// In en, this message translates to:
  /// **'Not available yet - this crop has not reached a completed harvest outcome.'**
  String get learningSummaryOutcomeNotAvailableMessage;

  /// No description provided for @personalizationProfileTitle.
  ///
  /// In en, this message translates to:
  /// **'Your Personalization Profile'**
  String get personalizationProfileTitle;

  /// No description provided for @personalizationConfidenceHighLabel.
  ///
  /// In en, this message translates to:
  /// **'HIGH'**
  String get personalizationConfidenceHighLabel;

  /// No description provided for @personalizationConfidenceMediumLabel.
  ///
  /// In en, this message translates to:
  /// **'MEDIUM'**
  String get personalizationConfidenceMediumLabel;

  /// No description provided for @personalizationConfidenceLowLabel.
  ///
  /// In en, this message translates to:
  /// **'LOW'**
  String get personalizationConfidenceLowLabel;

  /// No description provided for @personalizationProfileNoDataMessage.
  ///
  /// In en, this message translates to:
  /// **'Not enough data yet to identify a pattern.'**
  String get personalizationProfileNoDataMessage;

  /// No description provided for @orderStatusDraftLabel.
  ///
  /// In en, this message translates to:
  /// **'Draft'**
  String get orderStatusDraftLabel;

  /// No description provided for @orderStatusPendingConfirmationLabel.
  ///
  /// In en, this message translates to:
  /// **'Pending Confirmation'**
  String get orderStatusPendingConfirmationLabel;

  /// No description provided for @orderStatusConfirmedLabel.
  ///
  /// In en, this message translates to:
  /// **'Confirmed'**
  String get orderStatusConfirmedLabel;

  /// No description provided for @orderStatusPaymentPendingLabel.
  ///
  /// In en, this message translates to:
  /// **'Payment Pending'**
  String get orderStatusPaymentPendingLabel;

  /// No description provided for @orderStatusPaidLabel.
  ///
  /// In en, this message translates to:
  /// **'Paid'**
  String get orderStatusPaidLabel;

  /// No description provided for @orderStatusAcceptedByDealerLabel.
  ///
  /// In en, this message translates to:
  /// **'Accepted by Dealer'**
  String get orderStatusAcceptedByDealerLabel;

  /// No description provided for @orderStatusPreparingLabel.
  ///
  /// In en, this message translates to:
  /// **'Preparing'**
  String get orderStatusPreparingLabel;

  /// No description provided for @orderStatusReadyForDispatchLabel.
  ///
  /// In en, this message translates to:
  /// **'Ready for Dispatch'**
  String get orderStatusReadyForDispatchLabel;

  /// No description provided for @orderStatusDispatchedLabel.
  ///
  /// In en, this message translates to:
  /// **'Dispatched'**
  String get orderStatusDispatchedLabel;

  /// No description provided for @orderStatusOutForDeliveryLabel.
  ///
  /// In en, this message translates to:
  /// **'Out for Delivery'**
  String get orderStatusOutForDeliveryLabel;

  /// No description provided for @orderStatusDeliveredLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivered'**
  String get orderStatusDeliveredLabel;

  /// No description provided for @orderStatusCancelledLabel.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get orderStatusCancelledLabel;

  /// No description provided for @orderStatusRejectedLabel.
  ///
  /// In en, this message translates to:
  /// **'Rejected'**
  String get orderStatusRejectedLabel;

  /// No description provided for @orderStatusRefundPendingLabel.
  ///
  /// In en, this message translates to:
  /// **'Refund Pending'**
  String get orderStatusRefundPendingLabel;

  /// No description provided for @orderStatusRefundedLabel.
  ///
  /// In en, this message translates to:
  /// **'Refunded'**
  String get orderStatusRefundedLabel;

  /// No description provided for @orderStatusDisputedLabel.
  ///
  /// In en, this message translates to:
  /// **'Disputed'**
  String get orderStatusDisputedLabel;

  /// No description provided for @orderDisputeReasonWrongProductLabel.
  ///
  /// In en, this message translates to:
  /// **'Wrong product'**
  String get orderDisputeReasonWrongProductLabel;

  /// No description provided for @orderDisputeReasonMissingItemLabel.
  ///
  /// In en, this message translates to:
  /// **'Missing item'**
  String get orderDisputeReasonMissingItemLabel;

  /// No description provided for @orderDisputeReasonDamagedProductLabel.
  ///
  /// In en, this message translates to:
  /// **'Damaged product'**
  String get orderDisputeReasonDamagedProductLabel;

  /// No description provided for @orderDisputeReasonPaymentIssueLabel.
  ///
  /// In en, this message translates to:
  /// **'Payment issue'**
  String get orderDisputeReasonPaymentIssueLabel;

  /// No description provided for @orderDisputeReasonDeliveryIssueLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery issue'**
  String get orderDisputeReasonDeliveryIssueLabel;

  /// No description provided for @orderDisputeReasonUnexpectedChargeLabel.
  ///
  /// In en, this message translates to:
  /// **'Unexpected charge'**
  String get orderDisputeReasonUnexpectedChargeLabel;

  /// No description provided for @orderDisputeReasonProductAuthenticityConcernLabel.
  ///
  /// In en, this message translates to:
  /// **'Product authenticity concern'**
  String get orderDisputeReasonProductAuthenticityConcernLabel;

  /// No description provided for @orderDetailCartTitle.
  ///
  /// In en, this message translates to:
  /// **'Cart'**
  String get orderDetailCartTitle;

  /// No description provided for @orderDetailOrderTitle.
  ///
  /// In en, this message translates to:
  /// **'Order'**
  String get orderDetailOrderTitle;

  /// No description provided for @orderDetailOrderPlacedMessage.
  ///
  /// In en, this message translates to:
  /// **'Order placed.'**
  String get orderDetailOrderPlacedMessage;

  /// No description provided for @orderDetailCancelConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Cancel this order?'**
  String get orderDetailCancelConfirmTitle;

  /// No description provided for @orderDetailCancelConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'This cannot be undone.'**
  String get orderDetailCancelConfirmMessage;

  /// No description provided for @orderDetailNoButton.
  ///
  /// In en, this message translates to:
  /// **'No'**
  String get orderDetailNoButton;

  /// No description provided for @orderDetailYesCancelButton.
  ///
  /// In en, this message translates to:
  /// **'Yes, cancel'**
  String get orderDetailYesCancelButton;

  /// No description provided for @orderDetailDeliveryConfirmedMessage.
  ///
  /// In en, this message translates to:
  /// **'Delivery confirmed.'**
  String get orderDetailDeliveryConfirmedMessage;

  /// No description provided for @orderDetailFileDisputeTitle.
  ///
  /// In en, this message translates to:
  /// **'File a dispute'**
  String get orderDetailFileDisputeTitle;

  /// No description provided for @orderDetailDisputeReasonLabel.
  ///
  /// In en, this message translates to:
  /// **'Reason'**
  String get orderDetailDisputeReasonLabel;

  /// No description provided for @orderDetailDisputeDescriptionOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Description (optional)'**
  String get orderDetailDisputeDescriptionOptionalLabel;

  /// No description provided for @orderDetailSubmitDisputeButton.
  ///
  /// In en, this message translates to:
  /// **'Submit dispute'**
  String get orderDetailSubmitDisputeButton;

  /// No description provided for @orderDetailDisputeFiledMessage.
  ///
  /// In en, this message translates to:
  /// **'Dispute filed.'**
  String get orderDetailDisputeFiledMessage;

  /// No description provided for @orderDetailItemsLabel.
  ///
  /// In en, this message translates to:
  /// **'Items'**
  String get orderDetailItemsLabel;

  /// No description provided for @orderDetailNoItemsMessage.
  ///
  /// In en, this message translates to:
  /// **'No items.'**
  String get orderDetailNoItemsMessage;

  /// No description provided for @orderDetailSubtotalLabel.
  ///
  /// In en, this message translates to:
  /// **'Subtotal: ₹{amount}'**
  String orderDetailSubtotalLabel(String amount);

  /// No description provided for @orderDetailTaxLabel.
  ///
  /// In en, this message translates to:
  /// **'Tax: ₹{amount}'**
  String orderDetailTaxLabel(String amount);

  /// No description provided for @orderDetailDeliveryFeeLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery fee: ₹{amount}'**
  String orderDetailDeliveryFeeLabel(String amount);

  /// No description provided for @orderDetailTotalLabel.
  ///
  /// In en, this message translates to:
  /// **'Total: ₹{amount}'**
  String orderDetailTotalLabel(String amount);

  /// No description provided for @orderDetailRejectedLabel.
  ///
  /// In en, this message translates to:
  /// **'Rejected: {reason}'**
  String orderDetailRejectedLabel(String reason);

  /// No description provided for @orderDetailDeliveryLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery'**
  String get orderDetailDeliveryLabel;

  /// No description provided for @orderDetailEstimatedDeliveryLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated: {date}'**
  String orderDetailEstimatedDeliveryLabel(String date);

  /// No description provided for @orderDetailDisputeLabel.
  ///
  /// In en, this message translates to:
  /// **'Dispute'**
  String get orderDetailDisputeLabel;

  /// No description provided for @orderDetailItemQuantityLabel.
  ///
  /// In en, this message translates to:
  /// **'Qty: {quantity}'**
  String orderDetailItemQuantityLabel(String quantity);

  /// No description provided for @orderDetailCheckoutButton.
  ///
  /// In en, this message translates to:
  /// **'Checkout'**
  String get orderDetailCheckoutButton;

  /// No description provided for @orderDetailPayButton.
  ///
  /// In en, this message translates to:
  /// **'Pay'**
  String get orderDetailPayButton;

  /// No description provided for @orderDetailSimulatePaymentButton.
  ///
  /// In en, this message translates to:
  /// **'Simulate payment success (sandbox)'**
  String get orderDetailSimulatePaymentButton;

  /// No description provided for @orderDetailCancelOrderButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel order'**
  String get orderDetailCancelOrderButton;

  /// No description provided for @orderDetailConfirmDeliveryButton.
  ///
  /// In en, this message translates to:
  /// **'Confirm delivery received'**
  String get orderDetailConfirmDeliveryButton;

  /// No description provided for @orderDetailFileDisputeButton.
  ///
  /// In en, this message translates to:
  /// **'File a dispute'**
  String get orderDetailFileDisputeButton;

  /// No description provided for @orderListTitle.
  ///
  /// In en, this message translates to:
  /// **'My Orders'**
  String get orderListTitle;

  /// No description provided for @orderListNoOrdersYetMessage.
  ///
  /// In en, this message translates to:
  /// **'No orders yet.'**
  String get orderListNoOrdersYetMessage;

  /// No description provided for @productCategorySeedLabel.
  ///
  /// In en, this message translates to:
  /// **'Seed'**
  String get productCategorySeedLabel;

  /// No description provided for @productCategoryFertilizerLabel.
  ///
  /// In en, this message translates to:
  /// **'Fertilizer'**
  String get productCategoryFertilizerLabel;

  /// No description provided for @productCategoryBioInputLabel.
  ///
  /// In en, this message translates to:
  /// **'Bio Input'**
  String get productCategoryBioInputLabel;

  /// No description provided for @productCategoryPestControlLabel.
  ///
  /// In en, this message translates to:
  /// **'Pest Control'**
  String get productCategoryPestControlLabel;

  /// No description provided for @productCategoryCropProtectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Crop Protection'**
  String get productCategoryCropProtectionLabel;

  /// No description provided for @productCategoryEquipmentLabel.
  ///
  /// In en, this message translates to:
  /// **'Equipment'**
  String get productCategoryEquipmentLabel;

  /// No description provided for @productCategoryOtherLabel.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get productCategoryOtherLabel;

  /// No description provided for @productListTitle.
  ///
  /// In en, this message translates to:
  /// **'Buy Inputs'**
  String get productListTitle;

  /// No description provided for @productListSearchLabel.
  ///
  /// In en, this message translates to:
  /// **'Search products'**
  String get productListSearchLabel;

  /// No description provided for @productListAllCategoryLabel.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get productListAllCategoryLabel;

  /// No description provided for @productListNoProductsFoundMessage.
  ///
  /// In en, this message translates to:
  /// **'No products found.'**
  String get productListNoProductsFoundMessage;

  /// No description provided for @productDetailDefaultTitle.
  ///
  /// In en, this message translates to:
  /// **'Product'**
  String get productDetailDefaultTitle;

  /// No description provided for @productDetailScamShieldTitle.
  ///
  /// In en, this message translates to:
  /// **'Scam Shield'**
  String get productDetailScamShieldTitle;

  /// No description provided for @productDetailOkButton.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get productDetailOkButton;

  /// No description provided for @productDetailQuantityLabel.
  ///
  /// In en, this message translates to:
  /// **'Quantity'**
  String get productDetailQuantityLabel;

  /// No description provided for @productDetailInStockLabel.
  ///
  /// In en, this message translates to:
  /// **'{quantity} in stock'**
  String productDetailInStockLabel(String quantity);

  /// No description provided for @productDetailAddToCartButton.
  ///
  /// In en, this message translates to:
  /// **'Add to Cart'**
  String get productDetailAddToCartButton;

  /// No description provided for @productDetailByManufacturerLabel.
  ///
  /// In en, this message translates to:
  /// **'By {manufacturer}'**
  String productDetailByManufacturerLabel(String manufacturer);

  /// No description provided for @productDetailUsageLabel.
  ///
  /// In en, this message translates to:
  /// **'Usage'**
  String get productDetailUsageLabel;

  /// No description provided for @productDetailReferencePriceLabel.
  ///
  /// In en, this message translates to:
  /// **'Reference price: {price}'**
  String productDetailReferencePriceLabel(String price);

  /// No description provided for @productDetailAvailableFromDealersLabel.
  ///
  /// In en, this message translates to:
  /// **'Available from dealers'**
  String get productDetailAvailableFromDealersLabel;

  /// No description provided for @productDetailNoDealersAvailableMessage.
  ///
  /// In en, this message translates to:
  /// **'No dealer currently has this product available.'**
  String get productDetailNoDealersAvailableMessage;

  /// No description provided for @productDetailOfferSummaryLabel.
  ///
  /// In en, this message translates to:
  /// **'{pricePerUnit} per {unit} • {stockQuantity} in stock'**
  String productDetailOfferSummaryLabel(
      String pricePerUnit, String unit, String stockQuantity);

  /// No description provided for @productDetailCurrentlyUnavailableLabel.
  ///
  /// In en, this message translates to:
  /// **'Currently unavailable'**
  String get productDetailCurrentlyUnavailableLabel;

  /// No description provided for @productDetailCheckPriceFairnessButton.
  ///
  /// In en, this message translates to:
  /// **'Check price fairness'**
  String get productDetailCheckPriceFairnessButton;

  /// No description provided for @addCropAddedMessage.
  ///
  /// In en, this message translates to:
  /// **'Crop added.'**
  String get addCropAddedMessage;

  /// No description provided for @addCropTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Crop'**
  String get addCropTitle;

  /// No description provided for @addCropSelectCropLabel.
  ///
  /// In en, this message translates to:
  /// **'Select a crop'**
  String get addCropSelectCropLabel;

  /// No description provided for @addCropSowingDateLabel.
  ///
  /// In en, this message translates to:
  /// **'Sowing date'**
  String get addCropSowingDateLabel;

  /// No description provided for @addCropExpectedHarvestDateOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Expected harvest date (optional)'**
  String get addCropExpectedHarvestDateOptionalLabel;

  /// No description provided for @addCropSeasonOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Season (optional)'**
  String get addCropSeasonOptionalLabel;

  /// No description provided for @addCropVarietyOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Variety (optional)'**
  String get addCropVarietyOptionalLabel;

  /// No description provided for @addCropSubmitButton.
  ///
  /// In en, this message translates to:
  /// **'Add crop'**
  String get addCropSubmitButton;

  /// No description provided for @addCropSearchCropLabel.
  ///
  /// In en, this message translates to:
  /// **'Search crop'**
  String get addCropSearchCropLabel;

  /// No description provided for @addEditFarmLocationPermissionRequiredMessage.
  ///
  /// In en, this message translates to:
  /// **'Location permission is required to use current location.'**
  String get addEditFarmLocationPermissionRequiredMessage;

  /// No description provided for @addEditFarmEnableLocationMessage.
  ///
  /// In en, this message translates to:
  /// **'Please turn on device location and try again.'**
  String get addEditFarmEnableLocationMessage;

  /// No description provided for @addEditFarmLocationCapturedNoAreaMessage.
  ///
  /// In en, this message translates to:
  /// **'Location captured. Could not look up the area name - please select it below.'**
  String get addEditFarmLocationCapturedNoAreaMessage;

  /// No description provided for @addEditFarmLocationCapturedSelectManuallyMessage.
  ///
  /// In en, this message translates to:
  /// **'Location captured. Please select your State/District/Mandal/Village below.'**
  String get addEditFarmLocationCapturedSelectManuallyMessage;

  /// No description provided for @addEditFarmDetectedStateMessage.
  ///
  /// In en, this message translates to:
  /// **'Detected State: {stateName}. Please select District/Mandal/Village below.'**
  String addEditFarmDetectedStateMessage(String stateName);

  /// No description provided for @addEditFarmDetectedStateDistrictMessage.
  ///
  /// In en, this message translates to:
  /// **'Detected {stateName}, {districtName}. Please select Mandal/Village below.'**
  String addEditFarmDetectedStateDistrictMessage(
      String stateName, String districtName);

  /// No description provided for @addEditFarmDetectedFullLocationMessage.
  ///
  /// In en, this message translates to:
  /// **'Detected: {stateName}, {districtName}, {mandalName}. Please confirm below.'**
  String addEditFarmDetectedFullLocationMessage(
      String stateName, String districtName, String mandalName);

  /// No description provided for @addEditFarmDetectedFullLocationWithVillageMessage.
  ///
  /// In en, this message translates to:
  /// **'Detected: {stateName}, {districtName}, {mandalName}, {villageName}. Please confirm below.'**
  String addEditFarmDetectedFullLocationWithVillageMessage(String stateName,
      String districtName, String mandalName, String villageName);

  /// No description provided for @addEditFarmNoDataAvailableLabel.
  ///
  /// In en, this message translates to:
  /// **'No data available yet'**
  String get addEditFarmNoDataAvailableLabel;

  /// No description provided for @addEditFarmEditTitle.
  ///
  /// In en, this message translates to:
  /// **'Edit Farm'**
  String get addEditFarmEditTitle;

  /// No description provided for @addEditFarmAddTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Farm'**
  String get addEditFarmAddTitle;

  /// No description provided for @addEditFarmNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Farm name'**
  String get addEditFarmNameLabel;

  /// No description provided for @addEditFarmNameRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter a farm name.'**
  String get addEditFarmNameRequiredError;

  /// No description provided for @addEditFarmAreaLabel.
  ///
  /// In en, this message translates to:
  /// **'Area'**
  String get addEditFarmAreaLabel;

  /// No description provided for @addEditFarmAreaRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter the farm area.'**
  String get addEditFarmAreaRequiredError;

  /// No description provided for @addEditFarmAreaInvalidError.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid area.'**
  String get addEditFarmAreaInvalidError;

  /// No description provided for @addEditFarmUnitLabel.
  ///
  /// In en, this message translates to:
  /// **'Unit'**
  String get addEditFarmUnitLabel;

  /// No description provided for @addEditFarmLocationSectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Location (optional)'**
  String get addEditFarmLocationSectionLabel;

  /// No description provided for @addEditFarmDetectingLocationLabel.
  ///
  /// In en, this message translates to:
  /// **'Detecting location...'**
  String get addEditFarmDetectingLocationLabel;

  /// No description provided for @addEditFarmUseCurrentLocationButton.
  ///
  /// In en, this message translates to:
  /// **'Use current location'**
  String get addEditFarmUseCurrentLocationButton;

  /// No description provided for @addEditFarmLatitudeLabel.
  ///
  /// In en, this message translates to:
  /// **'Latitude'**
  String get addEditFarmLatitudeLabel;

  /// No description provided for @addEditFarmLongitudeLabel.
  ///
  /// In en, this message translates to:
  /// **'Longitude'**
  String get addEditFarmLongitudeLabel;

  /// No description provided for @addEditFarmStateLabel.
  ///
  /// In en, this message translates to:
  /// **'State'**
  String get addEditFarmStateLabel;

  /// No description provided for @addEditFarmDistrictLabel.
  ///
  /// In en, this message translates to:
  /// **'District'**
  String get addEditFarmDistrictLabel;

  /// No description provided for @addEditFarmMandalLabel.
  ///
  /// In en, this message translates to:
  /// **'Mandal / Taluk'**
  String get addEditFarmMandalLabel;

  /// No description provided for @addEditFarmVillageLabel.
  ///
  /// In en, this message translates to:
  /// **'Village'**
  String get addEditFarmVillageLabel;

  /// No description provided for @addEditFarmSaveChangesButton.
  ///
  /// In en, this message translates to:
  /// **'Save changes'**
  String get addEditFarmSaveChangesButton;

  /// No description provided for @addEditFarmAddFarmButton.
  ///
  /// In en, this message translates to:
  /// **'Add farm'**
  String get addEditFarmAddFarmButton;

  /// No description provided for @addEditFarmUpdatedMessage.
  ///
  /// In en, this message translates to:
  /// **'Farm updated.'**
  String get addEditFarmUpdatedMessage;

  /// No description provided for @addEditFarmAddedMessage.
  ///
  /// In en, this message translates to:
  /// **'Farm added.'**
  String get addEditFarmAddedMessage;

  /// No description provided for @addEditPlotUpdatedMessage.
  ///
  /// In en, this message translates to:
  /// **'Plot updated.'**
  String get addEditPlotUpdatedMessage;

  /// No description provided for @addEditPlotAddedMessage.
  ///
  /// In en, this message translates to:
  /// **'Plot added.'**
  String get addEditPlotAddedMessage;

  /// No description provided for @addEditPlotEditTitle.
  ///
  /// In en, this message translates to:
  /// **'Edit Plot'**
  String get addEditPlotEditTitle;

  /// No description provided for @addEditPlotAddTitle.
  ///
  /// In en, this message translates to:
  /// **'Add Plot'**
  String get addEditPlotAddTitle;

  /// No description provided for @addEditPlotNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Plot name'**
  String get addEditPlotNameLabel;

  /// No description provided for @addEditPlotNameRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter a plot name.'**
  String get addEditPlotNameRequiredError;

  /// No description provided for @addEditPlotAreaLabel.
  ///
  /// In en, this message translates to:
  /// **'Area'**
  String get addEditPlotAreaLabel;

  /// No description provided for @addEditPlotAreaInvalidError.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid area.'**
  String get addEditPlotAreaInvalidError;

  /// No description provided for @addEditPlotUnitLabel.
  ///
  /// In en, this message translates to:
  /// **'Unit'**
  String get addEditPlotUnitLabel;

  /// No description provided for @addEditPlotIrrigationOptionalLabel.
  ///
  /// In en, this message translates to:
  /// **'Irrigation (optional)'**
  String get addEditPlotIrrigationOptionalLabel;

  /// No description provided for @addEditPlotSaveChangesButton.
  ///
  /// In en, this message translates to:
  /// **'Save changes'**
  String get addEditPlotSaveChangesButton;

  /// No description provided for @addEditPlotAddButton.
  ///
  /// In en, this message translates to:
  /// **'Add plot'**
  String get addEditPlotAddButton;

  /// No description provided for @cropDetailsMarkedHarvestedMessage.
  ///
  /// In en, this message translates to:
  /// **'Crop marked as harvested.'**
  String get cropDetailsMarkedHarvestedMessage;

  /// No description provided for @cropDetailsCancelConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Cancel this crop?'**
  String get cropDetailsCancelConfirmTitle;

  /// No description provided for @cropDetailsCancelConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'This marks the crop cycle as cancelled. This cannot be undone.'**
  String get cropDetailsCancelConfirmMessage;

  /// No description provided for @cropDetailsCancelConfirmNoButton.
  ///
  /// In en, this message translates to:
  /// **'No'**
  String get cropDetailsCancelConfirmNoButton;

  /// No description provided for @cropDetailsCancelConfirmYesButton.
  ///
  /// In en, this message translates to:
  /// **'Yes, cancel'**
  String get cropDetailsCancelConfirmYesButton;

  /// No description provided for @cropDetailsFallbackTitle.
  ///
  /// In en, this message translates to:
  /// **'Crop'**
  String get cropDetailsFallbackTitle;

  /// No description provided for @cropDetailsInsightsTooltip.
  ///
  /// In en, this message translates to:
  /// **'Crop Insights'**
  String get cropDetailsInsightsTooltip;

  /// No description provided for @cropDetailsPerformanceScoreMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Performance Score'**
  String get cropDetailsPerformanceScoreMenuItem;

  /// No description provided for @cropDetailsCompareCropsMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Compare Crops'**
  String get cropDetailsCompareCropsMenuItem;

  /// No description provided for @cropDetailsInputSpendBreakdownMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Input Spend Breakdown'**
  String get cropDetailsInputSpendBreakdownMenuItem;

  /// No description provided for @cropDetailsIrrigationIntelligenceMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Irrigation Intelligence'**
  String get cropDetailsIrrigationIntelligenceMenuItem;

  /// No description provided for @cropDetailsPersonalizationProfileMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Your Personalization Profile'**
  String get cropDetailsPersonalizationProfileMenuItem;

  /// No description provided for @cropDetailsLearningSummaryMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Learning Summary'**
  String get cropDetailsLearningSummaryMenuItem;

  /// No description provided for @cropDetailsGiveFeedbackMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Give Feedback'**
  String get cropDetailsGiveFeedbackMenuItem;

  /// No description provided for @cropDetailsWeatherActionTooltip.
  ///
  /// In en, this message translates to:
  /// **'Weather Action Advisor'**
  String get cropDetailsWeatherActionTooltip;

  /// No description provided for @cropDetailsAiAssistantTooltip.
  ///
  /// In en, this message translates to:
  /// **'AI Crop Assistant'**
  String get cropDetailsAiAssistantTooltip;

  /// No description provided for @cropDetailsHealthTimelineTooltip.
  ///
  /// In en, this message translates to:
  /// **'Health Timeline'**
  String get cropDetailsHealthTimelineTooltip;

  /// No description provided for @cropDetailsTreatmentsTooltip.
  ///
  /// In en, this message translates to:
  /// **'Treatments'**
  String get cropDetailsTreatmentsTooltip;

  /// No description provided for @cropDetailsCropRiskTooltip.
  ///
  /// In en, this message translates to:
  /// **'Crop Risk'**
  String get cropDetailsCropRiskTooltip;

  /// No description provided for @cropDetailsProfitForecastTooltip.
  ///
  /// In en, this message translates to:
  /// **'Profit Forecast'**
  String get cropDetailsProfitForecastTooltip;

  /// No description provided for @cropDetailsFinancialSummaryTooltip.
  ///
  /// In en, this message translates to:
  /// **'Financial Summary'**
  String get cropDetailsFinancialSummaryTooltip;

  /// No description provided for @cropDetailsFinancialLedgerTooltip.
  ///
  /// In en, this message translates to:
  /// **'Financial Ledger'**
  String get cropDetailsFinancialLedgerTooltip;

  /// No description provided for @cropDetailsTasksTooltip.
  ///
  /// In en, this message translates to:
  /// **'Tasks'**
  String get cropDetailsTasksTooltip;

  /// No description provided for @cropDetailsCheckCropTooltip.
  ///
  /// In en, this message translates to:
  /// **'Check Crop'**
  String get cropDetailsCheckCropTooltip;

  /// No description provided for @cropDetailsHarvestTooltip.
  ///
  /// In en, this message translates to:
  /// **'Harvest'**
  String get cropDetailsHarvestTooltip;

  /// No description provided for @cropDetailsSowingDateLabel.
  ///
  /// In en, this message translates to:
  /// **'Sowing date'**
  String get cropDetailsSowingDateLabel;

  /// No description provided for @cropDetailsExpectedHarvestLabel.
  ///
  /// In en, this message translates to:
  /// **'Expected harvest'**
  String get cropDetailsExpectedHarvestLabel;

  /// No description provided for @cropDetailsHarvestedOnLabel.
  ///
  /// In en, this message translates to:
  /// **'Harvested on'**
  String get cropDetailsHarvestedOnLabel;

  /// No description provided for @cropDetailsSeasonLabel.
  ///
  /// In en, this message translates to:
  /// **'Season'**
  String get cropDetailsSeasonLabel;

  /// No description provided for @cropDetailsVarietyLabel.
  ///
  /// In en, this message translates to:
  /// **'Variety'**
  String get cropDetailsVarietyLabel;

  /// No description provided for @cropDetailsSeedVarietyLabel.
  ///
  /// In en, this message translates to:
  /// **'Seed variety'**
  String get cropDetailsSeedVarietyLabel;

  /// No description provided for @cropDetailsMarkAsHarvestedButton.
  ///
  /// In en, this message translates to:
  /// **'Mark as harvested'**
  String get cropDetailsMarkAsHarvestedButton;

  /// No description provided for @cropDetailsAdvanceToButton.
  ///
  /// In en, this message translates to:
  /// **'Advance to {status}'**
  String cropDetailsAdvanceToButton(String status);

  /// No description provided for @cropDetailsCancelCropButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel this crop'**
  String get cropDetailsCancelCropButton;

  /// No description provided for @farmDetailsRemoveConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Remove this farm?'**
  String get farmDetailsRemoveConfirmTitle;

  /// No description provided for @farmDetailsRemoveConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'This farm will be removed from your active list. Its history is kept.'**
  String get farmDetailsRemoveConfirmMessage;

  /// No description provided for @farmDetailsRemoveConfirmCancelButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get farmDetailsRemoveConfirmCancelButton;

  /// No description provided for @farmDetailsRemoveConfirmRemoveButton.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get farmDetailsRemoveConfirmRemoveButton;

  /// No description provided for @farmDetailsFallbackTitle.
  ///
  /// In en, this message translates to:
  /// **'Farm'**
  String get farmDetailsFallbackTitle;

  /// No description provided for @farmDetailsWeatherTooltip.
  ///
  /// In en, this message translates to:
  /// **'Weather'**
  String get farmDetailsWeatherTooltip;

  /// No description provided for @farmDetailsEditFarmMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Edit farm'**
  String get farmDetailsEditFarmMenuItem;

  /// No description provided for @farmDetailsRemoveFarmMenuItem.
  ///
  /// In en, this message translates to:
  /// **'Remove farm'**
  String get farmDetailsRemoveFarmMenuItem;

  /// No description provided for @farmDetailsAddPlotButton.
  ///
  /// In en, this message translates to:
  /// **'Add Plot'**
  String get farmDetailsAddPlotButton;

  /// No description provided for @farmDetailsTotalAreaLabel.
  ///
  /// In en, this message translates to:
  /// **'Total area'**
  String get farmDetailsTotalAreaLabel;

  /// No description provided for @farmDetailsNotesLabel.
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get farmDetailsNotesLabel;

  /// No description provided for @farmDetailsPlotsSectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Plots'**
  String get farmDetailsPlotsSectionLabel;

  /// No description provided for @farmDetailsNoPlotsYetMessage.
  ///
  /// In en, this message translates to:
  /// **'No plots yet. Tap \"Add Plot\" to create one.'**
  String get farmDetailsNoPlotsYetMessage;

  /// No description provided for @myFarmsTitle.
  ///
  /// In en, this message translates to:
  /// **'My Farms'**
  String get myFarmsTitle;

  /// No description provided for @myFarmsAddFarmButton.
  ///
  /// In en, this message translates to:
  /// **'Add Farm'**
  String get myFarmsAddFarmButton;

  /// No description provided for @myFarmsEmptyStateMessage.
  ///
  /// In en, this message translates to:
  /// **'No farms yet. Tap \"Add Farm\" to get started.'**
  String get myFarmsEmptyStateMessage;

  /// No description provided for @plotDetailsFallbackTitle.
  ///
  /// In en, this message translates to:
  /// **'Plot'**
  String get plotDetailsFallbackTitle;

  /// No description provided for @plotDetailsAddCropButton.
  ///
  /// In en, this message translates to:
  /// **'Add Crop'**
  String get plotDetailsAddCropButton;

  /// No description provided for @plotDetailsAreaLabel.
  ///
  /// In en, this message translates to:
  /// **'Area'**
  String get plotDetailsAreaLabel;

  /// No description provided for @plotDetailsSoilLabel.
  ///
  /// In en, this message translates to:
  /// **'Soil'**
  String get plotDetailsSoilLabel;

  /// No description provided for @plotDetailsIrrigationLabel.
  ///
  /// In en, this message translates to:
  /// **'Irrigation'**
  String get plotDetailsIrrigationLabel;

  /// No description provided for @plotDetailsCropsSectionLabel.
  ///
  /// In en, this message translates to:
  /// **'Crops'**
  String get plotDetailsCropsSectionLabel;

  /// No description provided for @plotDetailsNoCropsYetMessage.
  ///
  /// In en, this message translates to:
  /// **'No crops yet. Tap \"Add Crop\" to start one.'**
  String get plotDetailsNoCropsYetMessage;

  /// No description provided for @plotDetailsCropStatusSownSubtitle.
  ///
  /// In en, this message translates to:
  /// **'{status} · sown {sowingDate}'**
  String plotDetailsCropStatusSownSubtitle(String status, String sowingDate);

  /// No description provided for @cropComparisonTitle.
  ///
  /// In en, this message translates to:
  /// **'Compare Crops'**
  String get cropComparisonTitle;

  /// No description provided for @otherCropCycleIdLabel.
  ///
  /// In en, this message translates to:
  /// **'Other crop cycle ID'**
  String get otherCropCycleIdLabel;

  /// No description provided for @compareButton.
  ///
  /// In en, this message translates to:
  /// **'Compare'**
  String get compareButton;

  /// No description provided for @cropComparisonEmptyMessage.
  ///
  /// In en, this message translates to:
  /// **'Enter another crop cycle ID to compare.'**
  String get cropComparisonEmptyMessage;

  /// No description provided for @cropComparisonMetricRow.
  ///
  /// In en, this message translates to:
  /// **'This crop: {valueA}    Other crop: {valueB}'**
  String cropComparisonMetricRow(String valueA, String valueB);

  /// No description provided for @cropComparisonVerdictAHigher.
  ///
  /// In en, this message translates to:
  /// **'This crop — higher (based on available data)'**
  String get cropComparisonVerdictAHigher;

  /// No description provided for @cropComparisonVerdictBHigher.
  ///
  /// In en, this message translates to:
  /// **'Other crop — higher (based on available data)'**
  String get cropComparisonVerdictBHigher;

  /// No description provided for @cropComparisonVerdictEqual.
  ///
  /// In en, this message translates to:
  /// **'Equal'**
  String get cropComparisonVerdictEqual;

  /// No description provided for @cropComparisonVerdictNotComparable.
  ///
  /// In en, this message translates to:
  /// **'Not directly comparable'**
  String get cropComparisonVerdictNotComparable;

  /// No description provided for @insufficientDataLabel.
  ///
  /// In en, this message translates to:
  /// **'Insufficient data'**
  String get insufficientDataLabel;

  /// No description provided for @inputRoiTitle.
  ///
  /// In en, this message translates to:
  /// **'Input Spend Breakdown'**
  String get inputRoiTitle;

  /// No description provided for @inputRoiTotalActualCostLabel.
  ///
  /// In en, this message translates to:
  /// **'Total Actual Cost: {amount}'**
  String inputRoiTotalActualCostLabel(String amount);

  /// No description provided for @inputRoiNoExpensesMessage.
  ///
  /// In en, this message translates to:
  /// **'No expenses recorded yet for this crop.'**
  String get inputRoiNoExpensesMessage;

  /// No description provided for @inputRoiActualLabel.
  ///
  /// In en, this message translates to:
  /// **'Actual: {amount}'**
  String inputRoiActualLabel(String amount);

  /// No description provided for @inputRoiEstimatedVarianceLabel.
  ///
  /// In en, this message translates to:
  /// **'Estimated: {estimated}  ·  Variance: {variance}'**
  String inputRoiEstimatedVarianceLabel(String estimated, String variance);

  /// No description provided for @irrigationIntelligenceTitle.
  ///
  /// In en, this message translates to:
  /// **'Irrigation Intelligence'**
  String get irrigationIntelligenceTitle;

  /// No description provided for @irrigationRecommendationIrrigateNow.
  ///
  /// In en, this message translates to:
  /// **'IRRIGATE NOW'**
  String get irrigationRecommendationIrrigateNow;

  /// No description provided for @irrigationRecommendationDelay.
  ///
  /// In en, this message translates to:
  /// **'DELAY'**
  String get irrigationRecommendationDelay;

  /// No description provided for @irrigationRecommendationMonitor.
  ///
  /// In en, this message translates to:
  /// **'MONITOR'**
  String get irrigationRecommendationMonitor;

  /// No description provided for @irrigationRecommendationNoAction.
  ///
  /// In en, this message translates to:
  /// **'NO ACTION NEEDED'**
  String get irrigationRecommendationNoAction;

  /// No description provided for @irrigationRecommendationUnknown.
  ///
  /// In en, this message translates to:
  /// **'UNKNOWN'**
  String get irrigationRecommendationUnknown;

  /// No description provided for @irrigationWeatherSignalLabel.
  ///
  /// In en, this message translates to:
  /// **'Weather signal: {status}'**
  String irrigationWeatherSignalLabel(String status);

  /// No description provided for @irrigationPendingTaskMessage.
  ///
  /// In en, this message translates to:
  /// **'A pending irrigation task exists for this crop.'**
  String get irrigationPendingTaskMessage;

  /// No description provided for @irrigationSoilMoistureDisclosure.
  ///
  /// In en, this message translates to:
  /// **'Soil moisture data is unavailable. This recommendation is based on weather forecast and task status only.'**
  String get irrigationSoilMoistureDisclosure;

  /// No description provided for @cropPerformanceTitle.
  ///
  /// In en, this message translates to:
  /// **'Crop Performance'**
  String get cropPerformanceTitle;

  /// No description provided for @performanceOverallScoreLabel.
  ///
  /// In en, this message translates to:
  /// **'Overall Score'**
  String get performanceOverallScoreLabel;

  /// No description provided for @performanceDataCompletenessLabel.
  ///
  /// In en, this message translates to:
  /// **'Data completeness: {percent}%'**
  String performanceDataCompletenessLabel(String percent);

  /// No description provided for @tryAgainButton.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgainButton;

  /// No description provided for @cancelButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancelButton;

  /// No description provided for @doneButton.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get doneButton;

  /// No description provided for @removeButton.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get removeButton;

  /// No description provided for @homeFarmsSummaryLabel.
  ///
  /// In en, this message translates to:
  /// **'Farms'**
  String get homeFarmsSummaryLabel;

  /// No description provided for @homeActiveCropsSummaryLabel.
  ///
  /// In en, this message translates to:
  /// **'Active crops'**
  String get homeActiveCropsSummaryLabel;

  /// No description provided for @homeBuyInputsButton.
  ///
  /// In en, this message translates to:
  /// **'Buy Inputs'**
  String get homeBuyInputsButton;

  /// No description provided for @homeGoToMyFarmsButton.
  ///
  /// In en, this message translates to:
  /// **'Go to My Farms'**
  String get homeGoToMyFarmsButton;

  /// No description provided for @validatorPhoneRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter your phone number.'**
  String get validatorPhoneRequiredError;

  /// No description provided for @validatorPhoneInvalidError.
  ///
  /// In en, this message translates to:
  /// **'Please enter a valid phone number (7-15 digits).'**
  String get validatorPhoneInvalidError;

  /// No description provided for @validatorPasswordTooShortError.
  ///
  /// In en, this message translates to:
  /// **'Password must be at least 8 characters.'**
  String get validatorPasswordTooShortError;

  /// No description provided for @validatorPasswordNeedsLetterAndNumberError.
  ///
  /// In en, this message translates to:
  /// **'Password must contain a letter and a number.'**
  String get validatorPasswordNeedsLetterAndNumberError;

  /// No description provided for @validatorPasswordNeedsUppercaseError.
  ///
  /// In en, this message translates to:
  /// **'Password must contain an uppercase letter.'**
  String get validatorPasswordNeedsUppercaseError;

  /// No description provided for @validatorPasswordNeedsSpecialCharError.
  ///
  /// In en, this message translates to:
  /// **'Password must contain a special character.'**
  String get validatorPasswordNeedsSpecialCharError;

  /// No description provided for @validatorNameRequiredError.
  ///
  /// In en, this message translates to:
  /// **'Please enter your name.'**
  String get validatorNameRequiredError;

  /// No description provided for @errorInvalidCredentials.
  ///
  /// In en, this message translates to:
  /// **'That phone number or password isn\'t right. Please try again.'**
  String get errorInvalidCredentials;

  /// No description provided for @errorAccountDisabled.
  ///
  /// In en, this message translates to:
  /// **'This account is not active. Please contact support.'**
  String get errorAccountDisabled;

  /// No description provided for @errorDuplicateAccount.
  ///
  /// In en, this message translates to:
  /// **'An account with this phone number already exists. Try logging in instead.'**
  String get errorDuplicateAccount;

  /// No description provided for @errorIncorrectCurrentPassword.
  ///
  /// In en, this message translates to:
  /// **'Your current password is incorrect.'**
  String get errorIncorrectCurrentPassword;

  /// No description provided for @errorValidation.
  ///
  /// In en, this message translates to:
  /// **'Please check the information you entered and try again.'**
  String get errorValidation;

  /// No description provided for @errorSessionExpired.
  ///
  /// In en, this message translates to:
  /// **'Your session has ended. Please log in again.'**
  String get errorSessionExpired;

  /// No description provided for @errorRateLimited.
  ///
  /// In en, this message translates to:
  /// **'Too many attempts. Please wait a few minutes and try again.'**
  String get errorRateLimited;

  /// No description provided for @errorUnauthorized.
  ///
  /// In en, this message translates to:
  /// **'You need to log in again to continue.'**
  String get errorUnauthorized;

  /// No description provided for @errorGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errorGeneric;

  /// No description provided for @errorGenericConnection.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please check your connection and try again.'**
  String get errorGenericConnection;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>[
        'en',
        'hi',
        'kn',
        'ml',
        'mr',
        'ta',
        'te'
      ].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'kn':
      return AppLocalizationsKn();
    case 'ml':
      return AppLocalizationsMl();
    case 'mr':
      return AppLocalizationsMr();
    case 'ta':
      return AppLocalizationsTa();
    case 'te':
      return AppLocalizationsTe();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
