"""Knowledge-graph export.

Unlike OKF (which treats every markdown link as an untyped directed edge), VKF
exports *typed* edges from frontmatter relations and from claim-level evidence,
while still preserving untyped body links for OKF interoperability.
"""

from __future__ import annotations

import re
from pathlib import Path

from .claims import parse_claims
from .loader import load_objects

_TYPED_FIELDS = {
    "depends_on": "depends_on",
    "supersedes": "supersedes",
    "conflicts_with": "conflicts_with",
    "derived_from": "derived_from",
}

_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _as_list(value):
    if not value:
        return []
    return value if isinstance(value, list) else [value]


def build_graph(root: str | Path, include_body_links: bool = True) -> dict:
    root = Path(root)
    nodes = []
    edges = []
    for obj in load_objects(root):
        nodes.append({
            "id": obj.display_id,
            "concept_id": obj.concept_id,
            "alias": obj.alias,
            "type": obj.type,
            "title": obj.metadata.get("title"),
            "status": obj.status,
            "visibility": obj.metadata.get("visibility"),
            "path": str(obj.path),
        })
        for field, relation in _TYPED_FIELDS.items():
            for target in _as_list(obj.metadata.get(field)):
                edges.append({"source": obj.display_id, "target": target, "relation": relation, "typed": True})
        if obj.metadata.get("superseded_by"):
            edges.append({"source": obj.display_id, "target": obj.metadata["superseded_by"], "relation": "superseded_by", "typed": True})

        # Claim-level evidence edges.
        for claim in parse_claims(obj.body):
            for ev in claim.metadata.get("evidence") or []:
                src = ev.get("source") if isinstance(ev, dict) else None
                if src:
                    edges.append({
                        "source": claim.id or obj.display_id,
                        "target": src,
                        "relation": "evidenced_by",
                        "typed": True,
                    })

        # Untyped body links (OKF parity).
        if include_body_links:
            for match in _MD_LINK.findall(obj.body):
                if match.startswith(("http://", "https://", "#")):
                    continue
                target = match[:-3] if match.endswith(".md") else match
                target = target.lstrip("/")
                edges.append({"source": obj.concept_id, "target": target, "relation": "links_to", "typed": False})

    return {"nodes": nodes, "edges": edges}
