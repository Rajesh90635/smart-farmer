import '../../core/api_client.dart';
import 'dealer_market_models.dart';

/// Farmer-side surface of backend/app/api/v1/{products,orders}.py only -
/// dealer-role listing-management and fulfillment endpoints, and the
/// admin-role dispute-resolution/reference-price endpoints, have no
/// consumer here, matching the established farmer-only persona boundary.
class DealerMarketRepository {
  final ApiClient _apiClient;
  DealerMarketRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// GET /products only supports a `q` text filter server-side (no
  /// category param exists - see /seeds for the one category-scoped
  /// catalog endpoint) - a category chip picked in the UI filters this
  /// result client-side instead of being silently dropped.
  Future<List<Product>> listProducts({String? query}) async {
    final path = query != null && query.isNotEmpty ? '/products?q=${Uri.encodeQueryComponent(query)}' : '/products';
    final response = await _apiClient.get(path);
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(Product.fromJson).toList();
  }

  Future<Product> getProduct(String productId) async {
    final response = await _apiClient.get('/products/$productId');
    return Product.fromJson(response);
  }

  Future<PriceComparison> compareOffers(String productId) async {
    final response = await _apiClient.get('/products/$productId/compare');
    return PriceComparison.fromJson(response);
  }

  Future<ScamShieldStatus> getScamShieldStatus(String dealerProductId) async {
    final response = await _apiClient.get('/dealer-products/$dealerProductId/scam-shield');
    return ScamShieldStatus.fromJson(response);
  }

  Future<DealerOrder> addToCart({required String dealerProductId, required int quantity}) async {
    final response = await _apiClient.post('/cart', body: {'dealer_product_id': dealerProductId, 'quantity': quantity});
    return DealerOrder.fromJson(response);
  }

  Future<DealerOrder> getCart(String orderId) async {
    final response = await _apiClient.get('/cart/$orderId');
    return DealerOrder.fromJson(response);
  }

  Future<DealerOrder> updateCartItemQuantity({required String orderId, required String dealerProductId, required int quantity}) async {
    final response = await _apiClient.put('/cart/$orderId/items/$dealerProductId', body: {'quantity': quantity});
    return DealerOrder.fromJson(response);
  }

  Future<DealerOrder> removeCartItem({required String orderId, required String dealerProductId}) async {
    final response = await _apiClient.delete('/cart/$orderId/items/$dealerProductId');
    return DealerOrder.fromJson(response);
  }

  Future<DealerOrder> checkout({required String orderId, required String idempotencyKey}) async {
    final response = await _apiClient.post('/orders/$orderId/checkout', body: {'idempotency_key': idempotencyKey});
    return DealerOrder.fromJson(response);
  }

  Future<List<DealerOrder>> listMyOrders({int limit = 50, int offset = 0}) async {
    final response = await _apiClient.get('/orders?limit=$limit&offset=$offset');
    final items = (response['items'] as List).cast<Map<String, dynamic>>();
    return items.map(DealerOrder.fromJson).toList();
  }

  Future<DealerOrder> getOrder(String orderId) async {
    final response = await _apiClient.get('/orders/$orderId');
    return DealerOrder.fromJson(response);
  }

  Future<DealerOrder> cancelOrder(String orderId) async {
    final response = await _apiClient.post('/orders/$orderId/cancel');
    return DealerOrder.fromJson(response);
  }

  Future<void> initiatePayment(String orderId) async {
    await _apiClient.post('/orders/$orderId/pay');
  }

  /// SANDBOX/TEST-ONLY, mirroring the backend's own disclosed limitation
  /// (docs/PAYMENT_SANDBOX.md - no real payment gateway is integrated).
  /// This is the only way this app can move an order past
  /// `payment_pending` until a real gateway exists.
  Future<void> completeSandboxPayment(String orderId, {bool succeed = true}) async {
    await _apiClient.post('/orders/$orderId/pay/complete', body: {'succeed': succeed});
  }

  Future<DealerDelivery?> getDelivery(String orderId) async {
    try {
      final response = await _apiClient.get('/orders/$orderId/delivery');
      return DealerDelivery.fromJson(response);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<DealerOrder> confirmDelivery(String orderId) async {
    final response = await _apiClient.post('/orders/$orderId/confirm-delivery');
    return DealerOrder.fromJson(response);
  }

  Future<void> fileDispute({required String orderId, required String reason, String? description}) async {
    await _apiClient.post('/orders/$orderId/dispute', body: {
      'reason': reason,
      if (description != null) 'description': description,
    });
  }

  Future<DealerOrderDispute?> getDispute(String orderId) async {
    try {
      final response = await _apiClient.get('/orders/$orderId/dispute');
      return DealerOrderDispute.fromJson(response);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }
}
