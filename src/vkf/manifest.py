"""Bundle manifest and conformance profiles.

A VKF bundle may carry a ``vkf.bundle.yaml`` manifest at its root declaring,
among other things, the *conformance profile* the bundle targets. Profiles are
how VKF adds validation teeth without violating OKF's "consumers MUST NOT
reject" rule: Profile 0 is pure OKF (never errors), higher profiles are opt-in
contracts that *may* fail validation.

    Profile 0  okf-compatible  Structural OKF conformance only. Never errors.
    Profile 1  governed        + owners, ISO dates, resolvable typed refs,
                               unique ids, lifecycle sanity.
    Profile 2  verified        + evidence on claims, last_verified on verified
                               objects, no dangling references of any kind,
                               reciprocal supersession.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MANIFEST_NAMES = ("vkf.bundle.yaml", "vkf.bundle.yml")

PROFILE_OKF_COMPATIBLE = 0
PROFILE_GOVERNED = 1
PROFILE_VERIFIED = 2

PROFILE_NAMES = {
    0: "okf-compatible",
    1: "governed",
    2: "verified",
}

DEFAULT_PROFILE = PROFILE_GOVERNED


@dataclass
class BundleManifest:
    path: Path | None
    data: dict[str, Any]

    @property
    def profile(self) -> int:
        value = self.data.get("profile", DEFAULT_PROFILE)
        try:
            value = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PROFILE
        return max(0, min(2, value))


def find_manifest(root: str | Path) -> Path | None:
    root = Path(root)
    for name in MANIFEST_NAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def load_manifest(root: str | Path) -> BundleManifest:
    path = find_manifest(root)
    if path is None:
        return BundleManifest(path=None, data={})
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return BundleManifest(path=path, data=data)


def resolve_profile(root: str | Path, override: int | None = None) -> int:
    """Effective bundle profile: explicit override wins, else manifest."""
    if override is not None:
        return max(0, min(2, override))
    return load_manifest(root).profile
