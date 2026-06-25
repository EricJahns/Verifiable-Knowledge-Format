"""Loading of VKF concept documents.

VKF inherits OKF's identity model: a bundle is a directory tree of markdown
files, one concept per file, and a concept's canonical identity is its
bundle-relative path minus the ``.md`` extension (e.g. ``tables/orders.md`` ->
``tables/orders``). The reserved filenames ``index.md`` and ``log.md`` are not
concepts. On top of that, VKF allows an optional stable ``id`` alias in
frontmatter for references that must survive file moves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frontmatter

#: Filenames reserved by OKF for navigation/history, never treated as concepts.
RESERVED_FILENAMES = {"index.md", "log.md"}


@dataclass
class KnowledgeObject:
    """A single VKF concept document."""

    path: Path
    root: Path
    metadata: dict[str, Any]
    body: str

    @property
    def concept_id(self) -> str:
        """Canonical OKF identity: bundle-relative path without ``.md``."""
        rel = self.path.relative_to(self.root).as_posix()
        return rel[:-3] if rel.endswith(".md") else rel

    @property
    def alias(self) -> str | None:
        """Optional stable ``id`` alias declared in frontmatter."""
        value = self.metadata.get("id")
        return value if isinstance(value, str) else None

    @property
    def ref_keys(self) -> set[str]:
        """All identifiers other objects may use to reference this one."""
        keys = {self.concept_id}
        if self.alias:
            keys.add(self.alias)
        return keys

    @property
    def type(self) -> str | None:
        return self.metadata.get("type")

    @property
    def status(self) -> str | None:
        return self.metadata.get("status")

    @property
    def display_id(self) -> str:
        """Best human-facing identifier: alias if present, else path id."""
        return self.alias or self.concept_id


def iter_markdown_files(root: str | Path):
    """Yield concept files under ``root`` (skips reserved names and ``.git``)."""
    root = Path(root)
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        if path.name in RESERVED_FILENAMES:
            continue
        yield path


def load_object(path: str | Path, root: str | Path) -> KnowledgeObject:
    path = Path(path)
    root = Path(root)
    post = frontmatter.load(path)
    return KnowledgeObject(
        path=path,
        root=root,
        metadata=dict(post.metadata),
        body=post.content,
    )


def load_objects(root: str | Path) -> list[KnowledgeObject]:
    root = Path(root)
    return [load_object(path, root) for path in iter_markdown_files(root)]
