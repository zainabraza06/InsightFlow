import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../services/auth_service.dart';

class HistoryDetailScreen extends StatefulWidget {
  final String entryId;
  final String topic;

  const HistoryDetailScreen({super.key, required this.entryId, required this.topic});

  @override
  State<HistoryDetailScreen> createState() => _HistoryDetailScreenState();
}

class _HistoryDetailScreenState extends State<HistoryDetailScreen> {
  Map<String, dynamic>? _entry;
  bool _loading = true;
  String _error = '';

  // Feedback state
  int? _rating;
  final _commentCtrl = TextEditingController();
  bool _submitting = false;
  bool _feedbackDone = false;
  String _learningMsg = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _commentCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final headers = await AuthService.authHeaders();
      final res = await http.get(
        Uri.parse('${AppConfig.baseUrl}/history/${widget.entryId}'),
        headers: headers,
      );
      if (res.statusCode == 200) {
        setState(() => _entry = jsonDecode(res.body) as Map<String, dynamic>);
      } else {
        setState(() => _error = 'Failed to load detail');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _submitFeedback() async {
    if (_rating == null) return;
    setState(() => _submitting = true);
    try {
      final headers = await AuthService.authHeaders();
      headers['Content-Type'] = 'application/json';
      final res = await http.post(
        Uri.parse('${AppConfig.baseUrl}/feedback'),
        headers: headers,
        body: jsonEncode({
          'rating': _rating,
          'domain': _entry?['domain'] ?? '',
          'comment': _commentCtrl.text,
          'analysis_id': widget.entryId,
        }),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final ctx = data['learning_context'] as Map<String, dynamic>? ?? {};
        setState(() {
          _feedbackDone = true;
          _learningMsg = ctx['has_feedback'] == true
              ? '[INSIGHTFLOW LEARNING] domain=${_entry?['domain']} avg=${ctx['avg_rating']}/5 sentiment=${ctx['sentiment']}'
              : '';
        });
      }
    } catch (_) {
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0a0a0f),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0f0f1a),
        title: Text(
          widget.topic.length > 30 ? '${widget.topic.substring(0, 30)}…' : widget.topic,
          style: const TextStyle(color: Colors.white, fontSize: 15),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00d4ff)))
          : _error.isNotEmpty
              ? Center(child: Text(_error, style: const TextStyle(color: Color(0xFFEF4444))))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildSummaryRow(),
                    const SizedBox(height: 16),
                    _buildFeedback(),
                    const SizedBox(height: 16),
                    _buildAgentDebate(),
                    const SizedBox(height: 16),
                    _buildActionChain(),
                    if (_entry?['execute_result'] != null) ...[
                      const SizedBox(height: 16),
                      _buildExecutionSummary(),
                    ],
                  ],
                ),
    );
  }

  Widget _buildSummaryRow() {
    final e = _entry!;
    final cost = (e['total_cost_pkr'] as num?)?.toInt() ?? 0;
    return Row(
      children: [
        _statCard('Sources', '${e['sources_processed'] ?? 0}', const Color(0xFF00d4ff)),
        const SizedBox(width: 8),
        _statCard('Conflicts', '${e['contradictions_found'] ?? 0}', const Color(0xFFf59e0b)),
        const SizedBox(width: 8),
        _statCard('Actions', '${e['actions_total'] ?? 0}', const Color(0xFF8b5cf6)),
        const SizedBox(width: 8),
        _statCard('Cost', 'PKR\n${_fmt(cost)}', Colors.white),
      ],
    );
  }

  Widget _statCard(String label, String value, Color color) => Expanded(
        child: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: const Color(0xFF0f0f1a),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF1a1a2e)),
          ),
          child: Column(
            children: [
              Text(value, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.bold, fontFamily: 'monospace'), textAlign: TextAlign.center),
              const SizedBox(height: 2),
              Text(label, style: const TextStyle(color: Color(0xFF6b7280), fontSize: 10)),
            ],
          ),
        ),
      );

  Widget _buildFeedback() {
    if (_feedbackDone) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF0f0f1a),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: (_rating ?? 0) >= 4 ? const Color(0x4D10b981) : const Color(0x4DEF4444)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text((_rating ?? 0) >= 4 ? '✅ Agents noted your satisfaction' : '🔄 Agents will improve',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
          const SizedBox(height: 4),
          if (_learningMsg.isNotEmpty)
            Text(_learningMsg, style: const TextStyle(color: Color(0xFF8b5cf6), fontSize: 10, fontFamily: 'monospace')),
        ]),
      );
    }

    final emojis = ['😤', '😞', '😐', '😊', '🤩'];
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: const Color(0xFF0f0f1a), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFF1a1a2e))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Rate this analysis', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
        const Text('agents learn from your feedback', style: TextStyle(color: Color(0xFF6b7280), fontSize: 11)),
        const SizedBox(height: 10),
        Row(
          children: List.generate(5, (i) => Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _rating = i + 1),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 2),
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  color: _rating == i + 1 ? const Color(0x1A00d4ff) : const Color(0xFF0d0d14),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: _rating == i + 1 ? const Color(0xFF00d4ff) : const Color(0xFF1e1e2e)),
                ),
                child: Text(emojis[i], textAlign: TextAlign.center, style: const TextStyle(fontSize: 20)),
              ),
            ),
          )),
        ),
        if (_rating != null) ...[
          const SizedBox(height: 8),
          TextField(
            controller: _commentCtrl,
            style: const TextStyle(color: Colors.white, fontSize: 12),
            maxLines: 2,
            decoration: InputDecoration(
              hintText: (_rating ?? 0) <= 2 ? 'What was wrong? (agents will learn)' : 'What did agents do well?',
              hintStyle: const TextStyle(color: Colors.white24, fontSize: 12),
              filled: true, fillColor: const Color(0xFF0d0d14),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(0xFF1e1e2e))),
              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _submitting ? null : _submitFeedback,
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00d4ff), foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 10), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
              child: _submitting ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                  : const Text('Submit Feedback', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            ),
          ),
        ],
      ]),
    );
  }

  Widget _buildAgentDebate() {
    final analyze = _entry?['analyze_result'] as Map<String, dynamic>?;
    if (analyze == null) return const SizedBox.shrink();
    final agents = (analyze['agents'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final resolved = analyze['resolved'] as Map<String, dynamic>? ?? {};
    final colors = [const Color(0xFF10b981), const Color(0xFFef4444), const Color(0xFF8b5cf6)];

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sectionTitle('Agent Debate'),
      ...List.generate(agents.length, (i) {
        final ag = agents[i];
        final conf = (ag['confidence'] as num?)?.toInt() ?? 0;
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF0f0f1a),
            border: Border(left: BorderSide(color: colors[i % colors.length], width: 3)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Text(ag['agent'] ?? '', style: TextStyle(color: colors[i % colors.length], fontWeight: FontWeight.bold, fontSize: 13)),
              const Spacer(),
              Text('$conf%', style: TextStyle(color: colors[i % colors.length], fontSize: 12, fontFamily: 'monospace')),
            ]),
            const SizedBox(height: 4),
            Text(ag['persona'] ?? '', style: const TextStyle(color: Color(0xFF6b7280), fontSize: 10)),
            const SizedBox(height: 6),
            Text(ag['insight'] ?? '', style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 12)),
          ]),
        );
      }),
      if (resolved['final_insight'] != null) ...[
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF0a0a14),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0x4D00d4ff)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Resolver Synthesis', style: TextStyle(color: Color(0xFF00d4ff), fontWeight: FontWeight.bold, fontSize: 12)),
            const SizedBox(height: 6),
            Text(resolved['final_insight'] ?? '', style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 12)),
          ]),
        ),
      ],
    ]);
  }

  Widget _buildActionChain() {
    final execute = _entry?['execute_result'] as Map<String, dynamic>?;
    final analyze = _entry?['analyze_result'] as Map<String, dynamic>?;
    final chain = (execute?['chain'] ?? analyze?['action_chain'] as List?) as List?;
    if (chain == null || chain.isEmpty) return const SizedBox.shrink();

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sectionTitle('Action Chain'),
      ...chain.cast<Map<String, dynamic>>().map((action) {
        final step = action['step'] as int? ?? 0;
        final status = action['status'] as String? ?? 'PENDING';
        final cost = (action['estimated_cost_pkr'] as num?)?.toInt() ?? 0;
        final mins = action['estimated_time_minutes'] as int? ?? 0;
        final modified = action['was_modified'] == true;
        final isDone = status == 'DONE' || status == 'COMPLETED';

        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF0f0f1a),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: isDone ? const Color(0x4D10b981) : const Color(0xFF1a1a2e)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: const Color(0x1A00d4ff), borderRadius: BorderRadius.circular(4)),
                child: Text('$step', style: const TextStyle(color: Color(0xFF00d4ff), fontSize: 11, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: isDone ? const Color(0x1A10b981) : const Color(0x1A6b7280),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(status, style: TextStyle(color: isDone ? const Color(0xFF10b981) : const Color(0xFF6b7280), fontSize: 10)),
              ),
              if (modified) ...[
                const SizedBox(width: 6),
                const Text('⚠', style: TextStyle(fontSize: 11)),
              ],
            ]),
            const SizedBox(height: 6),
            Text(action['action'] ?? '', style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 12)),
            const SizedBox(height: 6),
            Text('PKR ${_fmt(cost)} · ${mins}min', style: const TextStyle(color: Color(0xFF6b7280), fontSize: 11, fontFamily: 'monospace')),
          ]),
        );
      }),
    ]);
  }

  Widget _buildExecutionSummary() {
    final exec = _entry!['execute_result'] as Map<String, dynamic>;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: const Color(0xFF0f0f1a), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFF1a1a2e))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionTitle('Execution Summary'),
        Row(children: [
          _execStat('Failures', '${exec['failures'] ?? 0}', const Color(0xFFEF4444)),
          const SizedBox(width: 24),
          _execStat('Recovered', '${exec['recovered'] ?? 0}', const Color(0xFF10b981)),
          const SizedBox(width: 24),
          _execStat('Latency', '${exec['total_latency_ms'] ?? 0}ms', Colors.white),
        ]),
      ]),
    );
  }

  Widget _execStat(String label, String val, Color color) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(label, style: const TextStyle(color: Color(0xFF6b7280), fontSize: 10)),
    Text(val, style: TextStyle(color: color, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.bold)),
  ]);

  Widget _sectionTitle(String t) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(t, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF4f8ef7))),
  );

  String _fmt(int n) => n.toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]},');
}
