import json
from pathlib import Path

from vkf.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_search_text(capsys):
    rc = main(["search", str(EXAMPLES), "activation"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "metric:activation_rate" in out


def test_search_json(capsys):
    rc = main(["search", str(EXAMPLES), "activation", "--json"])
    assert rc == 0
    hits = json.loads(capsys.readouterr().out)
    assert isinstance(hits, list)
    assert any(h["id"] == "metric:activation_rate" for h in hits)


def test_search_use_context_filters_forbidden(capsys):
    rc = main(["search", str(EXAMPLES), "events", "--use", "public_release", "--json"])
    assert rc == 0
    hits = json.loads(capsys.readouterr().out)
    assert "dataset:user_events" not in {h["id"] for h in hits}


def test_get_text(capsys):
    rc = main(["get", str(EXAMPLES), "metric:activation_rate"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "id: metric:activation_rate" in out
    assert "type: metric" in out


def test_get_json(capsys):
    rc = main(["get", str(EXAMPLES), "metric:activation_rate", "--json"])
    assert rc == 0
    concept = json.loads(capsys.readouterr().out)
    assert concept["id"] == "metric:activation_rate"
    assert concept["type"] == "metric"


def test_get_unknown_ref_errors(capsys):
    rc = main(["get", str(EXAMPLES), "concept:does_not_exist"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "concept:does_not_exist" in err


def test_list_text(capsys):
    rc = main(["list", str(EXAMPLES), "--type", "claim"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "claim:activation_predicts_retention" in out


def test_list_json(capsys):
    rc = main(["list", str(EXAMPLES), "--type", "claim", "--json"])
    assert rc == 0
    concepts = json.loads(capsys.readouterr().out)
    assert concepts and all(c["type"] == "claim" for c in concepts)
