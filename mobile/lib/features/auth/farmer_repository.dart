import '../../core/api_client.dart';

class FarmerProfile {
  final String userId;
  final String phoneNumber;
  final String fullName;
  final String preferredLanguageCode;
  final String preferredVoiceLanguageCode;
  final String status;

  FarmerProfile({
    required this.userId,
    required this.phoneNumber,
    required this.fullName,
    required this.preferredLanguageCode,
    required this.preferredVoiceLanguageCode,
    required this.status,
  });

  factory FarmerProfile.fromJson(Map<String, dynamic> json) => FarmerProfile(
        userId: json['user_id'] as String,
        phoneNumber: json['phone_number'] as String,
        fullName: json['full_name'] as String,
        preferredLanguageCode: json['preferred_language_code'] as String,
        preferredVoiceLanguageCode: json['preferred_voice_language_code'] as String,
        status: json['status'] as String,
      );
}

class FarmerRepository {
  final ApiClient _apiClient;
  FarmerRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<FarmerProfile> getMyProfile() async {
    final response = await _apiClient.get('/farmers/me');
    return FarmerProfile.fromJson(response);
  }

  Future<FarmerProfile> updateMyProfile({String? fullName, String? preferredLanguageCode}) async {
    final response = await _apiClient.put('/farmers/me', body: {
      if (fullName != null) 'full_name': fullName,
      if (preferredLanguageCode != null) 'preferred_language_code': preferredLanguageCode,
    });
    return FarmerProfile.fromJson(response);
  }

  Future<FarmerDashboard> getDashboard() async {
    final response = await _apiClient.get('/farmers/me/dashboard');
    return FarmerDashboard.fromJson(response);
  }
}

class FarmerDashboard {
  final int farmCount;
  final int plotCount;
  final int activeCropCycleCount;

  FarmerDashboard({required this.farmCount, required this.plotCount, required this.activeCropCycleCount});

  factory FarmerDashboard.fromJson(Map<String, dynamic> json) => FarmerDashboard(
        farmCount: json['farm_count'] as int,
        plotCount: json['plot_count'] as int,
        activeCropCycleCount: json['active_crop_cycle_count'] as int,
      );
}
