"""Profile-aware validation of a VKF bundle.

Validation severity is gated by the bundle's conformance profile so that VKF
never rejects a bundle OKF would accept:

* Profile 0 (okf-compatible): only the OKF requirement is enforced as an error
  (every concept has a non-empty ``type``). Everything else is advisory.
* Profile 1 (governed): schema conformance, ISO dates, ownership of live
  objects, unique ids, resolvable typed references, and dependency-cycle
  freedom become errors.
* Profile 2 (verified): additionally requires evidence on claims and
  ``last_verified`` on verified objects, and checks reciprocal supersession.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

from importlib.resources import files as _pkg_files  # schemas ship as package data

from .claims import parse_claims
from .loader import KnowledgeObject, load_objects
from .manifest import PROFILE_NAMES, resolve_profile

KNOWN_TYPES = {
    "concept", "claim", "decision", "policy", "runbook",
    "dataset", "metric", "experiment", "artifact", "transaction",
}

LIVE_STATUSES = {"active", "verified"}

#: Frontmatter fields whose values are typed references to other concepts.
LIST_REF_FIELDS = ("depends_on", "supersedes", "conflicts_with", "derived_from")
SCALAR_REF_FIELDS = ("superseded_by",)


@dataclass
class ValidationIssue:
    level: str  # ERROR | WARNING | INFO
    path: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.path}: {self.message}"


@lru_cache(maxsize=None)
def _load_schema() -> dict[str, Any]:
    text = _pkg_files("vkf").joinpath("schemas/object.schema.json").read_text()
    return json.loads(text)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    for parser in (date.fromisoformat, lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).date()):
        try:
            return parser(text)
        except ValueError:
            continue
    return None


def _is_valid_date(value: Any) -> bool:
    return value in (None, "") or _parse_date(value) is not None


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    if isinstance(value, str):
        return [value]
    return []


def validate_objects(root: str | Path, profile: int | None = None) -> list[ValidationIssue]:
    """Validate a bundle. Returns issues ordered by file."""
    root = Path(root)
    effective_profile = resolve_profile(root, profile)
    objects = load_objects(root)
    schema = _load_schema()
    issues: list[ValidationIssue] = []

    # ---- Build the reference index (concept paths, aliases, claim ids) ----
    known_refs: set[str] = set()
    alias_owners: dict[str, str] = {}
    for obj in objects:
        known_refs.update(obj.ref_keys)
        if obj.alias:
            if obj.alias in alias_owners:
                issues.append(ValidationIssue(
                    _gate(effective_profile, 1),
                    str(obj.path),
                    f"duplicate id alias also used by {alias_owners[obj.alias]}: {obj.alias}",
                ))
            alias_owners[obj.alias] = str(obj.path)
        for claim in parse_claims(obj.body):
            if claim.id:
                known_refs.add(claim.id)

    depends_graph: dict[str, list[str]] = {}

    for obj in objects:
        obj_profile = _object_profile(obj, effective_profile)
        p = str(obj.path)
        meta = obj.metadata

        # ---- OKF-level requirement (all profiles): non-empty type ----
        if not (isinstance(obj.type, str) and obj.type.strip()):
            issues.append(ValidationIssue("ERROR", p, "missing required field 'type' (OKF requirement)"))

        # ---- Structural schema conformance ----
        for err in jsonschema.Draft202012Validator(schema).iter_errors(_jsonable(meta)):
            loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
            issues.append(ValidationIssue(_gate(obj_profile, 1), p, f"schema: {loc}: {err.message}"))

        # ---- Type registry (informational; unknown types are tolerated) ----
        if isinstance(obj.type, str) and obj.type not in KNOWN_TYPES:
            issues.append(ValidationIssue("INFO", p, f"unregistered type '{obj.type}' (tolerated; type-specific checks skipped)"))

        # ---- ISO date hygiene ----
        for field_name in ("created", "last_verified", "valid_until", "timestamp"):
            if field_name in meta and not _is_valid_date(meta.get(field_name)):
                issues.append(ValidationIssue(_gate(obj_profile, 1), p, f"{field_name} is not a valid ISO 8601 date: {meta.get(field_name)!r}"))

        # ---- Ownership of live objects ----
        status = obj.status
        owners = _as_list(meta.get("owners"))
        if status in LIVE_STATUSES and not owners:
            issues.append(ValidationIssue(_gate(obj_profile, 1), p, f"{status} object must declare owners"))

        # ---- Lifecycle / freshness ----
        if status == "verified" and not meta.get("last_verified"):
            issues.append(ValidationIssue(_gate(obj_profile, 2), p, "verified object should declare last_verified"))
        valid_until = _parse_date(meta.get("valid_until"))
        if valid_until and valid_until < date.today():
            issues.append(ValidationIssue("WARNING", p, f"object is past valid_until: {valid_until}"))

        # ---- Reference resolution (typed frontmatter references) ----
        for fld in LIST_REF_FIELDS:
            refs = _as_list(meta.get(fld))
            for ref in refs:
                if ref not in known_refs:
                    issues.append(ValidationIssue(_gate(obj_profile, 1), p, f"unresolved {fld} reference: {ref}"))
            if fld == "depends_on":
                depends_graph[obj.display_id] = [r for r in refs]
        for fld in SCALAR_REF_FIELDS:
            sref = meta.get(fld)
            if isinstance(sref, str) and sref and sref not in known_refs:
                issues.append(ValidationIssue(_gate(obj_profile, 1), p, f"unresolved {fld} reference: {sref}"))

        # ---- Reciprocal supersession (Profile 2) ----
        sb = meta.get("superseded_by")
        if isinstance(sb, str) and sb and status not in {"superseded", "deprecated", "retracted", "archived"}:
            issues.append(ValidationIssue(_gate(obj_profile, 2), p, f"declares superseded_by {sb} but status is '{status}'"))

        # ---- Type-specific checks for known types ----
        issues.extend(_check_typed(obj, obj_profile))

        # ---- Claim blocks ----
        issues.extend(_check_claims(obj, obj_profile, known_refs))

    # ---- Dependency cycle detection ----
    issues.extend(_check_cycles(depends_graph, objects, effective_profile))

    return issues


def _gate(profile: int, error_at: int) -> str:
    """An issue is an ERROR at/above ``error_at``, else a WARNING."""
    return "ERROR" if profile >= error_at else "WARNING"


def _object_profile(obj: KnowledgeObject, bundle_profile: int) -> int:
    override = obj.metadata.get("profile")
    if isinstance(override, int) and 0 <= override <= 2:
        return override
    return bundle_profile


def _check_typed(obj: KnowledgeObject, profile: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    p = str(obj.path)
    meta = obj.metadata
    if obj.type == "metric":
        for fld in ("numerator", "denominator"):
            if not meta.get(fld):
                issues.append(ValidationIssue(_gate(profile, 2), p, f"metric should define '{fld}'"))
    if obj.type == "experiment":
        if not meta.get("verification") and not any(h in obj.body for h in ("## Method", "# Method")):
            issues.append(ValidationIssue("INFO", p, "experiment has no verification block or Method section"))
    return issues


def _check_claims(obj: KnowledgeObject, profile: int, known_refs: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    p = str(obj.path)
    for claim in parse_claims(obj.body):
        loc = f"{p}:{claim.start_line}"
        for err in claim.errors:
            issues.append(ValidationIssue(_gate(profile, 1), loc, f"claim block: {err}"))
        cid = claim.id
        if cid and not cid.startswith("claim:"):
            issues.append(ValidationIssue(_gate(profile, 1), loc, f"claim id should be of form claim:<slug>: {cid}"))
        confidence = claim.metadata.get("confidence")
        if confidence and confidence not in {"low", "medium", "high", "very_high"}:
            issues.append(ValidationIssue(_gate(profile, 1), loc, f"invalid claim confidence: {confidence}"))
        evidence = claim.metadata.get("evidence") or []
        if not evidence:
            issues.append(ValidationIssue(_gate(profile, 2), loc, "claim has no evidence"))
        else:
            for ev in evidence:
                src = ev.get("source") if isinstance(ev, dict) else None
                if isinstance(src, str) and ":" in src and src not in known_refs:
                    issues.append(ValidationIssue("WARNING", loc, f"claim evidence source does not resolve in bundle: {src}"))
    return issues


def _check_cycles(graph: dict[str, list[str]], objects: list[KnowledgeObject], profile: int) -> list[ValidationIssue]:
    # Map any ref key back to a canonical display id so edges line up.
    canonical: dict[str, str] = {}
    for obj in objects:
        for key in obj.ref_keys:
            canonical[key] = obj.display_id

    adj = {node: [canonical.get(t, t) for t in targets] for node, targets in graph.items()}
    issues: list[ValidationIssue] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}
    stack: list[str] = []

    def dfs(node: str) -> str | None:
        color[node] = GRAY
        stack.append(node)
        for nxt in adj.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                cycle = stack[stack.index(nxt):] + [nxt]
                return " -> ".join(cycle)
            if color[nxt] == WHITE:
                found = dfs(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    reported: set[str] = set()
    for node in adj:
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle and cycle not in reported:
                reported.add(cycle)
                issues.append(ValidationIssue(_gate(profile, 1), "<graph>", f"dependency cycle: {cycle}"))
    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.level == "ERROR" for issue in issues)


def summarize(issues: list[ValidationIssue]) -> dict[str, int]:
    out = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for issue in issues:
        out[issue.level] = out.get(issue.level, 0) + 1
    return out
