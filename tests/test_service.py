from pathlib import Path

from vkf.service import KnowledgeService

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def svc():
    return KnowledgeService(EXAMPLES)


def test_list_and_filter():
    s = svc()
    assert s.list_concepts()
    metrics = s.list_concepts(type="metric")
    assert metrics and all(c["type"] == "metric" for c in metrics)


def test_get_concept_includes_claims():
    s = svc()
    c = s.get_concept("metric:activation_rate")
    assert c is not None
    assert c["type"] == "metric"
    assert any(cl["id"] == "claim:activation_rate_definition" for cl in c["claims"])


def test_get_concept_by_path_identity():
    s = svc()
    assert s.get_concept("metrics/activation-rate") is not None


def test_search_matches_terms():
    s = svc()
    hits = s.search("activation")
    assert hits
    assert any("activation" in (h.title or "").lower() for h in hits)


def test_search_filters_forbidden_use():
    s = svc()
    # The user_events dataset forbids public_release; it must be excluded.
    public = {h.id for h in s.search("events", use="public_release")}
    internal = {h.id for h in s.search("events", use="internal_question_answering")}
    assert "dataset:user_events" in internal
    assert "dataset:user_events" not in public


def test_search_include_denied_annotates():
    s = svc()
    hits = s.search("events", use="public_release", include_denied=True)
    denied = [h for h in hits if h.id == "dataset:user_events"]
    assert denied and denied[0].allowed is False and denied[0].reason


def test_validate_passthrough():
    s = svc()
    rep = s.validate(profile=2)
    assert rep["profile"] == 2
    assert rep["summary"]["ERROR"] == 0
