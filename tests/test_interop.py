import textwrap
from pathlib import Path

from vkf.interop import OKF_KEYS, okf_conformance, to_okf, to_okf_metadata
from vkf.validate import has_errors, validate_objects

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_to_okf_metadata_drops_governance_keys():
    meta = {
        "type": "metric", "title": "T", "tags": ["a"], "resource": "https://x",
        "owners": ["team:x"], "status": "active", "access": {"forbidden_uses": []},
        "id": "metric:t",
    }
    out = to_okf_metadata(meta)
    assert set(out) <= set(OKF_KEYS)
    assert "owners" not in out and "status" not in out and "id" not in out
    assert out["type"] == "metric"


def test_examples_project_to_conformant_okf(tmp_path):
    n = to_okf(EXAMPLES, tmp_path)
    assert n > 0
    # The projection must be OKF-conformant...
    assert okf_conformance(tmp_path) == []
    # ...and therefore validate at VKF Profile 0 without errors.
    assert not has_errors(validate_objects(tmp_path, profile=0))


def test_okf_bundle_imports_clean(tmp_path):
    p = tmp_path / "t.md"
    p.write_text(textwrap.dedent("""
        ---
        type: dataset
        title: Orders
        ---
        # Schema
    """).lstrip())
    assert okf_conformance(tmp_path) == []
