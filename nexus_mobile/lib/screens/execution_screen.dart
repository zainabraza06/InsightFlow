import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/action_chain.dart';
import 'chain_screen.dart';

class ExecutionScreen extends StatefulWidget {
  final Map<String, dynamic> consensusData;
  final String domain;

  const ExecutionScreen({super.key, required this.consensusData, required this.domain});

  @override
  State<ExecutionScreen> createState() => _ExecutionScreenState();
}

class _ExecutionScreenState extends State<ExecutionScreen> {
  late List<ActionChain> _chain;
  bool _executing = false;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    final rawChain = (widget.consensusData['action_chain'] as List?) ?? [];
    _chain = rawChain.map((a) => ActionChain.fromJson(a as Map<String, dynamic>)).toList();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _execute() async {
    setState(() => _executing = true);
    try {
      final rawChain = _chain.map((a) => {
        'step': a.step, 'action': a.action, 'triggered_by': a.triggeredBy,
        'enables': a.enables, 'side_effect': a.sideEffect, 'monitor': a.monitor,
        'estimated_cost_pkr': a.estimatedCostPkr, 'estimated_time_minutes': a.estimatedTimeMinutes,
        'status': a.status, 'feasible': a.feasible, 'was_modified': a.wasModified,
      }).toList();

      final result = await ApiService().execute(rawChain, widget.domain);
      final updatedChain = (result['chain'] as List?)
          ?.map((a) => ActionChain.fromJson(a as Map<String, dynamic>))
          .toList() ?? _chain;

      if (mounted) {
        setState(() => _chain = updatedChain);
        Navigator.push(context, MaterialPageRoute(
          builder: (_) => ChainScreen(executeData: result, domain: widget.domain),
        ));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
    if (mounted) setState(() => _executing = false);
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'DONE': return const Color(0xFF10b981);
      case 'FAILED': return const Color(0xFFef4444);
      case 'RECOVERED': return const Color(0xFFf59e0b);
      case 'RUNNING': return const Color(0xFF4f8ef7);
      default: return const Color(0xFF6b7280);
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalCost = widget.consensusData['total_estimated_cost_pkr'] ?? 0;
    final totalTime = widget.consensusData['total_estimated_time_minutes'] ?? 0;
    final modCount = _chain.where((a) => a.wasModified).length;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0d0d14),
        title: const Text('Action Chain'),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _executing ? null : _execute,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10b981),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: _executing
                ? const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                    SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                    SizedBox(width: 8),
                    Text('Executing...'),
                  ])
                : const Text('Execute Chain', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(children: [
            _chip('PKR ${(totalCost as num).toStringAsFixed(0)}', const Color(0xFF4f8ef7)),
            const SizedBox(width: 8),
            _chip('$totalTime min', const Color(0xFF6b7280)),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: modCount == 0 ? const Color(0xFF10b981).withOpacity(0.1) : const Color(0xFFf59e0b).withOpacity(0.1),
              border: Border.all(color: modCount == 0 ? const Color(0xFF10b981) : const Color(0xFFf59e0b)),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              modCount == 0 ? '✓ All actions feasible' : '⚠ $modCount action(s) modified',
              style: TextStyle(color: modCount == 0 ? const Color(0xFF10b981) : const Color(0xFFf59e0b), fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _chain.length,
            itemBuilder: (_, i) {
              final a = _chain[i];
              return Card(
                color: const Color(0xFF111118),
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: const BorderSide(color: Color(0xFF1e1e2e))),
                child: ExpansionTile(
                  tilePadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  leading: CircleAvatar(
                    backgroundColor: const Color(0xFF4f8ef7),
                    radius: 14,
                    child: Text('${a.step}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                  title: Text(a.action, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600), maxLines: 2, overflow: TextOverflow.ellipsis),
                  subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('↳ ${a.triggeredBy}', style: const TextStyle(fontSize: 10, fontStyle: FontStyle.italic, color: Colors.white38)),
                    const SizedBox(height: 2),
                    Row(children: [
                      _statusChip(a.status),
                      const SizedBox(width: 6),
                      _chip('PKR ${a.estimatedCostPkr}', const Color(0xFF4f8ef7)),
                      const SizedBox(width: 6),
                      _chip('${a.estimatedTimeMinutes}m', const Color(0xFF6b7280)),
                    ]),
                  ]),
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        _detailRow('Enables', a.enables),
                        _detailRow('Side Effect', a.sideEffect),
                        _detailRow('Monitor', a.monitor),
                        if (a.wasModified) _detailRow('Note', 'Modified to meet constraints', color: const Color(0xFFf59e0b)),
                      ]),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ]),
    );
  }

  Widget _chip(String label, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: color.withOpacity(0.15), borderRadius: BorderRadius.circular(4)),
        child: Text(label, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w600)),
      );

  Widget _statusChip(String status) {
    final col = _statusColor(status);
    return _chip(status, col);
  }

  Widget _detailRow(String label, String val, {Color? color}) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 80, child: Text(label, style: const TextStyle(fontSize: 10, color: Colors.white38))),
          Expanded(child: Text(val, style: TextStyle(fontSize: 11, color: color ?? Colors.white70))),
        ]),
      );
}
