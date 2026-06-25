"""Parser for VKF inline claim blocks.

A claim block embeds a verifiable, provenance-bearing assertion inside an
otherwise free-form markdown body. The grammar is deliberately unambiguous and
degrades to inert text for plain-markdown (OKF) consumers:

    :::claim
    ---
    id: claim:activation_rate_definition
    confidence: high
    evidence:
      - source: dataset:user_events
        strength: strong
    ---
    Activation rate is activated new users divided by total new users.
    :::

Rules:
* The block opens with a line whose only content is ``:::claim`` and closes
  with a line whose only content is ``:::``.
* An optional YAML metadata header is delimited by ``---`` fences immediately
  after the opening line, mirroring document frontmatter.
* Everything between the metadata header (or the opening line, if none) and the
  closing fence is the claim's markdown body.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

_OPEN = re.compile(r"^:::claim\s*$")
_CLOSE = re.compile(r"^:::\s*$")
_FENCE = re.compile(r"^---\s*$")


@dataclass
class ParsedClaim:
    """A claim block extracted from a document body."""

    metadata: dict[str, Any]
    text: str
    start_line: int  # 1-based line number of the opening ``:::claim``
    errors: list[str] = field(default_factory=list)

    @property
    def id(self) -> str | None:
        value = self.metadata.get("id")
        return value if isinstance(value, str) else None


def parse_claims(body: str) -> list[ParsedClaim]:
    """Extract all claim blocks from a markdown body, in document order."""
    lines = body.splitlines()
    claims: list[ParsedClaim] = []
    i = 0
    n = len(lines)

    while i < n:
        if not _OPEN.match(lines[i]):
            i += 1
            continue

        start_line = i + 1
        errors: list[str] = []
        i += 1
        metadata: dict[str, Any] = {}

        # Optional YAML metadata header delimited by --- ... ---
        if i < n and _FENCE.match(lines[i]):
            i += 1
            meta_lines: list[str] = []
            closed_meta = False
            while i < n:
                if _FENCE.match(lines[i]):
                    closed_meta = True
                    i += 1
                    break
                if _CLOSE.match(lines[i]):
                    break  # claim closed before metadata fence -> malformed
                meta_lines.append(lines[i])
                i += 1
            if not closed_meta:
                errors.append("claim metadata header not closed with '---'")
            else:
                try:
                    loaded = yaml.safe_load("\n".join(meta_lines)) or {}
                    if isinstance(loaded, dict):
                        metadata = loaded
                    else:
                        errors.append("claim metadata is not a YAML mapping")
                except yaml.YAMLError as exc:
                    errors.append(f"invalid YAML in claim metadata: {exc}")

        # Body up to the closing fence
        text_lines: list[str] = []
        closed = False
        while i < n:
            if _CLOSE.match(lines[i]):
                closed = True
                i += 1
                break
            text_lines.append(lines[i])
            i += 1
        if not closed:
            errors.append("claim block not closed with ':::'")

        claims.append(
            ParsedClaim(
                metadata=metadata,
                text="\n".join(text_lines).strip(),
                start_line=start_line,
                errors=errors,
            )
        )

    return claims
