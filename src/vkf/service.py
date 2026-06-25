"""Framework-agnostic knowledge service.

This is the engine behind both the HTTP server (``vkf serve``) and the static
HTML visualizer (``vkf html``). Keeping it independent of any web framework
means the retrieval and permission logic is unit-testable without spinning up a
server, and the same code powers an offline single-file export.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .claims import parse_claims
from .freshness import freshness_report
from .graph import build_graph
from .loader import KnowledgeObject, load_objects
from .manifest import PROFILE_NAMES, resolve_profile
from .permissions import can_use
from .validate import summarize, validate_objects


@dataclass
class SearchHit:
    id: str
    type: str | None
    title: str | None
    status: str | None
    visibility: str | None
    score: float
    snippet: str
    allowed: bool | None
    requires_review: bool
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class KnowledgeService:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.profile = resolve_profile(self.root)
        self._objects: list[KnowledgeObject] = load_objects(self.root)
        self._by_ref: dict[str, KnowledgeObject] = {}
        for obj in self._objects:
            for key in obj.ref_keys:
                self._by_ref[key] = obj

    # ---- listing & lookup ----------------------------------------------
    def list_concepts(
        self,
        type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        out = []
        fresh = {r["path"]: r["freshness"] for r in freshness_report(self.root)}
        for obj in self._objects:
            if type and obj.type != type:
                continue
            if status and obj.status != status:
                continue
            if tag and tag not in (obj.metadata.get("tags") or []):
                continue
            out.append({
                "id": obj.display_id,
                "concept_id": obj.concept_id,
                "type": obj.type,
                "title": obj.metadata.get("title"),
                "status": obj.status,
                "visibility": obj.metadata.get("visibility"),
                "freshness": fresh.get(str(obj.path)),
                "tags": obj.metadata.get("tags") or [],
            })
        return out

    def get_concept(self, ref: str) -> dict[str, Any] | None:
        obj = self._by_ref.get(ref)
        if obj is None:
            return None
        claims = [
            {"id": c.id, "metadata": c.metadata, "text": c.text, "errors": c.errors}
            for c in parse_claims(obj.body)
        ]
        return {
            "id": obj.display_id,
            "concept_id": obj.concept_id,
            "alias": obj.alias,
            "type": obj.type,
            "metadata": obj.metadata,
            "body": obj.body,
            "claims": claims,
        }

    # ---- permission-aware retrieval ------------------------------------
    def search(
        self,
        q: str = "",
        use: str | None = None,
        role: str | None = None,
        limit: int = 20,
        include_denied: bool = False,
    ) -> list[SearchHit]:
        """Rank concepts by a simple term match, then apply permission rules.

        When a ``use`` context is supplied, concepts the agent may not use in
        that context are filtered out (unless ``include_denied`` is set), which
        is the point: retrieval that already respects governance.
        """
        terms = [t for t in q.lower().split() if t]
        hits: list[SearchHit] = []
        for obj in self._objects:
            haystack = " ".join(str(x) for x in (
                obj.metadata.get("title") or "",
                obj.metadata.get("summary") or obj.metadata.get("description") or "",
                " ".join(obj.metadata.get("tags") or []),
                obj.body,
            )).lower()

            score: float
            if terms:
                score = float(sum(haystack.count(t) for t in terms))
                if score == 0:
                    continue
                # Title matches weigh more.
                title = (obj.metadata.get("title") or "").lower()
                score += 5 * sum(1 for t in terms if t in title)
            else:
                score = 1.0

            decision = None
            allowed: bool | None = None
            requires_review = False
            reason = None
            if use is not None:
                decision = can_use(obj.metadata, use, role=role)
                allowed = decision.allowed
                requires_review = decision.requires_review
                reason = decision.reason
                if not allowed and not include_denied:
                    continue

            hits.append(SearchHit(
                id=obj.display_id,
                type=obj.type,
                title=obj.metadata.get("title"),
                status=obj.status,
                visibility=obj.metadata.get("visibility"),
                score=float(score),
                snippet=_snippet(obj, terms),
                allowed=allowed,
                requires_review=requires_review,
                reason=reason,
            ))

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    # ---- compiled views ------------------------------------------------
    def graph(self, include_body_links: bool = True) -> dict[str, Any]:
        return build_graph(self.root, include_body_links=include_body_links)

    def freshness(self) -> list[dict[str, Any]]:
        return freshness_report(self.root)

    def validate(self, profile: int | None = None) -> dict[str, Any]:
        issues = validate_objects(self.root, profile=profile)
        eff = resolve_profile(self.root, profile)
        return {
            "profile": eff,
            "profile_name": PROFILE_NAMES.get(eff),
            "summary": summarize(issues),
            "issues": [{"level": i.level, "path": i.path, "message": i.message} for i in issues],
        }


def _snippet(obj: KnowledgeObject, terms: list[str], width: int = 160) -> str:
    text = " ".join(obj.body.split())
    if not terms:
        return text[:width]
    low = text.lower()
    pos = min((low.find(t) for t in terms if t in low), default=-1)
    if pos < 0:
        return text[:width]
    start = max(0, pos - width // 3)
    return ("…" if start else "") + text[start:start + width] + ("…" if start + width < len(text) else "")
