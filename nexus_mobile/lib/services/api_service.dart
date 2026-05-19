import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';
import 'auth_service.dart';

class ApiService {
  Future<Map<String, dynamic>> ingest({
    String text = '',
    String url = '',
    String csvData = '',
    String domain = 'Business',
    String topic = '',
    bool includeFeed = true,
  }) async {
    final token = await AuthService.getToken();
    final req = http.MultipartRequest('POST', Uri.parse('${AppConfig.baseUrl}/ingest'));
    if (token != null) req.headers['Authorization'] = 'Bearer $token';
    req.fields['text'] = text;
    req.fields['url'] = url;
    req.fields['csv_data'] = csvData;
    req.fields['domain'] = domain;
    req.fields['topic'] = topic;
    req.fields['include_feed'] = includeFeed ? 'true' : 'false';
    final res = await req.send();
    final body = await res.stream.bytesToString();
    return jsonDecode(body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> analyze(String domain) async {
    final headers = await AuthService.authHeaders();
    final res = await http.post(Uri.parse('${AppConfig.baseUrl}/analyze'),
        headers: headers, body: jsonEncode({'domain': domain}));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> execute(List<dynamic> chain, String domain) async {
    final headers = await AuthService.authHeaders();
    final res = await http.post(Uri.parse('${AppConfig.baseUrl}/execute'),
        headers: headers, body: jsonEncode({'chain': chain, 'domain': domain}));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> whatIf(Map<String, dynamic> modifications) async {
    final headers = await AuthService.authHeaders();
    final res = await http.post(Uri.parse('${AppConfig.baseUrl}/what-if'),
        headers: headers, body: jsonEncode({'modifications': modifications}));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getState() async {
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/state'));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getLogs() async {
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/logs'));
    return (jsonDecode(res.body) as Map<String, dynamic>)['logs'] as List<dynamic>;
  }

  Future<Map<String, dynamic>> getBaseline() async {
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/baseline-comparison'));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> submitFeedback({
    required int rating,
    required String domain,
    String comment = '',
    String analysisId = '',
    Map<String, dynamic>? agentConfidences,
  }) async {
    final headers = await AuthService.authHeaders();
    final res = await http.post(Uri.parse('${AppConfig.baseUrl}/feedback'),
        headers: headers,
        body: jsonEncode({
          'rating': rating,
          'domain': domain,
          'comment': comment,
          'analysis_id': analysisId,
          if (agentConfidences != null) 'agent_confidences': agentConfidences,
        }));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getHistory() async {
    final headers = await AuthService.authHeaders();
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/history'), headers: headers);
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getHistoryEntry(String id) async {
    final headers = await AuthService.authHeaders();
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/history/$id'), headers: headers);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<bool> deleteHistoryEntry(String id) async {
    final headers = await AuthService.authHeaders();
    final res = await http.delete(Uri.parse('${AppConfig.baseUrl}/history/$id'), headers: headers);
    return res.statusCode == 200;
  }

  Future<Map<String, dynamic>> saveHistory(Map<String, dynamic> entry) async {
    final headers = await AuthService.authHeaders();
    final res = await http.post(Uri.parse('${AppConfig.baseUrl}/history'),
        headers: headers, body: jsonEncode(entry));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getHealth() async {
    final res = await http.get(Uri.parse('${AppConfig.baseUrl}/health'));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
