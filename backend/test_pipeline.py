"""
NEXUS Pipeline — comprehensive integration tests
Run:  pytest test_pipeline.py -v
LLM tests are slow (~10-30s each); skip with:  pytest test_pipeline.py -v -m "not llm"
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient
from main import app, state_store

client = TestClient(app)

SAMPLE_TEXT = (
    "Supply chain disruption: 14 containers held at Karachi customs. "
    "Estimated 72-hour delay. PKR 2.4M daily revenue at risk. "
    "Supplier B confirmed alternate stock available within 48 hours."
)
SAMPLE_CSV = (
    "date,sku,quantity,price_pkr\n"
    "2024-01-01,SKU-001,100,5000\n"
    "2024-01-02,SKU-001,85,5200\n"
    "2024-01-03,SKU-001,60,5500\n"
    "2024-01-04,SKU-002,200,3000\n"
    "2024-01-05,SKU-002,180,3100\n"
)
SAMPLE_CHAIN = [
    {"step": 1, "action": "Diagnose root cause of supply disruption", "estimated_cost_pkr": 5000, "estimated_time_minutes": 30, "status": "PENDING"},
    {"step": 2, "action": "Notify stakeholders via email", "estimated_cost_pkr": 2000, "estimated_time_minutes": 20, "status": "PENDING"},
    {"step": 3, "action": "Update system state in dashboard", "estimated_cost_pkr": 8000, "estimated_time_minutes": 15, "status": "PENDING"},
    {"step": 4, "action": "Launch mitigation: contact alternate suppliers", "estimated_cost_pkr": 150000, "estimated_time_minutes": 90, "status": "PENDING"},
    {"step": 5, "action": "Schedule 72h monitoring protocol", "estimated_cost_pkr": 10000, "estimated_time_minutes": 20, "status": "PENDING"},
]
HAS_GOOGLE_KEY = bool(os.environ.get("GOOGLE_API_KEY"))


def do_ingest(**kwargs):
    data = {"domain": "supply_chain", **kwargs}
    return client.post("/ingest", data=data)


def do_analyze(**kwargs):
    body = {"domain": "supply_chain", "flow_type": "custom", **kwargs}
    return client.post("/analyze", json=body)


# ── 1. Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_system_name(self):
        assert client.get("/health").json()["system"] == "NEXUS"

    def test_all_five_agents_listed(self):
        agents = set(client.get("/health").json()["agents"])
        assert agents == {"Orion", "Raven", "Cipher", "Resolver", "Executor"}

    def test_capabilities_present(self):
        caps = client.get("/health").json()["capabilities"]
        for cap in ("multi-source-ingestion", "constraint-checking", "contradiction-detection"):
            assert cap in caps, f"Missing capability: {cap}"


# ── 2. Ingestion ──────────────────────────────────────────────────────────────

class TestIngest:
    def test_text_source_processed(self):
        r = do_ingest(text=SAMPLE_TEXT)
        assert r.status_code == 200
        data = r.json()
        assert data["sources_processed"] == 1
        assert data["ready_for_analysis"] is True
        assert "credibility_map" in data

    def test_csv_source_trusted_high_credibility(self):
        r = do_ingest(csv_data=SAMPLE_CSV)
        data = r.json()
        assert data["sources_processed"] == 1
        assert data["sources_trusted"] >= 1
        assert data["credibility_map"].get("csv", 0) >= 0.90

    def test_feed_source_included_when_requested(self):
        r = do_ingest(include_feed="true", topic="supply")
        data = r.json()
        assert data["sources_processed"] >= 1

    def test_multi_source_counts(self):
        r = do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV, include_feed="true", topic="supply")
        data = r.json()
        assert data["sources_processed"] == 3

    def test_multi_source_has_contradictions_key(self):
        r = do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV)
        data = r.json()
        assert "contradictions" in data
        assert "temporal_analysis" in data

    def test_credibility_map_includes_all_source_types(self):
        r = do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV)
        cmap = r.json()["credibility_map"]
        assert "text" in cmap
        assert "csv" in cmap

    def test_csv_credibility_higher_than_text(self):
        r = do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV)
        cmap = r.json()["credibility_map"]
        assert cmap["csv"] > cmap["text"]

    def test_empty_ingest_zero_sources(self):
        r = client.post("/ingest", data={"domain": "test"})
        assert r.json()["sources_processed"] == 0

    def test_invalid_url_excluded(self):
        r = do_ingest(text=SAMPLE_TEXT, url="http://invalid.nexus-no-such-domain-xyz.invalid")
        data = r.json()
        cmap = data["credibility_map"]
        url_score = cmap.get("url", 0.0)
        assert url_score < 0.30 or data["sources_excluded"] >= 1

    def test_stale_text_reduces_credibility(self):
        stale = "Last month our inventory was adequate but yesterday we noticed issues."
        r = do_ingest(text=stale)
        data = r.json()
        text_score = data["credibility_map"].get("text", 1.0)
        assert text_score < 0.65  # stale penalty applied

    def test_noise_text_reduces_credibility(self):
        noisy = "BREAKING rumor: allegedly the supply chain is disrupted!"
        r = do_ingest(text=noisy)
        score = r.json()["credibility_map"].get("text", 1.0)
        assert score < 0.65

    def test_sources_excluded_count_matches(self):
        r = do_ingest(text=SAMPLE_TEXT, url="http://no-such-host.fake")
        data = r.json()
        total = data["sources_trusted"] + data["sources_excluded"]
        assert total == data["sources_processed"]

    def test_state_updated_domain_after_ingest(self):
        do_ingest(text=SAMPLE_TEXT, domain="fuel_supply")
        r = client.get("/state")
        assert r.json()["active_domain"] == "fuel_supply"

    def test_state_sources_ingested_increments(self):
        do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV)
        data = client.get("/state").json()
        assert data["sources_ingested"] >= 1


# ── 3. State, Logs, Baseline ──────────────────────────────────────────────────

class TestStateAndLogs:
    def test_state_endpoint_ok(self):
        assert client.get("/state").status_code == 200

    def test_state_has_required_fields(self):
        data = client.get("/state").json()
        for field in ("status", "sources_ingested", "active_domain", "last_updated"):
            assert field in data, f"Missing field: {field}"

    def test_logs_endpoint_ok(self):
        r = client.get("/logs")
        assert r.status_code == 200
        assert "logs" in r.json()

    def test_baseline_comparison_ok(self):
        r = client.get("/baseline-comparison")
        assert r.status_code == 200
        data = r.json()
        assert "nexus_agentic" in data
        assert "simple_heuristic" in data
        assert "improvements" in data

    def test_baseline_nexus_has_contradiction_detection(self):
        data = client.get("/baseline-comparison").json()
        assert data["nexus_agentic"]["contradiction_detection"] is True
        assert data["simple_heuristic"]["contradiction_detection"] is False

    def test_baseline_nexus_5_step_chain(self):
        data = client.get("/baseline-comparison").json()
        assert data["nexus_agentic"]["action_chain_depth"] == 5
        assert data["simple_heuristic"]["action_chain_depth"] == 1


# ── 4. Execute (no LLM) ───────────────────────────────────────────────────────

class TestExecute:
    def test_execute_explicit_chain_returns_result(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"})
        assert r.status_code == 200
        data = r.json()
        assert "chain" in data
        assert "total_cost_pkr" in data
        assert "log" in data

    def test_execute_cost_sums_chain(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"})
        data = r.json()
        expected = sum(a["estimated_cost_pkr"] for a in SAMPLE_CHAIN)
        assert data["total_cost_pkr"] == expected

    def test_execute_all_steps_done(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"})
        chain = r.json()["chain"]
        for step in chain:
            assert step["status"] in ("DONE", "RECOVERED"), f"Step {step.get('step')} not done"

    def test_execute_failure_recovery_tracked(self):
        results = [
            client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"}).json()
            for _ in range(5)
        ]
        # Over 5 runs, at least some should see recovery (step 3 has 40% failure rate)
        # Just verify the field exists; don't assert specific count (probabilistic)
        for r in results:
            assert "recovered" in r

    def test_execute_updates_state_last_updated(self):
        client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"})
        data = client.get("/state").json()
        assert data["last_updated"] is not None

    def test_execute_before_after_state_present(self):
        r = client.post("/execute", json={"chain": SAMPLE_CHAIN, "domain": "supply_chain"})
        data = r.json()
        assert "before_state" in data
        assert "after_state" in data
        assert data["after_state"]["status"] == "completed"


# ── 5. Analyze (LLM required) ─────────────────────────────────────────────────

@pytest.mark.llm
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not set")
class TestAnalyze:
    def setup_method(self):
        do_ingest(text=SAMPLE_TEXT, csv_data=SAMPLE_CSV, include_feed="true", topic="supply")

    def test_analyze_returns_200(self):
        r = do_analyze()
        assert r.status_code == 200

    def test_three_agent_perspectives_returned(self):
        agents = do_analyze().json().get("agents", [])
        assert len(agents) == 3
        names = {a.get("agent") for a in agents}
        assert names == {"Orion", "Raven", "Cipher"}

    def test_all_agent_personas_present(self):
        agents = do_analyze().json().get("agents", [])
        personas = {a.get("persona") for a in agents}
        assert personas == {"Optimist", "Pessimist", "Realist"}

    def test_resolved_final_insight_non_empty(self):
        resolved = do_analyze().json().get("resolved", {})
        assert "final_insight" in resolved
        assert len(resolved["final_insight"]) > 20

    def test_action_chain_exactly_5_steps(self):
        chain = do_analyze().json().get("action_chain", [])
        assert len(chain) == 5

    def test_action_chain_step_numbers_sequential(self):
        chain = do_analyze().json().get("action_chain", [])
        assert [a.get("step") for a in chain] == [1, 2, 3, 4, 5]

    def test_each_action_has_cost_and_time(self):
        chain = do_analyze().json().get("action_chain", [])
        for action in chain:
            assert "estimated_cost_pkr" in action
            assert "estimated_time_minutes" in action
            assert action["estimated_cost_pkr"] >= 0

    def test_weighted_confidence_in_range(self):
        conf = do_analyze().json().get("weighted_confidence")
        assert isinstance(conf, (int, float))
        assert 0 < conf <= 100

    def test_total_cost_sums_chain(self):
        data = do_analyze().json()
        chain = data.get("action_chain", [])
        expected = sum(a.get("estimated_cost_pkr", 0) for a in chain)
        assert data.get("total_estimated_cost_pkr") == expected

    def test_analyze_without_ingest_returns_400(self):
        original = state_store.get("ingestion_result")
        state_store["ingestion_result"] = None
        r = do_analyze()
        state_store["ingestion_result"] = original
        assert r.status_code == 400

    def test_google_sdk_flow_also_works(self):
        r = do_analyze(flow_type="google_sdk")
        assert r.status_code == 200
        assert "agents" in r.json()


# ── 6. Auth ───────────────────────────────────────────────────────────────────

class TestAuth:
    EMAIL = "nexus_test_user@example.com"
    PASS = "TestPass123!"

    def _ensure_registered(self):
        try:
            client.post("/auth/register", json={"name": "Test User", "email": self.EMAIL, "password": self.PASS})
        except Exception:
            pass

    def test_register_returns_token(self):
        # Delete existing user if any by trying a unique email
        import time as _t
        email = f"nexus_{int(_t.time())}@example.com"
        r = client.post("/auth/register", json={"name": "Test", "email": email, "password": self.PASS})
        assert r.status_code == 200
        assert "token" in r.json()

    def test_duplicate_register_returns_400(self):
        self._ensure_registered()
        r = client.post("/auth/register", json={"name": "Test", "email": self.EMAIL, "password": self.PASS})
        assert r.status_code == 400

    def test_login_returns_token(self):
        self._ensure_registered()
        r = client.post("/auth/login", json={"email": self.EMAIL, "password": self.PASS})
        assert r.status_code == 200
        assert "token" in r.json()

    def test_login_wrong_password_401(self):
        self._ensure_registered()
        r = client.post("/auth/login", json={"email": self.EMAIL, "password": "WrongPass!"})
        assert r.status_code == 401

    def test_me_with_valid_token(self):
        self._ensure_registered()
        token = client.post("/auth/login", json={"email": self.EMAIL, "password": self.PASS}).json()["token"]
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == self.EMAIL

    def test_me_without_token_401(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_with_bad_token_401(self):
        r = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401
