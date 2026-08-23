import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'config.dart';

/// Thin wrapper around http.Client so business/feature code never imports
/// `package:http` directly. This is the single seam where auth headers,
/// correlation-id propagation, retry, and (later) offline-queue routing
/// get added - once, here, rather than duplicated at every call site.
class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final String? code;
  ApiException(this.message, {this.statusCode, this.code});

  @override
  String toString() => 'ApiException($statusCode/$code): $message';
}

class ApiClient {
  final http.Client _client;
  final String baseUrl;
  String? _accessToken;

  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  void setAccessToken(String? token) => _accessToken = token;

  Map<String, String> get _defaultHeaders => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Future<Map<String, dynamic>> get(String path) => _send('GET', path);

  /// For endpoints that return a raw JSON array (e.g. /crops/master)
  /// rather than the {items, total} envelope most list endpoints use.
  Future<List<dynamic>> getList(String path) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final response = await _client.get(uri, headers: _defaultHeaders);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (response.body.isEmpty) return [];
        return jsonDecode(response.body) as List<dynamic>;
      }
      _handle(response); // throws the appropriately-shaped ApiException
      return []; // unreachable - _handle always throws on non-2xx
    } on ApiException {
      rethrow;
    } on Exception catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  /// For binary responses (e.g. serving crop photo bytes) that need the
  /// same auth header as every other call - Image.network can't attach
  /// this automatically, so callers fetch bytes here and render via
  /// Image.memory instead.
  Future<Uint8List> getBytes(String path) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final response = await _client.get(uri, headers: _defaultHeaders);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.bodyBytes;
      }
      _handle(response);
      return Uint8List(0); // unreachable
    } on ApiException {
      rethrow;
    } on Exception catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  /// Multipart upload (crop photo upload). No byte-level progress percentage
  /// is reported in this phase - only an indeterminate "uploading" state,
  /// which is both simpler to implement correctly and arguably better UX
  /// for low-literacy users than a percentage number. Deferred as a
  /// possible enhancement, not an oversight - see docs/CROP_PHOTO_MODULE.md.
  Future<Map<String, dynamic>> uploadMultipart(
    String path, {
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    required Map<String, String> fields,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final request = http.MultipartRequest('POST', uri);
      request.headers.addAll({
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      });
      request.fields.addAll(fields);

      final mimeParts = mimeType.split('/');
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
          contentType: mimeParts.length == 2 ? MediaType(mimeParts[0], mimeParts[1]) : null,
        ),
      );

      final streamedResponse = await _client.send(request);
      final response = await http.Response.fromStream(streamedResponse);
      return _handle(response);
    } on ApiException {
      rethrow;
    } on Exception catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) =>
      _send('POST', path, body: body);

  Future<Map<String, dynamic>> put(String path, {Map<String, dynamic>? body}) =>
      _send('PUT', path, body: body);

  Future<Map<String, dynamic>> delete(String path) => _send('DELETE', path);

  Future<Map<String, dynamic>> _send(String method, String path, {Map<String, dynamic>? body}) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final encodedBody = body != null ? jsonEncode(body) : null;

      late final http.Response response;
      switch (method) {
        case 'GET':
          response = await _client.get(uri, headers: _defaultHeaders);
          break;
        case 'POST':
          response = await _client.post(uri, headers: _defaultHeaders, body: encodedBody);
          break;
        case 'PUT':
          response = await _client.put(uri, headers: _defaultHeaders, body: encodedBody);
          break;
        case 'DELETE':
          response = await _client.delete(uri, headers: _defaultHeaders);
          break;
        default:
          throw ArgumentError('Unsupported method: $method');
      }
      return _handle(response);
    } on ApiException {
      rethrow;
    } on Exception catch (e) {
      // Network-layer failures (no connectivity, DNS, etc.) surface here.
      // The offline-state architecture (see OFFLINE_ARCHITECTURE.md) is
      // responsible for deciding whether to queue-and-retry; this class
      // only reports the failure honestly, it never silently swallows it.
      throw ApiException('Network error: $e');
    }
  }

  Map<String, dynamic> _handle(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return {};
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    // Backend error shape: {"error": {"code": "...", "message": "...", "correlation_id": "..."}}
    String? code;
    String message = 'Request failed with status ${response.statusCode}';
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final error = decoded['error'] as Map<String, dynamic>?;
      if (error != null) {
        code = error['code'] as String?;
        message = (error['message'] as String?) ?? message;
      }
    } catch (_) {
      // Response body wasn't the expected JSON error shape - fall back to
      // the generic message above rather than throwing a second exception.
    }

    throw ApiException(message, statusCode: response.statusCode, code: code);
  }
}
