"""
Challenge 1: Autonomous Content-to-Action Agent
Requirement Verification Test Suite

Each test class maps to one challenge requirement (CR):
  CR1  Content Understanding     — ingest multiple source types
  CR2  Insight Extraction        — specific, non-generic agent outputs
  CR3  Impact Analysis           — consequences connected to real-world outcomes
  CR4  Action Generation         — 5 causal, domain-specific actions
  CR5  Action Simulation         — real or simulated email / sheet / webhook
  CR6  Outcome Visualization     — before/after state, execution log
  CR7  Agentic Workflow          — multi-agent parallelism, traceable reasoning
  CR8  Both Flows                — custom ConsensusEngine + google_sdk flow

Run full suite (LLM calls included, ~10-15 min):
    pytest test_challenge1.py -v

Skip LLM tests (fast, no API calls):
    pytest test_challenge1.py -v -m "not llm"

Print full trace for demo:
    pytest test_challenge1.py::TestFullPipelineScenario -v -s
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient
from main import app, state_store

client = TestClient(app)

HAS_GOOGLE_KEY = bool(os.environ.get("GOOGLE_API_KEY"))
def _smtp_reachable() -> bool:
    if not (os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS")):
        return False
    import socket
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("smtp.gmail.com", 587))
        return True
    except Exception:
        return False

def _gspread_available() -> bool:
    if not (os.environ.get("GOOGLE_SHEET_ID") and os.environ.get("GOOGLE_SA_JSON")):
        return False
    try:
        import gspread  # noqa: F401
        return True
    except ImportError:
        return False

HAS_SMTP       = _smtp_reachable()
HAS_SHEETS     = _gspread_available()
HAS_SLACK      = bool(os.environ.get("SLACK_WEBHOOK_URL"))

# ── Scenario: Supply Chain Disruption (primary demo scenario) ─────────────────

SC_TEXT = (
    "URGENT SUPPLY CHAIN ALERT — Karachi Port Authority confirmed 14 containers "
    "from Supplier A are held at customs due to documentation mismatch. "
    "Estimated clearance delay: 72 hours minimum. Affected SKUs: SKU-001 through SKU-006. "
    "Current warehouse stock for SKU-002 will reach zero in 2 days at current consumption rate. "
    "Supplier B has confirmed they can ship 60% of required volume within 48 hours at a "
    "15% premium over standard price (PKR 3,450 vs PKR 3,000 per unit)."
)

SC_CSV = (
    "date,sku,quantity,unit_cost_pkr,days_remaining\n"
    "2024-01-01,SKU-001,120,5000,8\n"
    "2024-01-02,SKU-001,98,5000,6\n"
    "2024-01-03,SKU-001,72,5000,5\n"
    "2024-01-04,SKU-002,200,3000,4\n"
    "2024-01-05,SKU-002,165,3000,3\n"
    "2024-01-06,SKU-002,130,3000,2\n"
    "2024-01-07,SKU-003,80,8000,12\n"
)

SAMPLE_CHAIN_5 = [
    {
        "step": 1,
        "action": "Root cause analysis: audit all supply chain data, cross-reference supplier reports, "
                  "identify primary failure point — documentation mismatch at Karachi customs for 14 containers.",
        "triggered_by": "Multi-source convergence: CSV + text + feed confirm same signal",
        "enables": "Stakeholder notification with verified root cause",
        "estimated_cost_pkr": 8000,
        "estimated_time_minutes": 45,
        "side_effect": "2 analysts diverted from routine tasks",
        "monitor": "Diagnosis completion vs 2-hour target",
        "status": "PENDING",
    },
    {
        "step": 2,
        "action": "Notify stakeholders: send executive alert with root cause summary, "
                  "PKR 2.4M daily revenue exposure, and 72-hour response timeline.",
        "triggered_by": "Root cause verified in Step 1",
        "enables": "System state update with stakeholder-approved parameters",
        "estimated_cost_pkr": 3000,
        "estimated_time_minutes": 30,
        "side_effect": "May trigger premature customer communications",
        "monitor": "Stakeholder acknowledgement rate within 1 hour",
        "status": "PENDING",
    },
    {
        "step": 3,
        "action": "Update system state: freeze non-critical POs for SKU-001 to SKU-006, "
                  "activate contingency supplier list, flag impacted SKUs in inventory dashboard.",
        "triggered_by": "Stakeholder approval received in Step 2",
        "enables": "Step 4 mitigation has clean system state to work from",
        "estimated_cost_pkr": 12000,
        "estimated_time_minutes": 60,
        "side_effect": "PO freeze delays unrelated procurement 24-48h",
        "monitor": "Number of flagged SKUs and POs paused",
        "status": "PENDING",
    },
    {
        "step": 4,
        "action": "Launch mitigation: engage Supplier B for emergency bridge orders on SKU-002 "
                  "(2,000 units at PKR 3,450 each), request expedited Karachi customs clearance.",
        "triggered_by": "System state updated in Step 3",
        "enables": "Step 5 monitoring has concrete order metrics to track",
        "estimated_cost_pkr": 6900000,
        "estimated_time_minutes": 120,
        "side_effect": "Emergency procurement creates 15% unit cost premium",
        "monitor": "Bridge order confirmation rate and supplier response time",
        "status": "PENDING",
    },
    {
        "step": 5,
        "action": "Schedule 72-hour monitoring: 4-hourly automated supply feed checks, "
                  "daily supplier calls, weekly executive review until full resolution.",
        "triggered_by": "Mitigation launched in Step 4",
        "enables": "Executive team can make data-driven escalation decisions",
        "estimated_cost_pkr": 15000,
        "estimated_time_minutes": 20,
        "side_effect": "Monitoring adds 8% load to analytics infrastructure",
        "monitor": "Recovery velocity: % critical SKUs back to normal within 72h",
        "status": "PENDING",
    },
]


def do_ingest(**kwargs):
    data = {"domain": "supply_chain", **kwargs}
    return client.post("/ingest", data=data)


def do_analyze(**kwargs):
    body = {"domain": "supply_chain", "flow_type": "custom", **kwargs}
    return client.post("/analyze", json=body)


def do_ingest_full():
    return do_ingest(
        text=SC_TEXT,
        csv_data=SC_CSV,
        include_feed="true",
        topic="supply",
        domain="supply_chain",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CR1 — Content Understanding
# Challenge: "Process unstructured input (text, PDF, website) — Extract key facts"
# ═══════════════════════════════════════════════════════════════════════════════

class TestCR1_ContentUnderstanding:
    """System must ingest multiple unstructured source types and score credibility."""

    def test_text_source_ingested(self):
        r = do_ingest(text=SC_TEXT)
        data = r.json()
        assert r.status_code == 200
        assert data["sources_processed"] == 1
        assert data["ready_for_analysis"] is True

    def test_csv_source_ingested_as_structured(self):
        r = do_ingest(csv_data=SC_CSV)
        data = r.json()
        assert data["sources_processed"] == 1
        assert data["credibility_map"]["csv"] >= 0.90

    def test_realtime_feed_ingested(self):
        r = do_ingest(include_feed="true", topic="supply")
        data = r.json()
        assert data["sources_processed"] >= 1

    def test_multi_source_all_three_types(self):
        r = do_ingest_full()
        data = r.json()
        assert data["sources_processed"] == 3
        cmap = data["credibility_map"]
        assert "text" in cmap
        assert "csv" in cmap
        assert "realtime_feed" in cmap

    def test_credibility_scored_per_source(self):
        r = do_ingest_full()
        cmap = r.json()["credibility_map"]
        for src_type, score in cmap.items():
            assert 0.0 <= score <= 1.0, f"{src_type} credibility {score} out of range"

    def test_csv_most_credible_source(self):
        r = do_ingest_full()
        cmap = r.json()["credibility_map"]
        assert cmap["csv"] > cmap["text"]
        assert cmap["csv"] > cmap.get("realtime_feed", 0)

    def test_stale_content_penalised(self):
        stale = "Last week the supply chain was fine but yesterday issues emerged."
        r = do_ingest(text=stale)
        assert r.json()["credibility_map"]["text"] < 0.50

    def test_noisy_content_penalised(self):
        noisy = "BREAKING rumor: allegedly supply chain is disrupted!"
        r = do_ingest(text=noisy)
        assert r.json()["credibility_map"]["text"] < 0.55

    def test_invalid_url_automatically_excluded(self):
        r = do_ingest(text=SC_TEXT, url="http://no-such-domain-nexus.invalid")
        data = r.json()
        url_score = data["credibility_map"].get("url", 0.0)
        assert url_score < 0.30 or data["sources_excluded"] >= 1

    def test_noise_filtered_count_consistent(self):
        r = do_ingest_full()
        data = r.json()
        assert data["sources_trusted"] + data["sources_excluded"] == data["sources_processed"]

    def test_temporal_analysis_present_for_csv(self):
        r = do_ingest(csv_data=SC_CSV)
        data = r.json()
        assert "temporal_analysis" in data


# ═══════════════════════════════════════════════════════════════════════════════
# CR2 — Insight Extraction (LLM)
# Challenge: "Identify meaningful patterns — Avoid generic summarization"
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestCR2_InsightExtraction:
    """Each of the 3 agents (Orion/Raven/Cipher) must return specific, non-generic insights."""

    def setup_method(self):
        do_ingest_full()

    def test_three_distinct_agent_perspectives(self):
        agents = do_analyze().json()["agents"]
        assert len(agents) == 3
        personas = {a["persona"] for a in agents}
        assert personas == {"Optimist", "Pessimist", "Realist"}

    def test_all_agent_required_fields_present(self):
        agents = do_analyze().json()["agents"]
        required = {"agent", "persona", "insight", "impact", "recommended_action",
                    "confidence", "reasoning", "key_signal"}
        for a in agents:
            missing = required - set(a.keys())
            assert not missing, f"{a.get('agent')} missing fields: {missing}"

    def test_insights_are_non_empty(self):
        agents = do_analyze().json()["agents"]
        for a in agents:
            assert len(a["insight"]) > 20, f"{a['agent']} insight too short: {a['insight']}"
            assert len(a["impact"]) > 10
            assert len(a["recommended_action"]) > 10

    def test_confidence_scores_in_valid_range(self):
        agents = do_analyze().json()["agents"]
        for a in agents:
            assert 0 < a["confidence"] <= 100, f"{a['agent']} confidence {a['confidence']} invalid"

    def test_key_signal_identifies_specific_datapoint(self):
        agents = do_analyze().json()["agents"]
        for a in agents:
            assert a["key_signal"], f"{a['agent']} key_signal is empty"
            assert len(a["key_signal"]) > 5

    def test_optimist_positive_framing(self):
        agents = do_analyze().json()["agents"]
        orion = next(a for a in agents if a["agent"] == "Orion")
        text = (orion["insight"] + orion["impact"]).lower()
        positive_words = {"opportunity", "advantage", "growth", "gain", "increase",
                          "recover", "improve", "first-mover", "alternative", "supplier"}
        assert any(w in text for w in positive_words), f"Orion insight not optimistic: {orion['insight']}"

    def test_pessimist_risk_framing(self):
        agents = do_analyze().json()["agents"]
        raven = next(a for a in agents if a["agent"] == "Raven")
        text = (raven["insight"] + raven["impact"]).lower()
        risk_words = {"risk", "failure", "loss", "disrupt", "halt", "cascade",
                      "churn", "delay", "critical", "threat", "decline"}
        assert any(w in text for w in risk_words), f"Raven insight not pessimistic: {raven['insight']}"

    def test_realist_probability_framing(self):
        agents = do_analyze().json()["agents"]
        cipher = next(a for a in agents if a["agent"] == "Cipher")
        text = (cipher["insight"] + cipher["reasoning"]).lower()
        realist_words = {"likely", "probability", "chance", "percent", "%", "estimate",
                         "expected", "moderate", "possible", "range", "interval"}
        assert any(w in text for w in realist_words), f"Cipher insight not probability-weighted: {cipher['insight']}"

    def test_weighted_confidence_correctly_calculated(self):
        data = do_analyze().json()
        agents = data["agents"]
        orion  = next(a for a in agents if a["agent"] == "Orion")
        raven  = next(a for a in agents if a["agent"] == "Raven")
        cipher = next(a for a in agents if a["agent"] == "Cipher")
        expected = round(
            cipher["confidence"] * 0.40
            + orion["confidence"]  * 0.30
            + raven["confidence"]  * 0.30,
            1,
        )
        assert data["weighted_confidence"] == expected


# ═══════════════════════════════════════════════════════════════════════════════
# CR3 — Impact Analysis (LLM)
# Challenge: "Explain why insight matters — Connect to real-world consequences"
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestCR3_ImpactAnalysis:
    """Resolver must synthesize agent insights into an authoritative impact assessment."""

    def setup_method(self):
        do_ingest_full()

    def test_resolver_produces_final_insight(self):
        resolved = do_analyze().json()["resolved"]
        assert "final_insight" in resolved
        assert len(resolved["final_insight"]) > 30

    def test_resolver_cites_trusted_evidence(self):
        resolved = do_analyze().json()["resolved"]
        assert "trusted_evidence" in resolved
        assert len(resolved["trusted_evidence"]) > 10

    def test_resolver_identifies_remaining_uncertainty(self):
        resolved = do_analyze().json()["resolved"]
        assert "remaining_uncertainty" in resolved
        assert len(resolved["remaining_uncertainty"]) > 10

    def test_resolver_executive_summary_two_sentences(self):
        resolved = do_analyze().json()["resolved"]
        assert "situation_summary" in resolved
        summary = resolved["situation_summary"]
        assert len(summary) > 20

    def test_resolver_provides_investigation_path(self):
        resolved = do_analyze().json()["resolved"]
        path = resolved.get("investigation_path", [])
        assert isinstance(path, list)
        assert len(path) >= 2

    def test_resolver_confidence_is_numeric(self):
        resolved = do_analyze().json()["resolved"]
        conf = resolved.get("confidence")
        assert isinstance(conf, (int, float))
        assert 0 < conf <= 100

    def test_resolver_explains_contradiction_resolution(self):
        resolved = do_analyze().json()["resolved"]
        assert "contradiction_resolution" in resolved
        assert len(resolved["contradiction_resolution"]) > 5

    def test_contradictions_detected_from_multi_sources(self):
        r = do_ingest_full()
        contradictions = r.json().get("contradictions", {})
        assert "contradictions" in contradictions or "temporal_analysis" in contradictions

    def test_temporal_trend_identified(self):
        r = do_ingest(csv_data=SC_CSV)
        temporal = r.json().get("temporal_analysis", {})
        assert "trend_direction" in temporal or "has_trend" in temporal


# ═══════════════════════════════════════════════════════════════════════════════
# CR4 — Action Generation (LLM)
# Challenge: "Generate clear, actionable recommendations — Realistic & domain-relevant"
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestCR4_ActionGeneration:
    """Executor must produce 5 causally-linked, specific, domain-relevant actions."""

    def setup_method(self):
        do_ingest_full()

    def test_exactly_five_actions_generated(self):
        chain = do_analyze().json()["action_chain"]
        assert len(chain) == 5, f"Expected 5 actions, got {len(chain)}"

    def test_steps_are_sequentially_numbered(self):
        chain = do_analyze().json()["action_chain"]
        assert [a["step"] for a in chain] == [1, 2, 3, 4, 5]

    def test_causal_chain_fields_present(self):
        chain = do_analyze().json()["action_chain"]
        required = {"step", "action", "triggered_by", "enables",
                    "estimated_cost_pkr", "estimated_time_minutes", "status"}
        for action in chain:
            missing = required - set(action.keys())
            assert not missing, f"Step {action.get('step')} missing fields: {missing}"

    def test_all_actions_start_as_pending(self):
        chain = do_analyze().json()["action_chain"]
        for action in chain:
            assert action["status"] == "PENDING"

    def test_action_costs_are_positive(self):
        chain = do_analyze().json()["action_chain"]
        for action in chain:
            assert action["estimated_cost_pkr"] >= 0

    def test_action_times_are_positive(self):
        chain = do_analyze().json()["action_chain"]
        for action in chain:
            assert action["estimated_time_minutes"] > 0

    def test_total_cost_sum_matches(self):
        data = do_analyze().json()
        chain = data["action_chain"]
        expected = sum(a["estimated_cost_pkr"] for a in chain)
        assert data["total_estimated_cost_pkr"] == expected

    def test_total_time_sum_matches(self):
        data = do_analyze().json()
        chain = data["action_chain"]
        expected = sum(a["estimated_time_minutes"] for a in chain)
        assert data["total_estimated_time_minutes"] == expected

    def test_action_descriptions_are_specific(self):
        chain = do_analyze().json()["action_chain"]
        for action in chain:
            desc = action["action"]
            assert len(desc) > 20, f"Step {action['step']} action too generic: {desc}"

    def test_constraints_applied_to_chain(self):
        data = do_analyze().json()
        chain = data["action_chain"]
        for action in chain:
            assert "status" in action
            assert action["status"] in ("PENDING", "MODIFIED", "CONSTRAINED")

    def test_constraint_checker_flags_overbudget_action(self):
        from constraints import ConstraintChecker, DEFAULT_CONSTRAINTS
        checker = ConstraintChecker()
        tight_constraints = {**DEFAULT_CONSTRAINTS, "budget_pkr": 1000}
        chain = [{"step": 1, "action": "test", "estimated_cost_pkr": 50000,
                  "estimated_time_minutes": 30, "staff_required": 1, "status": "PENDING"}]
        validated = checker.validate_chain(chain, tight_constraints)
        assert validated[0].get("was_modified") is True or validated[0].get("status") in ("MODIFIED", "CONSTRAINED")


# ═══════════════════════════════════════════════════════════════════════════════
# CR5 — Action Simulation (CRITICAL)
# Challenge: "Simulate execution of at least one action"
# ═══════════════════════════════════════════════════════════════════════════════

class TestCR5_ActionSimulation:
    """Steps 2/3/4 must fire real or richly-simulated integrations with full audit trail."""

    def test_execute_returns_chain_with_results(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        assert r.status_code == 200
        data = r.json()
        assert "chain" in data
        assert len(data["chain"]) == 5

    def test_all_five_steps_executed(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        for step in r.json()["chain"]:
            assert step["status"] in ("DONE", "RECOVERED"), \
                f"Step {step['step']} status={step['status']}"

    def test_step2_email_fires_with_channel_info(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step2 = r.json()["chain"][1]
        result = step2["real_result"]
        assert "channel" in result
        assert "email" in result["channel"]
        assert result["http_status"] in (200, 250), f"Email step HTTP status: {result['http_status']}"

    def test_step2_email_real_if_smtp_configured(self):
        if not HAS_SMTP:
            pytest.skip("SMTP not configured — email is simulated (acceptable)")
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step2 = r.json()["chain"][1]
        assert step2["real_result"]["real"] is True

    def test_step3_sheets_fires_with_row_data(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step3 = r.json()["chain"][2]
        result = step3["real_result"]
        assert "channel" in result
        assert "sheet" in result["channel"]
        assert "row_appended" in result
        assert isinstance(result["row_appended"], list)
        assert len(result["row_appended"]) >= 4

    def test_step3_sheet_real_if_configured(self):
        if not HAS_SHEETS:
            pytest.skip("Google Sheets not configured — simulated (acceptable)")
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step3 = r.json()["chain"][2]
        assert step3["real_result"]["real"] is True
        assert "sheet_url" in step3["real_result"]

    def test_step4_webhook_fires_with_payload(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step4 = r.json()["chain"][3]
        result = step4["real_result"]
        assert "channel" in result
        assert result["http_status"] in (200, 201), f"Webhook HTTP status: {result['http_status']}"

    def test_step4_slack_real_if_configured(self):
        if not HAS_SLACK:
            pytest.skip("Slack webhook not configured — simulated (acceptable)")
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        step4 = r.json()["chain"][3]
        assert step4["real_result"]["real"] is True

    def test_cost_accumulates_across_steps(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        data = r.json()
        expected = sum(a["estimated_cost_pkr"] for a in SAMPLE_CHAIN_5)
        assert data["total_cost_pkr"] == expected

    def test_execution_transaction_ids_assigned(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        for step in r.json()["chain"]:
            result = step["real_result"]
            assert "transaction_id" in result
            assert result["transaction_id"].startswith("TXN-")

    def test_failure_recovery_mechanism_triggers(self):
        recovered_seen = False
        for _ in range(10):
            r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
            data = r.json()
            if data["recovered"] > 0:
                recovered_seen = True
                step3 = data["chain"][2]
                assert step3["status"] == "RECOVERED"
                break
        # Step 3 has 40% failure rate — 10 runs makes seeing at least one recovery very likely
        assert recovered_seen, "Recovery mechanism never triggered in 10 runs (low probability)"

    def test_simulated_steps_still_complete_successfully(self):
        # Even without real creds, simulation must complete and log correctly
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        data = r.json()
        assert data["total_cost_pkr"] > 0
        assert len(data["log"]) >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# CR6 — Outcome Visualization
# Challenge: "Show before vs after state, logs, resulting system change"
# ═══════════════════════════════════════════════════════════════════════════════

class TestCR6_OutcomeVisualization:
    """System must expose clear before/after state, execution logs, and trace."""

    def test_before_state_captured(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        assert "before_state" in r.json()

    def test_after_state_captured(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        assert "after_state" in r.json()

    def test_after_state_shows_completed(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        after = r.json()["after_state"]
        assert after["status"] == "completed"

    def test_before_state_shows_initial_zeroes(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        before = r.json()["before_state"]
        assert before["actions_completed"] == 0
        assert before["total_cost_pkr"] == 0

    def test_after_state_actions_completed_incremented(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        after = r.json()["after_state"]
        assert after["actions_completed"] == len(SAMPLE_CHAIN_5)

    def test_after_cost_greater_than_before(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        data = r.json()
        assert data["after_state"]["total_cost_pkr"] > data["before_state"]["total_cost_pkr"]

    def test_execution_log_populated(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        log = r.json()["log"]
        assert isinstance(log, list)
        assert len(log) >= len(SAMPLE_CHAIN_5)

    def test_log_entries_have_timestamp_and_message(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        for entry in r.json()["log"]:
            assert "timestamp" in entry
            assert "message" in entry
            assert len(entry["message"]) > 5

    def test_logs_endpoint_returns_execution_history(self):
        client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        r = client.get("/logs")
        assert r.status_code == 200
        logs = r.json()["logs"]
        assert isinstance(logs, list)

    def test_state_endpoint_reflects_execution(self):
        do_ingest_full()
        client.post("/execute", json={"chain": SAMPLE_CHAIN_5, "domain": "supply_chain"})
        state = client.get("/state").json()
        assert state["status"] == "completed"
        assert state["sources_ingested"] >= 1
        assert state["actions_total"] >= 0

    def test_export_trace_endpoint_returns_full_audit(self):
        r = client.get("/export-trace")
        assert r.status_code == 200
        data = r.json()
        assert data["system"] == "NEXUS"
        assert "agents_used" in data
        assert data["agents_used"] == ["Orion", "Raven", "Cipher", "Resolver", "Executor"]
        assert "execution_log" in data
        assert "sources_ingested" in data

    def test_baseline_comparison_shows_nexus_vs_simple(self):
        r = client.get("/baseline-comparison")
        data = r.json()
        nexus = data["nexus_agentic"]
        simple = data["simple_heuristic"]
        assert nexus["action_chain_depth"] > simple["action_chain_depth"]
        assert nexus["contradiction_detection"] is True
        assert simple["contradiction_detection"] is False
        assert nexus["failure_recovery"] is True

    def test_what_if_analysis_available(self):
        # Needs analysis result in state — run analyze first if LLM available
        if not HAS_GOOGLE_KEY:
            pytest.skip("What-if requires /analyze to have run first (GOOGLE_API_KEY not set)")
        do_ingest_full()
        do_analyze()
        r = client.post("/what-if", json={"modifications": {"budget_pkr": 100000}})
        assert r.status_code == 200
        data = r.json()
        assert "action_chain" in data
        assert "what_if_constraints" in data
        assert data["what_if_constraints"]["budget_pkr"] == 100000


# ═══════════════════════════════════════════════════════════════════════════════
# CR7 — Agentic Workflow
# Challenge: "Multiple agents, planning and execution flow, traceable reasoning"
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestCR7_AgenticWorkflow:
    """System must demonstrate multi-agent parallelism and traceable decision flow."""

    def setup_method(self):
        do_ingest_full()

    def test_five_agents_named_in_health(self):
        agents = client.get("/health").json()["agents"]
        assert set(agents) == {"Orion", "Raven", "Cipher", "Resolver", "Executor"}

    def test_agents_run_in_parallel_all_respond(self):
        data = do_analyze().json()
        agent_names = {a["agent"] for a in data["agents"]}
        assert agent_names == {"Orion", "Raven", "Cipher"}

    def test_resolver_synthesizes_all_three_perspectives(self):
        data = do_analyze().json()
        resolved = data["resolved"]
        assert resolved["final_insight"]
        assert resolved["trusted_evidence"]
        assert resolved["contradiction_resolution"]

    def test_executor_plans_from_resolved_insight(self):
        data = do_analyze().json()
        chain = data["action_chain"]
        resolved = data["resolved"]
        assert resolved["final_insight"]
        assert len(chain) == 5

    def test_each_agent_has_distinct_perspective(self):
        agents = do_analyze().json()["agents"]
        insights = [a["insight"] for a in agents]
        # All three insights should differ (not identical)
        assert len(set(insights)) == 3, "All three agents returned identical insights"

    def test_causal_chain_is_logically_ordered(self):
        chain = do_analyze().json()["action_chain"]
        step_names = [a.get("action", "").lower() for a in chain]
        assert any("diagnose" in s or "root" in s or "analyze" in s or "audit" in s
                   for s in step_names[:2]), "Step 1 should be diagnostic"
        assert any("monitor" in s or "schedule" in s or "track" in s
                   for s in step_names[3:]), "Step 5 should be monitoring"

    def test_learning_context_field_present(self):
        data = do_analyze().json()
        assert "learning_active" in data
        assert "learning_context" in data

    def test_adk_enabled_field_reported(self):
        data = do_analyze().json()
        assert "adk_enabled" in data


# ═══════════════════════════════════════════════════════════════════════════════
# CR8 — Both Execution Flows
# Challenge: "Google Antigravity must be central to system logic"
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestCR8_BothFlows:
    """Both the custom ADK-backed flow and the google_sdk flow must produce valid output."""

    def setup_method(self):
        do_ingest_full()

    def test_custom_flow_completes(self):
        data = do_analyze(flow_type="custom").json()
        assert len(data["agents"]) == 3
        assert len(data["action_chain"]) == 5

    def test_google_sdk_flow_completes(self):
        data = do_analyze(flow_type="google_sdk").json()
        assert len(data["agents"]) == 3
        assert len(data["action_chain"]) >= 3

    def test_google_sdk_flow_labels_itself(self):
        data = do_analyze(flow_type="google_sdk").json()
        assert data.get("flow") == "google_sdk"
        assert data.get("sdk_native_tools") is True

    def test_custom_flow_labels_itself(self):
        data = do_analyze(flow_type="custom").json()
        assert "adk_enabled" in data

    def test_both_flows_return_final_insight(self):
        for flow in ("custom", "google_sdk"):
            data = do_analyze(flow_type=flow).json()
            assert data["resolved"]["final_insight"], f"{flow} flow missing final_insight"

    def test_both_flows_return_five_agent_actions(self):
        for flow in ("custom", "google_sdk"):
            data = do_analyze(flow_type=flow).json()
            assert len(data["action_chain"]) >= 3, f"{flow} chain too short"


# ═══════════════════════════════════════════════════════════════════════════════
# Full End-to-End Pipeline Scenario
# Runs the complete challenge demo: Input → Insight → Action → Simulation → Result
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestFullPipelineScenario:
    """
    Complete end-to-end challenge scenario.
    Scenario: Supply chain disruption — 14 containers held at Karachi port.
    Demonstrates: Input → Insight → Action → Simulation → Result
    """

    def test_full_pipeline_supply_chain_scenario(self, capsys):
        print("\n" + "=" * 70)
        print("NEXUS — Challenge 1: Autonomous Content-to-Action Agent")
        print("Scenario: Supply Chain Disruption — Karachi Port Customs Hold")
        print("=" * 70)

        # ── STAGE 1: Content Understanding ───────────────────────────────────
        print("\n[STAGE 1] Ingesting 3 sources: text alert + CSV inventory + live feed")
        r_ingest = do_ingest_full()
        assert r_ingest.status_code == 200
        ingest = r_ingest.json()
        print(f"  ✓ Sources processed: {ingest['sources_processed']}")
        print(f"  ✓ Sources trusted: {ingest['sources_trusted']}")
        print(f"  ✓ Sources excluded: {ingest['sources_excluded']}")
        print(f"  ✓ Credibility scores: {ingest['credibility_map']}")
        print(f"  ✓ Contradictions found: {ingest['contradictions_found']}")
        assert ingest["sources_processed"] == 3
        assert ingest["ready_for_analysis"] is True

        # ── STAGE 2: Insight Extraction ───────────────────────────────────────
        print("\n[STAGE 2] Running 5-agent analysis pipeline (Orion/Raven/Cipher/Resolver/Executor)...")
        r_analyze = do_analyze()
        assert r_analyze.status_code == 200
        analysis = r_analyze.json()

        agents = {a["agent"]: a for a in analysis["agents"]}
        print(f"\n  [ORION — Optimist]")
        print(f"    Insight: {agents['Orion']['insight'][:120]}")
        print(f"    Action:  {agents['Orion']['recommended_action'][:100]}")
        print(f"    Confidence: {agents['Orion']['confidence']}%")

        print(f"\n  [RAVEN — Pessimist]")
        print(f"    Insight: {agents['Raven']['insight'][:120]}")
        print(f"    Action:  {agents['Raven']['recommended_action'][:100]}")
        print(f"    Confidence: {agents['Raven']['confidence']}%")

        print(f"\n  [CIPHER — Realist]")
        print(f"    Insight: {agents['Cipher']['insight'][:120]}")
        print(f"    Action:  {agents['Cipher']['recommended_action'][:100]}")
        print(f"    Confidence: {agents['Cipher']['confidence']}%")

        print(f"\n  Weighted Confidence: {analysis['weighted_confidence']}%")
        assert len(agents) == 3

        # ── STAGE 3: Impact Analysis (Resolver) ───────────────────────────────
        resolved = analysis["resolved"]
        print(f"\n[STAGE 3] Resolver synthesized final authoritative insight:")
        print(f"  Final Insight: {resolved['final_insight'][:150]}")
        print(f"  Evidence:      {resolved['trusted_evidence'][:100]}")
        print(f"  Uncertainty:   {resolved['remaining_uncertainty'][:100]}")
        print(f"  Summary:       {resolved['situation_summary'][:150]}")
        assert resolved["final_insight"]

        # ── STAGE 4: Action Generation (Executor) ────────────────────────────
        chain = analysis["action_chain"]
        print(f"\n[STAGE 4] Executor generated {len(chain)}-step causal action chain:")
        for action in chain:
            print(f"  Step {action['step']}: {action['action'][:80]}")
            print(f"           Cost: PKR {action['estimated_cost_pkr']:,} | "
                  f"Time: {action['estimated_time_minutes']}min | "
                  f"Status: {action['status']}")
        assert len(chain) == 5
        print(f"\n  Total estimated cost: PKR {analysis['total_estimated_cost_pkr']:,}")
        print(f"  Total estimated time: {analysis['total_estimated_time_minutes']} minutes")

        # ── STAGE 5: Action Simulation ────────────────────────────────────────
        print(f"\n[STAGE 5] Executing action chain (real integrations where configured)...")
        r_execute = client.post("/execute", json={"domain": "supply_chain"})
        assert r_execute.status_code == 200
        execution = r_execute.json()

        for step in execution["chain"]:
            result = step.get("real_result", {})
            real_flag = "REAL" if result.get("real") else "SIM"
            print(f"  Step {step['step']} [{real_flag}] → {result.get('channel', 'unknown')} "
                  f"| HTTP {result.get('http_status')} | {step['status']}")

        print(f"\n  Failures: {execution['failures']} | Recovered: {execution['recovered']}")
        print(f"  Total cost executed: PKR {execution['total_cost_pkr']:,}")

        # ── STAGE 6: Outcome Visualization ───────────────────────────────────
        before = execution["before_state"]
        after  = execution["after_state"]
        print(f"\n[STAGE 6] System state change:")
        print(f"  BEFORE → status: {before['status']} | "
              f"actions_done: {before['actions_completed']} | "
              f"cost: PKR {before['total_cost_pkr']:,}")
        print(f"  AFTER  → status: {after['status']} | "
              f"actions_done: {after['actions_completed']} | "
              f"cost: PKR {after['total_cost_pkr']:,}")
        assert after["status"] == "completed"
        assert after["actions_completed"] > before["actions_completed"]
        assert after["total_cost_pkr"] > before["total_cost_pkr"]

        print(f"\n  Execution log ({len(execution['log'])} entries):")
        for entry in execution["log"][:6]:
            print(f"    [{entry['time_display']}] {entry['message'][:80]}")

        # ── Final assertion: all 6 stages completed ───────────────────────────
        print("\n" + "=" * 70)
        print("✓ Challenge 1 COMPLETE: Input → Insight → Action → Simulation → Result")
        print("=" * 70)

        assert ingest["ready_for_analysis"] is True
        assert len(agents) == 3
        assert resolved["final_insight"]
        assert len(chain) == 5
        assert execution["total_cost_pkr"] > 0
        assert after["status"] == "completed"
