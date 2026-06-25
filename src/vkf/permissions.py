"""Contextual permission checks.

Knowing something internally does not mean an agent may quote it externally,
send it to another tool, or train on it. VKF attaches contextual ``access``
rules to objects and this module answers: *may this object be used in this
context, by this role?*
"""

from __future__ import annotations

from dataclasses import dataclass

VISIBILITY_ORDER = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
    "private": 4,
}

#: Use contexts that imply leaving the trust boundary.
EXTERNAL_USE_CONTEXTS = {"public_release", "external_sharing", "training_data"}

#: Visibilities that must never flow to an external context by default.
NON_EXTERNAL_VISIBILITY = {"confidential", "restricted", "private"}


@dataclass
class Decision:
    allowed: bool
    reason: str
    requires_review: bool = False

    def __bool__(self) -> bool:
        return self.allowed


def can_use(metadata: dict, use_context: str, role: str | None = None) -> Decision:
    access = metadata.get("access") or {}
    forbidden = set(access.get("forbidden_uses") or [])
    allowed = set(access.get("allowed_uses") or [])
    allowed_roles = set(access.get("allowed_roles") or [])
    denied_roles = set(access.get("denied_roles") or [])
    requires_review_for = set(access.get("requires_review_for") or [])
    visibility = metadata.get("visibility")

    if role and role in denied_roles:
        return Decision(False, f"role '{role}' is explicitly denied")
    if allowed_roles and role is not None and role not in allowed_roles:
        return Decision(False, f"role '{role}' is not in allowed_roles")

    if use_context in forbidden:
        return Decision(False, f"use context '{use_context}' is forbidden")
    if allowed and use_context not in allowed:
        return Decision(False, f"use context '{use_context}' is not in allowed_uses")

    if use_context in EXTERNAL_USE_CONTEXTS and visibility in NON_EXTERNAL_VISIBILITY:
        return Decision(False, f"{visibility} visibility cannot be used for '{use_context}' by default")

    if use_context in requires_review_for:
        return Decision(True, f"allowed but '{use_context}' requires human review", requires_review=True)

    return Decision(True, "allowed")
