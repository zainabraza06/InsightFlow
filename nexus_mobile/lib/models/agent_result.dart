class AgentResult {
  final String agent;
  final String persona;
  final String insight;
  final String impact;
  final String recommendedAction;
  final String reasoning;
  final String keySignal;
  final int confidence;

  AgentResult({
    required this.agent,
    required this.persona,
    required this.insight,
    required this.impact,
    required this.recommendedAction,
    required this.reasoning,
    required this.keySignal,
    required this.confidence,
  });

  factory AgentResult.fromJson(Map<String, dynamic> json) => AgentResult(
        agent: json['agent'] ?? '',
        persona: json['persona'] ?? '',
        insight: json['insight'] ?? '',
        impact: json['impact'] ?? '',
        recommendedAction: json['recommended_action'] ?? '',
        reasoning: json['reasoning'] ?? '',
        keySignal: json['key_signal'] ?? '',
        confidence: (json['confidence'] ?? 0).toInt(),
      );
}
