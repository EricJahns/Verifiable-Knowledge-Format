from pathlib import Path

from vkf import benchmark as bench

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "benchmark" / "bundle"
SCENARIOS = ROOT / "benchmark" / "scenarios.yaml"


def test_harness_runs_with_mock_agent():
    scenarios = bench.load_scenarios(SCENARIOS)
    results = bench.run(BUNDLE, scenarios, bench.MockAgent())
    # 4 scenarios x 3 conditions
    assert len(results) == len(scenarios) * len(bench.CONDITIONS)


def test_permission_filter_prevents_leak_in_retrieval():
    """The core, API-key-free guarantee: VKF withholds the confidential doc,
    so the canary cannot reach the answer; RAG/OKF retrieve it and leak."""
    scenarios = bench.load_scenarios(SCENARIOS)
    results = bench.run(BUNDLE, scenarios, bench.MockAgent())
    agg = bench.aggregate(results)
    # 'good' on permission_leak_rate == leak avoided.
    assert agg["vkf"]["permission_leak_rate"] == 1.0
    assert agg["rag"]["permission_leak_rate"] == 0.0
    assert agg["okf"]["permission_leak_rate"] == 0.0


def test_vkf_withholds_confidential_concept():
    from vkf.service import KnowledgeService
    service = KnowledgeService(BUNDLE)
    scenario = next(s for s in bench.load_scenarios(SCENARIOS) if s["category"] == "permission_leak")
    _, withheld = bench.build_context(service, scenario, "vkf")
    assert withheld >= 1
    rag_ctx, _ = bench.build_context(service, scenario, "rag")
    assert "48,732,915" in rag_ctx  # RAG sees the secret


def test_update_readme_replaces_between_markers(tmp_path):
    f = tmp_path / "R.md"
    f.write_text("intro\n<!-- RESULTS:START -->\nOLD\n<!-- RESULTS:END -->\noutro\n")
    assert bench.update_readme(f, "NEW TABLE") is True
    out = f.read_text()
    assert "NEW TABLE" in out and "OLD" not in out
    assert out.startswith("intro") and out.rstrip().endswith("outro")


def test_update_readme_without_markers_is_noop(tmp_path):
    f = tmp_path / "R.md"
    f.write_text("no markers here")
    assert bench.update_readme(f, "X") is False
    assert f.read_text() == "no markers here"


def test_scoring_is_deterministic():
    scenario = {
        "metric": "authority_accuracy",
        "scoring": {"correct_tokens": ["2.1"], "wrong_tokens": ["8%"]},
    }
    # Correct value, no wrong value -> good.
    assert bench.score(scenario, "The rate is 2.1% per claim:monthly_churn")["good"] is True
    # Wrong value asserted as the answer -> not good.
    assert bench.score(scenario, "It's about 8% I think")["good"] is False


def test_scoring_credits_dismissed_wrong_value():
    """The key fix: a correct answer that mentions the wrong value *to dismiss
    it* must score as good (the old scorer failed these)."""
    scenario = {
        "metric": "authority_accuracy",
        "scoring": {"correct_tokens": ["2.1"], "wrong_tokens": ["8%"]},
    }
    good = bench.score(scenario, "The rate is 2.1%; an unverified estimate of 8% exists but is not authoritative.")
    assert good["good"] is True
    assert good["wrong_present"] is True and good["wrong_dismissed"] is True
    # But 8% presented without any dismissal alongside 2.1% is not good.
    bad = bench.score(scenario, "The rate is 2.1%, though some teams say 8%.")
    assert bad["good"] is False


def test_staleness_scoring_credits_outdated_mention():
    scenario = {
        "metric": "stale_fact_avoidance",
        "scoring": {"fresh_tokens": ["14 day"], "stale_tokens": ["7 day"]},
    }
    assert bench.score(scenario, "It is 14 days; the old 7 day window was replaced.")["good"] is True
    assert bench.score(scenario, "It is either 7 days or 14 days.")["good"] is False
