"""VKF — Verifiable Knowledge Format.

A Git-native, human-readable, agent-operable knowledge format. VKF is a strict
superset of Google's Open Knowledge Format (OKF) v0.1 that adds a trust and
governance layer: provenance, evidence, confidence, lifecycle/freshness,
contextual permissions, typed relationships, executable verification, and
opt-in conformance profiles with validation teeth.
"""

from __future__ import annotations

__version__ = "0.4.0"

from .loader import KnowledgeObject, load_object, load_objects  # noqa: E402

__all__ = ["KnowledgeObject", "load_object", "load_objects", "__version__"]
