"""Model Context Protocol (MCP) server for a VKF bundle.

This exposes the same :class:`~vkf.service.KnowledgeService` that powers
``vkf serve`` and ``vkf html`` as MCP *tools*, so any MCP-speaking agent host
(Claude Desktop, Claude Code, the Gemini CLI, Cursor, …) can consume a VKF
bundle with zero custom integration code.

The tools mirror VKF's governance model rather than exposing raw files:

* ``search`` is **permission-aware** — pass a ``use`` context and confidential
  concepts that may not be used there are never returned, so they cannot leak
  into an answer.
* ``check_permission`` gives an explicit allow / deny / needs-review verdict for
  one concept in one context.
* ``freshness`` and ``validate`` let the agent reason about staleness and about
  what the bundle's conformance profile guarantees.

The MCP SDK is an optional dependency — install with ``pip install "vkf[mcp]"``.

    from vkf.mcp_server import create_mcp
    create_mcp("examples").run()          # stdio transport

Or simply: ``vkf mcp examples``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .service import KnowledgeService


def create_mcp(root: str | Path):
    """Build an MCP server bound to the VKF bundle at ``root``."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "The MCP SDK is not installed. Install the mcp extra: pip install 'vkf[mcp]'"
        ) from exc

    service = KnowledgeService(root)
    mcp = FastMCP(
        "vkf",
        instructions=(
            f"Verifiable Knowledge Format bundle at '{service.root}' "
            f"(conformance profile {service.profile}). Retrieve knowledge with "
            "`search`, always passing the `use` context you are answering in "
            "(e.g. 'internal_question_answering' or 'public_release') so "
            "permission-restricted concepts are filtered out. Prefer concepts "
            "whose status is 'verified' or 'active'; warn the user when you rely "
            "on a 'stale', 'draft', 'deprecated', or 'disputed' concept. Cite "
            "concept ids in your answers. Use `check_permission` before quoting a "
            "concept externally, and `freshness` to detect stale facts."
        ),
    )

    @mcp.tool()
    def search(
        q: str = "",
        use: str | None = None,
        role: str | None = None,
        limit: int = 20,
        include_denied: bool = False,
    ) -> dict[str, Any]:
        """Search the knowledge bundle and return concepts ranked by relevance.

        Args:
            q: Free-text query. Empty string lists everything (up to ``limit``).
            use: The use context you are answering in, e.g.
                ``internal_question_answering``, ``public_release``,
                ``external_sharing``, or ``training_data``. When set, concepts
                that may not be used in that context are filtered out — this is
                how VKF prevents confidential knowledge from leaking into an
                answer. Always set it when you know the audience.
            role: Optional requester role (e.g. ``employee``, ``contractor``)
                for role-scoped access rules.
            limit: Maximum number of results (1–200).
            include_denied: If true, include concepts you may NOT use, each
                flagged with ``allowed: false`` and a reason. Use only for
                debugging governance, never to answer a user.
        """
        limit = max(1, min(200, limit))
        hits = service.search(q=q, use=use, role=role, limit=limit, include_denied=include_denied)
        return {
            "query": q,
            "use_context": use,
            "role": role,
            "count": len(hits),
            "results": [h.to_dict() for h in hits],
        }

    @mcp.tool()
    def get_concept(ref: str) -> dict[str, Any]:
        """Fetch one concept in full: frontmatter, body, and parsed claim blocks.

        Args:
            ref: The concept's id/alias (e.g. ``metric:activation_rate``) or its
                bundle-relative path without ``.md`` (e.g. ``metrics/activation``).
        """
        concept = service.get_concept(ref)
        if concept is None:
            return {"error": f"unknown concept: {ref}"}
        return concept

    @mcp.tool()
    def list_concepts(
        type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """List concepts with their type, status, visibility, and freshness.

        Args:
            type: Filter by object type (e.g. ``metric``, ``dataset``, ``policy``).
            status: Filter by lifecycle status (e.g. ``verified``, ``draft``).
            tag: Filter by a tag.
        """
        return service.list_concepts(type=type, status=status, tag=tag)

    @mcp.tool()
    def check_permission(ref: str, use: str, role: str | None = None) -> dict[str, Any]:
        """Check whether one concept may be used in a given context.

        Returns an ``allowed`` verdict, whether it ``requires_review``, and a
        human-readable ``reason``. Call this before quoting a concept in an
        external or sensitive context.

        Args:
            ref: Concept id/alias or bundle-relative path.
            use: The use context, e.g. ``public_release`` or ``external_sharing``.
            role: Optional requester role.
        """
        result = service.check(ref, use, role=role)
        if result is None:
            return {"error": f"unknown concept: {ref}"}
        return result

    @mcp.tool()
    def freshness() -> list[dict[str, Any]]:
        """Report each concept's freshness (fresh / stale / expired) so you can
        warn about, or avoid relying on, out-of-date knowledge."""
        return service.freshness()

    @mcp.tool()
    def validate(profile: int | None = None) -> dict[str, Any]:
        """Validate the bundle and report what its conformance profile guarantees.

        Args:
            profile: Override the profile to validate against (0=okf-compatible,
                1=governed, 2=verified). Defaults to the bundle's declared profile.
        """
        return service.validate(profile=profile)

    @mcp.tool()
    def graph(typed_only: bool = False) -> dict[str, Any]:
        """Return the knowledge graph: concept nodes and their relationships.

        Args:
            typed_only: If true, include only typed frontmatter relations
                (``depends_on``, ``supersedes``, …) and omit untyped body links.
        """
        return service.graph(include_body_links=not typed_only)

    return mcp


def run(root: str | Path) -> None:  # pragma: no cover - stdio loop
    """Run the VKF MCP server over stdio (the default MCP transport)."""
    create_mcp(root).run()
