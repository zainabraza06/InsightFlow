import 'action_chain.dart';

class ExecutionResult {
  final List<ActionChain> chain;
  final int totalCostPkr;
  final int totalLatencyMs;
  final int failures;
  final int recovered;
  final Map<String, dynamic> beforeState;
  final Map<String, dynamic> afterState;

  ExecutionResult({
    required this.chain,
    required this.totalCostPkr,
    required this.totalLatencyMs,
    required this.failures,
    required this.recovered,
    required this.beforeState,
    required this.afterState,
  });

  factory ExecutionResult.fromJson(Map<String, dynamic> json) => ExecutionResult(
        chain: (json['chain'] as List? ?? [])
            .map((a) => ActionChain.fromJson(a))
            .toList(),
        totalCostPkr: (json['total_cost_pkr'] ?? 0).toInt(),
        totalLatencyMs: (json['total_latency_ms'] ?? 0).toInt(),
        failures: (json['failures'] ?? 0).toInt(),
        recovered: (json['recovered'] ?? 0).toInt(),
        beforeState: json['before_state'] ?? {},
        afterState: json['after_state'] ?? {},
      );
}
