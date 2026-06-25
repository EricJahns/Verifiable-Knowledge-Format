"""OKF interoperability.

VKF is a strict superset of OKF v0.1, and this module makes that claim
falsifiable in both directions:

* ``to_okf`` projects a VKF bundle down to a pure OKF bundle (dropping VKF
  governance keys) and writes it out — proving VKF degrades cleanly to
  something any OKF consumer accepts.
* ``okf_conformance`` checks that a bundle satisfies OKF's structural rules
  (parseable frontmatter, non-empty ``type``) — i.e. it would validate at
  VKF Profile 0.
* ``enrichment_report`` tells a team what governance fields they'd add to lift
  an OKF bundle to the VKF "governed" profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter

from .loader import iter_markdown_files, load_objects

#: Frontmatter keys recognized by OKF v0.1.
OKF_KEYS = ("type", "title", "description", "resource", "tags", "timestamp")

#: Governance fields VKF adds on top of OKF, for the enrichment report.
VKF_GOVERNANCE_FIELDS = ("owners", "status", "visibility", "last_verified", "valid_until", "evidence", "access")


@dataclass
class OkfIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"[OKF] {self.path}: {self.message}"


def to_okf_metadata(metadata: dict) -> dict:
    """Project frontmatter onto the OKF-recognized key set."""
    return {k: metadata[k] for k in OKF_KEYS if k in metadata}


def to_okf(root: str | Path, out: str | Path) -> int:
    """Write a pure-OKF projection of a VKF bundle to ``out``. Returns count."""
    root = Path(root)
    out = Path(out)
    count = 0
    for path in iter_markdown_files(root):
        post = frontmatter.load(path)
        post.metadata = to_okf_metadata(dict(post.metadata))
        rel = path.relative_to(root)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(frontmatter.dumps(post) + "\n")
        count += 1
    return count


def okf_conformance(root: str | Path) -> list[OkfIssue]:
    """Check OKF structural conformance (== VKF Profile 0)."""
    issues: list[OkfIssue] = []
    for path in iter_markdown_files(root):
        try:
            post = frontmatter.load(path)
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            issues.append(OkfIssue(str(path), f"frontmatter does not parse: {exc}"))
            continue
        t = post.metadata.get("type")
        if not (isinstance(t, str) and t.strip()):
            issues.append(OkfIssue(str(path), "missing required OKF field 'type'"))
    return issues


def enrichment_report(root: str | Path) -> list[dict]:
    """For each concept, which VKF governance fields are still missing."""
    rows = []
    for obj in load_objects(root):
        missing = [f for f in VKF_GOVERNANCE_FIELDS if not obj.metadata.get(f)]
        rows.append({
            "id": obj.display_id,
            "path": str(obj.path),
            "type": obj.type,
            "missing_governance_fields": missing,
        })
    return rows
