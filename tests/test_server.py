from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from starlette.testclient import TestClient  # noqa: E402

from vkf.server import create_app  # noqa: E402

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(EXAMPLES))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["concepts"] > 0


def test_list_concepts(client):
    r = client.get("/concepts", params={"type": "metric"})
    assert r.status_code == 200
    assert all(c["type"] == "metric" for c in r.json())


def test_get_concept(client):
    r = client.get("/concepts/metric:activation_rate")
    assert r.status_code == 200
    assert r.json()["type"] == "metric"


def test_get_concept_404(client):
    assert client.get("/concepts/nope:missing").status_code == 404


def test_permission_aware_search(client):
    denied = client.get("/search", params={"q": "events", "use": "public_release"}).json()
    allowed = client.get("/search", params={"q": "events", "use": "internal_question_answering"}).json()
    ids_denied = {r["id"] for r in denied["results"]}
    ids_allowed = {r["id"] for r in allowed["results"]}
    assert "dataset:user_events" in ids_allowed
    assert "dataset:user_events" not in ids_denied


def test_graph_and_validate(client):
    assert client.get("/graph").json()["nodes"]
    rep = client.get("/validate", params={"profile": 2}).json()
    assert rep["summary"]["ERROR"] == 0
