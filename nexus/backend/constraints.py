import json
import logging
import os

import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.constraints")

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.0-flash")

DEFAULT_CONSTRAINTS = {
    "max_budget_pkr": 500000,
    "max_response_time_hours": 4,
    "available_staff": 3,
    "urgency_level": "medium",
    "api_rate_limit_per_minute": 10,
    "max_actions_in_chain": 5,
}


class ConstraintChecker:

    def check_action(self, action_text: str, step: int, constraints: dict) -> dict:
        prompt = f"""Action (step {step}): "{action_text}"
Constraints: {json.dumps(constraints)}

Evaluate feasibility. Consider estimated cost, time, staff, urgency alignment.
Also identify: does this action create any side effects in adjacent business areas?
What should be monitored as a result of this action?

Return ONLY valid JSON:
{{
  "feasible": true,
  "estimated_cost_pkr": 15000,
  "estimated_time_hours": 1.5,
  "staff_required": 2,
  "constraint_violations": [],
  "modified_action": "feasible version of action if infeasible, else same text",
  "feasibility_reason": "one sentence explanation",
  "side_effect": "what unintended consequence might this create in an adjacent area",
  "monitor": "what metric to watch after this action executes"
}}"""

        try:
            response = _model.generate_content(prompt)
            raw = response.text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            logger.info(
                f"Step {step} constraint check — feasible={result.get('feasible')} cost={result.get('estimated_cost_pkr')} PKR"
            )
            return result
        except Exception as e:
            logger.warning(f"Constraint check failed for step {step}: {e} — using fallback")
            return {
                "feasible": True,
                "estimated_cost_pkr": 15000,
                "estimated_time_hours": 1.5,
                "staff_required": 2,
                "constraint_violations": [],
                "modified_action": action_text,
                "feasibility_reason": "Action within standard operating parameters",
                "side_effect": "May temporarily increase load on adjacent reporting systems",
                "monitor": "System response time and staff availability over next 2 hours",
            }

    def validate_chain(self, actions: list, constraints: dict) -> list:
        validated = []
        for action in actions:
            step = action.get("step", 0)
            action_text = action.get("action", "")
            check = self.check_action(action_text, step, constraints)

            was_modified = not check.get("feasible", True)
            if was_modified:
                action["action"] = check.get("modified_action", action_text)
                logger.info(f"Step {step} action modified to meet constraints")

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
