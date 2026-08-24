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
