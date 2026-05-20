import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'execution_screen.dart';

class DebateScreen extends StatefulWidget {
  final Map<String, dynamic> ingestData;
  final String domain;
  final Map<String, dynamic>? constraints;

  const DebateScreen({super.key, required this.ingestData, required this.domain, this.constraints});

  @override
  State<DebateScreen> createState() => _DebateScreenState();
}

class _DebateScreenState extends State<DebateScreen> {
  final List<bool> _agentVisible = [false, false, false];
  bool _analyzing = false;

  @override
  void initState() {
    super.initState();
    for (int i = 0; i < 3; i++) {
      Future.delayed(Duration(milliseconds: 200 * i), () {
        if (mounted) setState(() => _agentVisible[i] = true);
      });
    }
  }

  Future<void> _analyze() async {
    setState(() => _analyzing = true);
    try {
      final data = await ApiService().analyze(widget.domain, constraints: widget.constraints);
      if (mounted) {
        Navigator.push(context, MaterialPageRoute(
          builder: (_) => ExecutionScreen(
            consensusData: data,
            ingestData: widget.ingestData,
            domain: widget.domain,
          ),
        ));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
    if (mounted) setState(() => _analyzing = false);
  }

  @override
  Widget build(BuildContext context) {
    final credMap = widget.ingestData['credibility_map'] as Map<String, dynamic>? ?? {};
    final contData = widget.ingestData['contradictions'] as Map<String, dynamic>? ?? {};
    final temporal = widget.ingestData['temporal_analysis'] as Map<String, dynamic>? ?? {};
    final noiseFiltered = (widget.ingestData['noise_filtered'] as List?)?.cast<String>() ?? [];
    final contList = (contData['contradictions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final agents = (widget.ingestData['_agents'] as List?)?.cast<Map<String, dynamic>>() ?? [];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0d0d14),
        title: const Text('Source Intelligence + Agent Debate'),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _analyzing ? null : _analyze,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF8b5cf6),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: _analyzing
                ? const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                    SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                    SizedBox(width: 8),
                    Text('Validating Actions...'),
                  ])
                : const Text('Validate Actions', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        _sectionTitle('Source Credibility'),
        SizedBox(
          height: 110,
          child: ListView(scrollDirection: Axis.horizontal, children: credMap.entries.map((e) {
            final score = (e.value as num).toDouble();
            return _credCard(e.key, score);
          }).toList()),
        ),
        const SizedBox(height: 16),

        if ((temporal['has_trend'] as bool?) == true) ...[
          _sectionTitle('Temporal Analysis'),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF0d0d14),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _trendBadge(temporal['trend_direction'] as String? ?? 'unknown'),
              const SizedBox(height: 6),
              Text(temporal['trend_description'] as String? ?? '', style: const TextStyle(fontSize: 12, color: Colors.white60)),
              const SizedBox(height: 4),
              Text('Rate: ${temporal['rate_of_change'] ?? ''}', style: const TextStyle(fontSize: 11, color: Color(0xFFf59e0b))),
            ]),
          ),
          const SizedBox(height: 16),
        ],

        if (contList.isNotEmpty) ...[
          _sectionTitle('Contradictions (${contList.length})'),
          ...contList.map((c) => _contradictionTile(c)),
          const SizedBox(height: 16),
        ],

        if (noiseFiltered.isNotEmpty) ...[
          _sectionTitle('Excluded Sources'),
          Wrap(spacing: 8, children: noiseFiltered.map((t) => Chip(
            label: Text(t, style: const TextStyle(fontSize: 11)),
            backgroundColor: const Color(0xFF0d0d14),
            side: const BorderSide(color: Color(0xFF6b7280)),
          )).toList()),
          const SizedBox(height: 16),
        ],

        _sectionTitle('Overall Confidence: ${widget.ingestData['contradictions']?['overall_signal_confidence'] ?? '--'}'),
        const SizedBox(height: 16),

        _sectionTitle('Agent Analysis'),
        ..._buildAgentCards(agents),
      ]),
    );
  }

  List<Widget> _buildAgentCards(List<Map<String, dynamic>> agents) {
    if (agents.isEmpty) {
      return [const Padding(
        padding: EdgeInsets.only(bottom: 8),
        child: Text('Run analysis to see agent outputs.', style: TextStyle(color: Colors.white38, fontSize: 12)),
      )];
    }
    final colors = [const Color(0xFF10b981), const Color(0xFFef4444), const Color(0xFF8b5cf6)];
    return List.generate(agents.length, (i) {
      final ag = agents[i];
      return AnimatedOpacity(
        opacity: i < _agentVisible.length && _agentVisible[i] ? 1.0 : 0.0,
        duration: const Duration(milliseconds: 500),
        child: Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF0d0d14),
            border: Border(left: BorderSide(color: colors[i % colors.length], width: 4)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(ag['agent'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(ag['insight'] ?? '', style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 4),
            Text(ag['key_signal'] ?? '', style: TextStyle(fontSize: 11, color: colors[i % colors.length])),
            const SizedBox(height: 6),
            LinearProgressIndicator(
              value: ((ag['confidence'] as num?)?.toDouble() ?? 0) / 100,
              backgroundColor: const Color(0xFF1e1e2e),
              color: colors[i % colors.length],
            ),
          ]),
        ),
      );
    });
  }

  Widget _credCard(String type, double score) {
    Color col = score >= 0.7 ? const Color(0xFF10b981) : score >= 0.4 ? const Color(0xFFf59e0b) : const Color(0xFFef4444);
    return Container(
      width: 120,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: const Color(0xFF0d0d14), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFF1e1e2e))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(type.replaceAll('_', ' '), style: const TextStyle(fontSize: 10, color: Colors.white38)),
        const SizedBox(height: 4),
        Text('${(score * 100).round()}%', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: col)),
        const SizedBox(height: 4),
        LinearProgressIndicator(value: score, backgroundColor: const Color(0xFF1e1e2e), color: col),
      ]),
    );
  }

  Widget _contradictionTile(Map<String, dynamic> c) {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: Text(
        '${c['source_a_type']} vs ${c['source_b_type']}',
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      ),
      subtitle: Text(c['conflict_reason'] ?? '', style: const TextStyle(fontSize: 11, color: Colors.white38)),
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16, right: 16, bottom: 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Trust: ${c['trust_reason']}', style: const TextStyle(fontSize: 11, color: Color(0xFFf59e0b))),
            const SizedBox(height: 4),
            ...((c['investigation_path'] as List?)?.asMap().entries.map((e) =>
              Padding(padding: const EdgeInsets.only(top: 2), child: Text('${e.key + 1}. ${e.value}', style: const TextStyle(fontSize: 11, color: Colors.white54)))) ?? []),
          ]),
        ),
      ],
    );
  }

  Widget _trendBadge(String dir) {
    Color col = dir == 'worsening' ? const Color(0xFFef4444) : dir == 'improving' ? const Color(0xFF10b981) : const Color(0xFFf59e0b);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: col.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
      child: Text(dir.toUpperCase(), style: TextStyle(color: col, fontSize: 11, fontWeight: FontWeight.bold)),
    );
  }

  Widget _sectionTitle(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(t, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF4f8ef7))),
      );
}
