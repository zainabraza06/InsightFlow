import logging

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.constraints")

DEFAULT_CONSTRAINTS = {
    "max_budget_pkr": 500000,
    "max_response_time_hours": 4,
    "available_staff": 3,
    "urgency_level": "medium",
    "api_rate_limit_per_minute": 10,
    "max_actions_in_chain": 5,
}

_URGENCY_MULTIPLIER = {"low": 1.5, "medium": 1.0, "high": 0.7, "critical": 0.4}


class ConstraintChecker:

    def check_action(self, action: dict, step: int, constraints: dict) -> dict:
        budget = constraints.get("budget_pkr") or constraints.get("max_budget_pkr", 500_000)
        max_hours = constraints.get("max_response_time_hours", 4)
        staff_limit = constraints.get("max_staff") or constraints.get("available_staff", 3)
        urgency = constraints.get("urgency", constraints.get("urgency_level", "medium"))

        per_step_budget = budget / 5
        time_mult = _URGENCY_MULTIPLIER.get(urgency, 1.0)
        per_step_hours = (max_hours / 5) * time_mult

        # Use the action's actual cost/time — check them against constraints
        cost = action.get("estimated_cost_pkr", 0)
        time_minutes = action.get("estimated_time_minutes", 0)
        time_hours = round(time_minutes / 60, 2)
        staff = action.get("staff_required", 1)

        violations = []
        if cost > per_step_budget:
            violations.append(
                f"Cost PKR {cost:,} exceeds per-step budget PKR {per_step_budget:,.0f}"
            )
        if time_hours > per_step_hours * time_mult:
            violations.append(
                f"Time {time_hours:.1f}h exceeds allocation {per_step_hours * time_mult:.1f}h"
            )
        if staff > staff_limit:
            violations.append(f"Staff {staff} exceeds limit {staff_limit}")

        feasible = len(violations) == 0
        action_text = action.get("action", "")
        logger.info(f"Step {step} constraint check — feasible={feasible} cost=PKR {cost:,}")
        return {
            "feasible": feasible,
            "estimated_cost_pkr": cost,
            "estimated_time_hours": time_hours,
            "staff_required": staff,
            "constraint_violations": violations,
            "modified_action": action_text,
            "feasibility_reason": "Within constraints" if feasible else "; ".join(violations),
            "side_effect": action.get("side_effect", "May temporarily increase load on adjacent systems"),
            "monitor": action.get("monitor", "Completion time and resource utilisation vs plan"),
        }

    def validate_chain(self, actions: list, constraints: dict) -> list:
        validated = []
        for action in actions:
            step = action.get("step", 0)
            check = self.check_action(action, step, constraints)

            was_modified = not check.get("feasible", True)
            if was_modified:
                logger.info(f"Step {step} action flagged — constraints violated: {check['constraint_violations']}")

            action.update({
                "feasible": check.get("feasible", True),
                "estimated_cost_pkr": check.get("estimated_cost_pkr", action.get("estimated_cost_pkr", 15000)),
                "estimated_time_hours": check.get("estimated_time_hours", 1.5),
                "staff_required": check.get("staff_required", 2),
                "constraint_violations": check.get("constraint_violations", []),
                "feasibility_reason": check.get("feasibility_reason", ""),
                "side_effect": check.get("side_effect", action.get("side_effect", "")),
                "monitor": check.get("monitor", action.get("monitor", "")),
                "was_modified": was_modified,
            })
            validated.append(action)
        return validated
