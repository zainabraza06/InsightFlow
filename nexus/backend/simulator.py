import random
import time
import logging
from datetime import datetime

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

        before = _snapshot()
        state_store["before_state"] = before
        self.add_log(f"[NEXUS] Chain execution started — {len(chain)} actions — domain: {domain}")

        for action in chain:
            step = action.get("step", 0)
            state_store["current_action"] = action.get("action", "")

            if step == 3 and random.random() < 0.40:
                action["status"] = "FAILED"
                self.add_log(f"[NEXUS] Step 3 FAILED — Mock API timeout after 30s. Transaction rolled back.")
                self.add_log(f"[NEXUS] Initiating recovery protocol. Retry attempt 1 of 2...")
                self.add_log(f"[NEXUS] Step 3 FAILED — API timeout. Rolling back partial state.")
                self.add_log(f"[NEXUS] Recovery: Retry 1 of 2 initiated.")
                self.add_log(f"[NEXUS] Retry succeeded. Chain resuming.")
                self.add_log(f"[NEXUS] Retry 1 succeeded. Resuming chain from step 3.")
                action["status"] = "RECOVERED"
                state_store["actions_failed"] += 1
                state_store["actions_recovered"] += 1

            self.execute_single(action, step)

        after = _snapshot()
        after["status"] = "completed"
        state_store["after_state"] = after
        state_store["status"] = "completed"
        state_store["last_updated"] = datetime.utcnow().isoformat()
        self.add_log(f"[NEXUS] Chain execution complete — cost: PKR {state_store['total_cost_pkr']} — latency: {state_store['total_latency_ms']}ms")

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

    def execute_single(self, action: dict, step: int) -> dict:
        latency = random.randint(120, 480)
        cost = action.get("estimated_cost_pkr", 5000)
        txn_id = f"TXN-{int(time.time())}-S{step}"

        mock = {
            "endpoint": f"/api/nexus/chain/step-{step}",
            "method": "POST",
            "http_status": 200,
            "transaction_id": txn_id,
            "message": f"Step {step} executed: {action.get('action', '')[:80]}",
            "cost_pkr": cost,
            "latency_ms": latency,
            "side_effect_logged": action.get("side_effect", "none"),
            "monitor_metric": action.get("monitor", "none"),
        }

        state_store["actions_completed"] += 1
        state_store["total_cost_pkr"] += cost
        state_store["total_latency_ms"] += latency
        state_store["last_updated"] = datetime.utcnow().isoformat()

        if action.get("status") != "RECOVERED":
            action["status"] = "DONE"

        self.add_log(
            f"[{datetime.utcnow().strftime('%H:%M:%S')}] Step {step} | {txn_id} | PKR {cost} | {latency}ms | {action.get('action', '')[:60]}"
        )
        return mock
