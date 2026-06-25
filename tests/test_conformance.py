"""Runs the validator against the committed conformance corpus.

Each case under conformance/cases/ has an expected outcome (pass/error) at each
profile in conformance/expectations.yaml. This is what makes VKF a *standard*
rather than just a library: the reference validator's behavior is pinned to a
shared, inspectable corpus.
"""

from pathlib import Path

import pytest
import yaml

from vkf.validate import has_errors, validate_objects

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "conformance" / "cases"
EXPECTATIONS = yaml.safe_load((ROOT / "conformance" / "expectations.yaml").read_text())


def _params():
    for case, profiles in EXPECTATIONS.items():
        for profile, expected in profiles.items():
            yield pytest.param(case, int(profile), expected, id=f"{case}-p{profile}")


@pytest.mark.parametrize("case,profile,expected", list(_params()))
def test_conformance_case(case, profile, expected):
    issues = validate_objects(CASES / case, profile=profile)
    got = "error" if has_errors(issues) else "pass"
    assert got == expected, (
        f"{case} at profile {profile}: expected {expected}, got {got}\n"
        + "\n".join(str(i) for i in issues)
    )


def test_every_case_directory_has_expectations():
    case_dirs = {p.name for p in CASES.iterdir() if p.is_dir()}
    assert case_dirs == set(EXPECTATIONS), "case dirs and expectations.yaml are out of sync"
