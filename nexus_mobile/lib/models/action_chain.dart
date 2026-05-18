class ActionChain {
  final int step;
  final String action;
  final String triggeredBy;
  final String enables;
  final String sideEffect;
  final String monitor;
  final int estimatedCostPkr;
  final int estimatedTimeMinutes;
  String status;
  final bool feasible;
  final bool wasModified;

  ActionChain({
    required this.step,
    required this.action,
    required this.triggeredBy,
    required this.enables,
    required this.sideEffect,
    required this.monitor,
    required this.estimatedCostPkr,
    required this.estimatedTimeMinutes,
    required this.status,
    required this.feasible,
    required this.wasModified,
  });

  factory ActionChain.fromJson(Map<String, dynamic> json) => ActionChain(
        step: (json['step'] ?? 0).toInt(),
        action: json['action'] ?? '',
        triggeredBy: json['triggered_by'] ?? '',
        enables: json['enables'] ?? '',
        sideEffect: json['side_effect'] ?? '',
        monitor: json['monitor'] ?? '',
        estimatedCostPkr: (json['estimated_cost_pkr'] ?? 0).toInt(),
        estimatedTimeMinutes:
            (json['estimated_time_minutes'] ?? json['estimated_time_hours'] ?? 0).toInt(),
        status: json['status'] ?? 'PENDING',
        feasible: json['feasible'] ?? true,
        wasModified: json['was_modified'] ?? false,
      );
}
