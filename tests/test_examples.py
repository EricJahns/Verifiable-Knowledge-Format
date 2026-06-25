from pathlib import Path

from vkf.graph import build_graph
from vkf.validate import has_errors, validate_objects

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_examples_validate_at_governed_profile():
    issues = validate_objects(EXAMPLES)  # profile read from examples/vkf.bundle.yaml (=1)
    assert not has_errors(issues), "\n".join(str(i) for i in issues)


def test_examples_validate_at_verified_profile_has_no_errors():
    # The curated examples are intended to be exemplary at the strictest profile.
    issues = validate_objects(EXAMPLES, profile=2)
    assert not has_errors(issues), "\n".join(str(i) for i in issues)


def test_graph_contains_metric_node_and_evidence_edge():
    graph = build_graph(EXAMPLES)
    assert any(n["id"] == "metric:activation_rate" for n in graph["nodes"])
    assert any(e["relation"] == "evidenced_by" for e in graph["edges"])
