import 'agent_result.dart';
import 'action_chain.dart';

class Consensus {
  final List<AgentResult> agents;
  final double weightedConfidence;
  final bool agreement;
  final Map<String, dynamic> resolved;
  final List<ActionChain> actionChain;
  final String domain;
  final int totalCostPkr;
  final int totalTimeMinutes;

  Consensus({
    required this.agents,
    required this.weightedConfidence,
    required this.agreement,
    required this.resolved,
    required this.actionChain,
    required this.domain,
    required this.totalCostPkr,
    required this.totalTimeMinutes,
  });

  factory Consensus.fromJson(Map<String, dynamic> json) => Consensus(
        agents: (json['agents'] as List? ?? [])
            .map((a) => AgentResult.fromJson(a))
            .toList(),
        weightedConfidence: (json['weighted_confidence'] ?? 0).toDouble(),
        agreement: json['agreement'] ?? false,
        resolved: json['resolved'] ?? {},
        actionChain: (json['action_chain'] as List? ?? [])
            .map((a) => ActionChain.fromJson(a))
            .toList(),
        domain: json['domain'] ?? '',
        totalCostPkr: (json['total_estimated_cost_pkr'] ?? 0).toInt(),
        totalTimeMinutes: (json['total_estimated_time_minutes'] ?? 0).toInt(),
      );
}
