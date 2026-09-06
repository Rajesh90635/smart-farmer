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

/// D84-01 (docs/audit/FINAL_CANONICAL_group_D.md): thrown instead of a raw
/// ApiException(401) once a silent refresh attempt has already failed -
/// every screen can catch this ONE type uniformly (e.g. via FriendlyError)
/// rather than each needing its own ad hoc 401-handling logic.
class SessionExpiredException implements Exception {
  const SessionExpiredException();

  @override
  String toString() => 'SessionExpiredException';
}

class ApiClient {
  final http.Client _client;
  final String baseUrl;
  String? _accessToken;

  /// D84-01: set once at app startup (see app.dart) to close the circular-
  /// dependency gap between ApiClient and AuthRepository - attempts ONE
  /// silent token refresh on any 401, returning the new access token on
  /// success or null on failure (refresh token itself expired/revoked).
  Future<String?> Function()? onSessionExpired;
  bool _refreshInProgress = false;

  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  void setAccessToken(String? token) => _accessToken = token;

  Map<String, String> get _defaultHeaders => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  /// Wraps every call site below: on a 401, attempts exactly one silent
  /// refresh (never recursively - `_refreshInProgress` guards the refresh
  /// call's OWN request from re-triggering this), then either transparently
  /// retries the original request with the new token or surfaces a single,
  /// uniform SessionExpiredException instead of the raw 401.
  Future<T> _withSessionRetry<T>(Future<T> Function() attempt) async {
    try {
      return await attempt();
    } on ApiException catch (e) {
      if (e.statusCode != 401 || onSessionExpired == null || _refreshInProgress) {
        rethrow;
      }
      _refreshInProgress = true;
      String? newToken;
      try {
        newToken = await onSessionExpired!();
      } finally {
        _refreshInProgress = false;
      }
      if (newToken == null) {
        throw const SessionExpiredException();
      }
      setAccessToken(newToken);
      return await attempt();
    }
  }

  Future<Map<String, dynamic>> get(String path) => _withSessionRetry(() => _send('GET', path));

  /// For endpoints that return a raw JSON array (e.g. /crops/master)
  /// rather than the {items, total} envelope most list endpoints use.
  Future<List<dynamic>> getList(String path) => _withSessionRetry(() => _getListOnce(path));

  Future<List<dynamic>> _getListOnce(String path) async {
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
  Future<Uint8List> getBytes(String path) => _withSessionRetry(() => _getBytesOnce(path));

  Future<Uint8List> _getBytesOnce(String path) async {
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
  }) => _withSessionRetry(() => _uploadMultipartOnce(path, fileBytes: fileBytes, fileName: fileName, mimeType: mimeType, fields: fields));

  Future<Map<String, dynamic>> _uploadMultipartOnce(
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

  /// `interceptSessionExpiry: false` opts a call OUT of the 401 -> silent-
  /// refresh interceptor - required for the auth-issuing endpoints
  /// themselves (login/register/refresh/reset-password), where a 401
  /// means "bad credentials/OTP", never "this session expired". Every
  /// other authenticated POST correctly defaults to intercepted.
  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body, bool interceptSessionExpiry = true}) {
    return interceptSessionExpiry ? _withSessionRetry(() => _send('POST', path, body: body)) : _send('POST', path, body: body);
  }

  Future<Map<String, dynamic>> put(String path, {Map<String, dynamic>? body}) =>
      _withSessionRetry(() => _send('PUT', path, body: body));

  Future<Map<String, dynamic>> delete(String path) => _withSessionRetry(() => _send('DELETE', path));

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
