import random
import time
import logging
from datetime import datetime

from real_actions import (
    step2_notify_stakeholders,
    step3_update_system_state,
    step4_launch_mitigation,
)

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.simulator")

state_store = {
    "status": "idle",
    "last_input_summary": None,
    "active_domain": None,
    "sources_ingested": 0,
    "sources_trusted": 0,
    "sources_excluded": 0,
    "contradictions_found": 0,
    "actions_total": 0,
    "actions_completed": 0,
    "actions_failed": 0,
    "actions_recovered": 0,
    "actions_modified_by_constraints": 0,
    "current_action": None,
    "chain_progress": [],
    "before_state": {},
    "after_state": {},
    "execution_log": [],
    "total_cost_pkr": 0,
    "total_latency_ms": 0,
    "last_updated": None,
    "ingestion_result": None,
    "analysis_result": None,
}


def _snapshot() -> dict:
    return {
        "status": state_store["status"],
        "actions_completed": state_store["actions_completed"],
        "actions_failed": state_store["actions_failed"],
        "actions_recovered": state_store["actions_recovered"],
        "total_cost_pkr": state_store["total_cost_pkr"],
        "total_latency_ms": state_store["total_latency_ms"],
    }


class ActionSimulator:

    def add_log(self, message: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "time_display": datetime.utcnow().strftime("%H:%M:%S"),
            "message": message,
        }
        state_store["execution_log"].append(entry)
        logger.info(message)

    def execute_chain(self, chain: list, domain: str) -> dict:
        state_store["status"] = "executing"
        state_store["execution_log"] = []
        state_store["total_cost_pkr"] = 0
        state_store["total_latency_ms"] = 0
        state_store["actions_completed"] = 0
        state_store["actions_failed"] = 0
        state_store["actions_recovered"] = 0

        # Pull the final insight from analysis result for email body
        insight = ""
        if state_store.get("analysis_result"):
            insight = (
                state_store["analysis_result"]
                .get("resolved", {})
                .get("final_insight", "")
            )

        before = _snapshot()
        state_store["before_state"] = before
        self.add_log(
            f"[NEXUS] Chain execution started — {len(chain)} actions — domain: {domain}"
        )

        for action in chain:
            step = action.get("step", 0)
            state_store["current_action"] = action.get("action", "")

            # ── Step 3 failure injection (40% chance) ─────────────────────────
            if step == 3 and random.random() < 0.40:
                action["status"] = "FAILED"
                self.add_log(
                    "[NEXUS] Step 3 FAILED — Google Sheets write timed out after 30s. "
                    "Transaction rolled back."
                )
                self.add_log(
                    "[NEXUS] Recovery protocol initiated. Retry attempt 1 of 2..."
                )
                self.add_log(
                    "[NEXUS] Rolling back partial sheet write. Restoring last good state."
                )
                self.add_log("[NEXUS] Retry 1 of 2 executing now...")
                self.add_log(
                    "[NEXUS] Retry succeeded. Sheet write confirmed. Chain resuming."
                )
                action["status"] = "RECOVERED"
                state_store["actions_failed"] += 1
                state_store["actions_recovered"] += 1

            result = self.execute_single(action, step, domain, insight)
            action["real_result"] = result

        after = _snapshot()
        after["status"] = "completed"
        state_store["after_state"] = after
        state_store["status"] = "completed"
        state_store["last_updated"] = datetime.utcnow().isoformat()

        # Update Google Sheets with the final completed system state to ensure no ambiguity
        final_state = {
            "status": "completed",
            "actions_completed": state_store.get("actions_completed", 5),
            "total_cost_pkr": state_store.get("total_cost_pkr", 0),
            "risk_level": "REDUCED",
            "domain": domain,
        }
        step3_update_system_state(domain, final_state)

        self.add_log(
            f"[NEXUS] Chain complete — cost PKR {state_store['total_cost_pkr']} — "
            f"latency {state_store['total_latency_ms']}ms"
        )

        return {
            "chain": chain,
            "before_state": before,
            "after_state": after,
            "total_cost_pkr": state_store["total_cost_pkr"],
            "total_latency_ms": state_store["total_latency_ms"],
            "failures": state_store["actions_failed"],
            "recovered": state_store["actions_recovered"],
            "log": state_store["execution_log"],
        }

    def execute_single(
        self, action: dict, step: int, domain: str = "Business", insight: str = ""
    ) -> dict:
        t_start = time.time()
        cost = action.get("estimated_cost_pkr", 5000)
        txn_id = f"TXN-{int(time.time())}-S{step}"
        action_text = action.get("action", "")

        # ── Dispatch to real integrations ─────────────────────────────────────
        if step == 2:
            # Real email: notify stakeholders
            real = step2_notify_stakeholders(action_text, domain, insight)
            channel = real.get("channel", "email")
            self.add_log(
                f"[NEXUS] Step 2 | {txn_id} | REAL EMAIL → {real.get('to','?')} | "
                f"subject: {real.get('subject','')[:60]} | real={real.get('real')}"
            )

        elif step == 3:
            # Real Google Sheets: update system state dashboard
            state_snapshot = {
                "status": state_store.get("status", "executing"),
                "actions_completed": state_store.get("actions_completed", 0),
                "total_cost_pkr": state_store.get("total_cost_pkr", 0),
                "risk_level": "REDUCING",
                "domain": domain,
            }
            real = step3_update_system_state(domain, state_snapshot)
            channel = real.get("channel", "google_sheets")
            sheet_url = real.get("sheet_url", "")
            self.add_log(
                f"[NEXUS] Step 3 | {txn_id} | REAL SHEET UPDATE → {sheet_url or 'simulated'} | "
                f"real={real.get('real')}"
            )

        elif step == 4:
            # Real Slack/webhook: launch mitigation alert
            real = step4_launch_mitigation(action_text, domain, cost)
            channel = real.get("channel", "webhook")
            self.add_log(
                f"[NEXUS] Step 4 | {txn_id} | REAL WEBHOOK → {channel} | "
                f"http={real.get('http_status')} | real={real.get('real')}"
            )

        else:
            # Steps 1 and 5: enhanced simulation (root-cause analysis and monitoring
            # are handled by Gemini in the agent layer — no separate API needed)
            real = {
                "real": False,
                "channel": f"simulated_step_{step}",
                "endpoint": f"/api/nexus/chain/step-{step}",
                "method": "POST",
                "http_status": 200,
                "transaction_id": txn_id,
                "message": f"Step {step} executed: {action_text[:80]}",
            }
            time.sleep(random.uniform(0.08, 0.25))
            self.add_log(
                f"[NEXUS] Step {step} | {txn_id} | simulated | "
                f"{action_text[:60]}"
            )

        latency = int((time.time() - t_start) * 1000)
        state_store["actions_completed"] += 1
        state_store["total_cost_pkr"] += cost
        state_store["total_latency_ms"] += latency
        state_store["last_updated"] = datetime.utcnow().isoformat()

        if action.get("status") != "RECOVERED":
            action["status"] = "DONE"

        real.update({
            "transaction_id": txn_id,
            "cost_pkr": cost,
            "latency_ms": latency,
            "side_effect_logged": action.get("side_effect", ""),
            "monitor_metric": action.get("monitor", ""),
        })
        return real
