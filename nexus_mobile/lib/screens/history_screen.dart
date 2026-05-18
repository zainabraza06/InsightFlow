import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../services/auth_service.dart';
import 'history_detail_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<Map<String, dynamic>> _entries = [];
  bool _loading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = ''; });
    try {
      final headers = await AuthService.authHeaders();
      final res = await http.get(Uri.parse('${AppConfig.baseUrl}/history'), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List<dynamic>;
        setState(() => _entries = data.cast<Map<String, dynamic>>());
      } else {
        setState(() => _error = 'Failed to load history');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _delete(String id) async {
    final headers = await AuthService.authHeaders();
    await http.delete(Uri.parse('${AppConfig.baseUrl}/history/$id'), headers: headers);
    setState(() => _entries.removeWhere((e) => e['id'] == id));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0a0a0f),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0f0f1a),
        title: const Text('Analysis History', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: Color(0xFF00d4ff)), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00d4ff)))
          : _error.isNotEmpty
              ? Center(child: Text(_error, style: const TextStyle(color: Color(0xFFEF4444))))
              : _entries.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('📋', style: TextStyle(fontSize: 48)),
                          SizedBox(height: 12),
                          Text('No analyses yet', style: TextStyle(color: Color(0xFF6b7280))),
                          SizedBox(height: 4),
                          Text('Run an analysis to save it here', style: TextStyle(color: Color(0xFF374151), fontSize: 12)),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      color: const Color(0xFF00d4ff),
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _entries.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (ctx, i) => _EntryCard(
                          entry: _entries[i],
                          onDelete: () => _delete(_entries[i]['id'] as String),
                          onTap: () => Navigator.push(ctx, MaterialPageRoute(
                            builder: (_) => HistoryDetailScreen(
                              entryId: _entries[i]['id'] as String,
                              topic: _entries[i]['topic'] as String? ?? 'Analysis Detail',
                            ),
                          )),
                        ),
                      ),
                    ),
    );
  }
}

class _EntryCard extends StatelessWidget {
  final Map<String, dynamic> entry;
  final VoidCallback onDelete;
  final VoidCallback onTap;

  const _EntryCard({required this.entry, required this.onDelete, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final domain = entry['domain'] as String? ?? '';
    final topic = entry['topic'] as String? ?? 'Untitled';
    final ts = entry['timestamp'] as String? ?? '';
    final cost = (entry['total_cost_pkr'] as num?)?.toInt() ?? 0;
    final sources = (entry['sources_processed'] as num?)?.toInt() ?? 0;
    final conflicts = (entry['contradictions_found'] as num?)?.toInt() ?? 0;

    return GestureDetector(
      onTap: onTap,
      child: Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0f0f1a),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1a1a2e)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0x1A00d4ff),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0x4D00d4ff)),
                ),
                child: Text(domain, style: const TextStyle(color: Color(0xFF00d4ff), fontSize: 11, fontWeight: FontWeight.w600)),
              ),
              const Spacer(),
              Text(ts.length > 16 ? ts.substring(0, 16).replaceAll('T', ' ') : ts,
                  style: const TextStyle(color: Color(0xFF4b5563), fontSize: 11, fontFamily: 'monospace')),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onDelete,
                child: const Icon(Icons.delete_outline, color: Color(0xFF6b7280), size: 18),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(topic, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500), maxLines: 2, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 10),
          Row(
            children: [
              _stat('Sources', '$sources', const Color(0xFF00d4ff)),
              const SizedBox(width: 16),
              _stat('Conflicts', '$conflicts', const Color(0xFFF59e0b)),
              const SizedBox(width: 16),
              _stat('Cost', 'PKR ${cost.toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]},')}', Colors.white),
            ],
          ),
        ],
      ),
      ),
    );
  }

  Widget _stat(String label, String value, Color color) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label, style: const TextStyle(color: Color(0xFF6b7280), fontSize: 10)),
      Text(value, style: TextStyle(color: color, fontSize: 12, fontFamily: 'monospace', fontWeight: FontWeight.w600)),
    ],
  );
}
