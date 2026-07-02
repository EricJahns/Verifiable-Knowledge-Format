import asyncio
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from vkf.mcp_server import create_mcp  # noqa: E402

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

EXPECTED_TOOLS = {
    "search",
    "get_concept",
    "list_concepts",
    "check_permission",
    "freshness",
    "validate",
    "graph",
}


@pytest.fixture(scope="module")
def mcp():
    return create_mcp(EXAMPLES)


def _structured(result):
    """`FastMCP.call_tool` returns (content, structured_result); take the latter."""
    return result[1] if isinstance(result, tuple) else result


def test_tools_registered(mcp):
    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert EXPECTED_TOOLS <= names


def test_search_is_permission_aware(mcp):
    async def run():
        internal = _structured(
            await mcp.call_tool("search", {"q": "events", "use": "internal_question_answering"})
        )
        public = _structured(
            await mcp.call_tool("search", {"q": "events", "use": "public_release"})
        )
        return internal, public

    internal, public = asyncio.run(run())
    ids_internal = {r["id"] for r in internal["results"]}
    ids_public = {r["id"] for r in public["results"]}
    # The confidential dataset is retrievable internally but never for public release.
    assert "dataset:user_events" in ids_internal
    assert "dataset:user_events" not in ids_public


def test_check_permission_denies_external_use(mcp):
    result = _structured(
        asyncio.run(mcp.call_tool("check_permission", {"ref": "dataset:user_events", "use": "public_release"}))
    )
    assert result["allowed"] is False
    assert result["reason"]


def test_get_concept_and_validate(mcp):
    async def run():
        concept = _structured(await mcp.call_tool("get_concept", {"ref": "metric:activation_rate"}))
        report = _structured(await mcp.call_tool("validate", {"profile": 2}))
        return concept, report

    concept, report = asyncio.run(run())
    assert concept["type"] == "metric"
    assert report["summary"]["ERROR"] == 0


def test_unknown_concept_returns_error(mcp):
    result = _structured(asyncio.run(mcp.call_tool("get_concept", {"ref": "nope:missing"})))
    assert "error" in result
