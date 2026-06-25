"""HTTP API for a VKF bundle.

This exposes the :class:`~vkf.service.KnowledgeService` over HTTP so an agent (or
a UI) can do **permission-aware retrieval**: ask for knowledge in a given use
context and get back only what it is allowed to use. FastAPI is an optional
dependency — install with ``pip install "vkf[server]"``.

    from vkf.server import create_app
    app = create_app("examples")            # then: uvicorn ...

Or simply: ``vkf serve examples``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .service import KnowledgeService


def create_app(root: str | Path):
    try:
        from fastapi import FastAPI, HTTPException, Query
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install the server extra: pip install 'vkf[server]'"
        ) from exc

    from . import __version__

    service = KnowledgeService(root)
    app = FastAPI(
        title="VKF Knowledge Service",
        version=__version__,
        description="Permission-aware retrieval over a Verifiable Knowledge Format bundle.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "root": str(service.root),
            "profile": service.profile,
            "concepts": len(service._objects),
        }

    @app.get("/concepts")
    def list_concepts(
        type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        return service.list_concepts(type=type, status=status, tag=tag)

    @app.get("/concepts/{ref:path}")
    def get_concept(ref: str) -> dict[str, Any]:
        concept = service.get_concept(ref)
        if concept is None:
            raise HTTPException(status_code=404, detail=f"unknown concept: {ref}")
        return concept

    @app.get("/search")
    def search(
        q: str = "",
        use: str | None = None,
        role: str | None = None,
        limit: int = Query(20, ge=1, le=200),
        include_denied: bool = False,
    ) -> dict[str, Any]:
        hits = service.search(q=q, use=use, role=role, limit=limit, include_denied=include_denied)
        return {
            "query": q,
            "use_context": use,
            "role": role,
            "count": len(hits),
            "results": [h.to_dict() for h in hits],
        }

    @app.get("/graph")
    def graph(typed_only: bool = False) -> dict[str, Any]:
        return service.graph(include_body_links=not typed_only)

    @app.get("/freshness")
    def freshness() -> list[dict[str, Any]]:
        return service.freshness()

    @app.get("/validate")
    def validate(profile: int | None = Query(None, ge=0, le=2)) -> dict[str, Any]:
        return service.validate(profile=profile)

    return app


def serve(root: str | Path, host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError(
            "uvicorn is not installed. Install the server extra: pip install 'vkf[server]'"
        ) from exc
    uvicorn.run(create_app(root), host=host, port=port)
