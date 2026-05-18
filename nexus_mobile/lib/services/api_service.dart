import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiService {
  Future<Map<String, dynamic>> ingest({
    String text = '',
    String url = '',
    String csvData = '',
    String domain = 'Business',
    String topic = '',
    bool includeFeed = true,
  }) async {
    final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/ingest'));
    req.fields['text'] = text;
    req.fields['url'] = url;
    req.fields['csv_data'] = csvData;
    req.fields['domain'] = domain;
    req.fields['topic'] = topic;
    req.fields['include_feed'] = includeFeed ? 'true' : 'false';
    final res = await req.send();
    final body = await res.stream.bytesToString();
    return jsonDecode(body);
  }

  Future<Map<String, dynamic>> analyze(String domain) async {
    final res = await http.post(
      Uri.parse('$baseUrl/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'domain': domain}),
    );
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> execute(List chain, String domain) async {
    final res = await http.post(
      Uri.parse('$baseUrl/execute'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'chain': chain, 'domain': domain}),
    );
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> getState() async {
    final res = await http.get(Uri.parse('$baseUrl/state'));
    return jsonDecode(res.body);
  }

  Future<List<dynamic>> getLogs() async {
    final res = await http.get(Uri.parse('$baseUrl/logs'));
    return jsonDecode(res.body)['logs'];
  }

  Future<Map<String, dynamic>> getBaseline() async {
    final res = await http.get(Uri.parse('$baseUrl/baseline-comparison'));
    return jsonDecode(res.body);
  }
}
