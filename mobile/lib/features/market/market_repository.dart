import '../../core/api_client.dart';
import 'market_models.dart';

/// Farmer-side surface of backend/app/api/v1/marketplace.py only - the
/// buyer-role endpoints (browse listings, make an initial offer) are
/// deliberately not called from anywhere in this app, matching the same
/// farmer-only-persona boundary already established for Expert/Field
/// Agent (no buyer registration/login/browsing UI exists).
class MarketRepository {
  final ApiClient _apiClient;
  MarketRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  Future<List<Offer>> listOffersForListing(String listingId) async {
    final response = await _apiClient.get('/marketplace/listings/$listingId/offers');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Offer.fromJson).toList();
  }

  Future<CounterOffer> counterOffer({
    required String offerId,
    required String pricePerUnit,
    required String quantity,
    String? message,
  }) async {
    final response = await _apiClient.post('/marketplace/offers/$offerId/counter', body: {
      'price_per_unit': pricePerUnit,
      'quantity': quantity,
      if (message != null) 'message': message,
    });
    return CounterOffer.fromJson(response);
  }

  Future<SaleOrder> acceptOffer(String offerId) async {
    final response = await _apiClient.post('/marketplace/offers/$offerId/accept');
    return SaleOrder.fromJson(response);
  }

  Future<Offer> rejectOffer(String offerId) async {
    final response = await _apiClient.post('/marketplace/offers/$offerId/reject');
    return Offer.fromJson(response);
  }

  Future<List<SaleOrder>> listMySales({int limit = 100, int offset = 0}) async {
    final response = await _apiClient.get('/marketplace/sales?limit=$limit&offset=$offset');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(SaleOrder.fromJson).toList();
  }

  Future<SaleOrder> getSale(String saleId) async {
    final response = await _apiClient.get('/marketplace/sales/$saleId');
    return SaleOrder.fromJson(response);
  }

  Future<SaleOrder> acceptSale(String saleId) async {
    final response = await _apiClient.post('/marketplace/sales/$saleId/accept');
    return SaleOrder.fromJson(response);
  }

  Future<SaleOrder> advanceSale({required String saleId, required String targetStatus}) async {
    final response = await _apiClient.post('/marketplace/sales/$saleId/advance?target_status=$targetStatus');
    return SaleOrder.fromJson(response);
  }

  Future<SaleOrder> cancelSale({required String saleId, required String reason}) async {
    final response = await _apiClient.post('/marketplace/sales/$saleId/cancel', body: {'reason': reason});
    return SaleOrder.fromJson(response);
  }

  Future<void> fileSaleDispute({required String saleId, required String reason, String? description}) async {
    await _apiClient.post('/marketplace/sales/$saleId/dispute', body: {
      'reason': reason,
      if (description != null) 'description': description,
    });
  }

  Future<void> submitSaleFeedback({
    required String saleId,
    bool? helpful,
    int? rating,
    String? feedbackText,
  }) async {
    await _apiClient.post('/marketplace/sales/$saleId/feedback', body: {
      if (helpful != null) 'helpful': helpful,
      if (rating != null) 'rating': rating,
      if (feedbackText != null) 'feedback_text': feedbackText,
    });
  }
}
