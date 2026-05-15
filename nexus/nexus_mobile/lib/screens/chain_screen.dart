import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/action_chain.dart';

class ChainScreen extends StatefulWidget {
  final Map<String, dynamic> executeData;
  final String domain;

  const ChainScreen({super.key, required this.executeData, required this.domain});

  @override
  State<ChainScreen> createState() => _ChainScreenState();
}

class _ChainScreenState extends State<ChainScreen> {
  List<dynamic> _logs = [];
  Timer? _logTimer;
  Map<String, dynamic>? _baseline;

  @override
  void initState() {
    super.initState();
    _logTimer = Timer.periodic(const Duration(seconds: 3), (_) => _refreshLogs());
    _refreshLogs();
  }

  @override
  void dispose() {
    _logTimer?.cancel();
    super.dispose();
  }

  Future<void> _refreshLogs() async {
    try {
      final logs = await ApiService().getLogs();
      if (mounted) setState(() => _logs = logs);
    } catch (_) {}
  }

  Future<void> _loadBaseline() async {
    try {
      final data = await ApiService().getBaseline();
      if (mounted) setState(() => _baseline = data);
      _showBaselineDialog(data);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  void _showBaselineDialog(Map<String, dynamic> data) {
    final simple = data['simple_heuristic'] as Map<String, dynamic>;
    final nexus = data['nexus_agentic'] as Map<String, dynamic>;
    final rows = [
      ['Contradiction detection', simple['contradiction_detection'], nexus['contradiction_detection']],
      ['Credibility scoring', simple['source_credibility_scoring'], nexus['source_credibility_scoring']],
      ['Temporal analysis', simple['temporal_analysis'], nexus['temporal_analysis']],
      ['Failure recovery', simple['failure_recovery'], nexus['failure_recovery']],
      ['Avg latency', '${simple['avg_latency_ms']}ms', '${nexus['avg_latency_ms']}ms'],
      ['False signals caught', simple['false_signals_caught'], nexus['false_signals_caught']],
    ];
    showDialog(context: context, builder: (_) => AlertDialog(
      backgroundColor: const Color(0xFF111118),
      title: const Text('Baseline vs NEXUS', style: TextStyle(color: Color(0xFF4f8ef7))),
      content: SingleChildScrollView(
        child: DataTable(
          headingRowColor: WidgetStateProperty.all(const Color(0xFF0d0d14)),
          columns: const [
            DataColumn(label: Text('Capability', style: TextStyle(fontSize: 11, color: Colors.white38))),
            DataColumn(label: Text('Simple', style: TextStyle(fontSize: 11, color: Colors.white38))),
            DataColumn(label: Text('NEXUS', style: TextStyle(fontSize: 11, color: Colors.white38))),
          ],
          rows: rows.map((r) => DataRow(cells: [
            DataCell(Text(r[0] as String, style: const TextStyle(fontSize: 11))),
            DataCell(_cellVal(r[1])),
            DataCell(_cellVal(r[2])),
          ])).toList(),
        ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
    ));
  }

  Widget _cellVal(dynamic v) {
    if (v == true) return const Text('✓', style: TextStyle(color: Color(0xFF10b981), fontWeight: FontWeight.bold));
    if (v == false) return const Text('✗', style: TextStyle(color: Color(0xFFef4444), fontWeight: FontWeight.bold));
    return Text(v.toString(), style: const TextStyle(fontSize: 11));
  }

  @override
  Widget build(BuildContext context) {
    final chain = (widget.executeData['chain'] as List?)
        ?.map((a) => ActionChain.fromJson(a as Map<String, dynamic>)).toList() ?? [];
    final totalCost = widget.executeData['total_cost_pkr'] ?? 0;
    final totalLatency = widget.executeData['total_latency_ms'] ?? 0;
    final failures = widget.executeData['failures'] ?? 0;
    final recovered = widget.executeData['recovered'] ?? 0;
    final before = widget.executeData['before_state'] as Map<String, dynamic>? ?? {};
    final after = widget.executeData['after_state'] as Map<String, dynamic>? ?? {};
    final fields = ['status', 'actions_completed', 'total_cost_pkr', 'total_latency_ms', 'actions_failed', 'actions_recovered'];
    final recentLogs = _logs.length > 10 ? _logs.sublist(_logs.length - 10) : _logs;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0d0d14),
        title: const Text('Outcome'),
      ),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(children: [
            _metricCard('Total Cost', 'PKR $totalCost'),
            _metricCard('Latency', '${totalLatency}ms'),
            _metricCard('Failures', '$failures'),
            _metricCard('Recovered', '$recovered'),
          ]),
        ),
        const SizedBox(height: 16),

        _sectionTitle('Before / After'),
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: _stateCol('Before', before, fields, null)),
          const SizedBox(width: 8),
          Expanded(child: _stateCol('After', after, fields, before)),
        ]),
        const SizedBox(height: 16),

        _sectionTitle('What-If Side Effects'),
        ...chain.where((a) => a.sideEffect.isNotEmpty).map((a) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Step ${a.step} — ${a.monitor}', style: const TextStyle(fontSize: 10, color: Colors.white38, fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(a.sideEffect, style: const TextStyle(fontSize: 12, color: Colors.white70)),
          ]),
        )),
        const SizedBox(height: 16),

        TextButton(
          onPressed: _loadBaseline,
          child: const Text('Compare vs Non-Agentic Baseline', style: TextStyle(color: Color(0xFF4f8ef7))),
        ),
        const SizedBox(height: 8),

        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Trace ready — download from web dashboard or include in submission'),
              ));
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4f8ef7),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('Export Antigravity Trace', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
        const SizedBox(height: 16),

        _sectionTitle('Live Execution Log'),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF050508),
            border: Border.all(color: const Color(0xFF0f0f1a)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: recentLogs.isEmpty
              ? const Text('Waiting for activity...', style: TextStyle(color: Colors.white24, fontSize: 12, fontFamily: 'monospace'))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: recentLogs.map<Widget>((l) {
                    final msg = l['message'] as String? ?? '';
                    Color col = const Color(0xFF00ff88);
                    if (msg.toLowerCase().contains('failed') || msg.toLowerCase().contains('error')) col = const Color(0xFFef4444);
                    if (msg.toLowerCase().contains('recovered') || msg.toLowerCase().contains('retry')) col = const Color(0xFFf59e0b);
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 3),
                      child: Text('[${l['time_display']}] $msg', style: TextStyle(color: col, fontSize: 11, fontFamily: 'monospace')),
                    );
                  }).toList(),
                ),
        ),
      ]),
    );
  }

  Widget _metricCard(String label, String val) => Container(
        width: 120,
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF111118),
          border: Border.all(color: const Color(0xFF1e1e2e)),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(children: [
          Text(label, style: const TextStyle(fontSize: 10, color: Colors.white38)),
          const SizedBox(height: 4),
          Text(val, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF4f8ef7))),
        ]),
      );

  Widget _stateCol(String header, Map<String, dynamic> state, List<String> fields, Map<String, dynamic>? compare) {
    final isAfter = compare != null;
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: const Color(0xFF0d0d14), borderRadius: BorderRadius.circular(8)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(header, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isAfter ? const Color(0xFF4f8ef7) : Colors.white38)),
        const SizedBox(height: 6),
        ...fields.map((f) {
          final val = state[f]?.toString() ?? '-';
          final changed = compare != null && compare[f]?.toString() != val;
          return Container(
            margin: const EdgeInsets.only(bottom: 3),
            padding: const EdgeInsets.symmetric(horizontal: changed ? 6 : 0, vertical: 2),
            decoration: BoxDecoration(
              border: changed ? const Border(left: BorderSide(color: Color(0xFFf59e0b), width: 3)) : null,
            ),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text(f.replaceAll('_', ' '), style: const TextStyle(fontSize: 9, color: Colors.white38)),
              Text(val, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: changed ? const Color(0xFFf59e0b) : Colors.white70)),
            ]),
          );
        }),
      ]),
    );
  }

  Widget _sectionTitle(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(t, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF4f8ef7))),
      );
}
