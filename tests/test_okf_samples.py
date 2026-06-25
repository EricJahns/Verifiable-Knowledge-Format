"""Proof of the 'strict superset of OKF' claim against REAL OKF bundles.

These fixtures (tests/okf_samples/) are unmodified OKF concept documents from
Google Cloud's knowledge-catalog repository (see okf_samples/NOTICE.md). The
guarantee VKF makes is: every conformant OKF bundle is a conformant VKF bundle
at Profile 0. This pins that guarantee to Google's actual published samples, not
just hand-written fixtures.
"""

from pathlib import Path

from vkf.interop import okf_conformance
from vkf.validate import has_errors, summarize, validate_objects

SAMPLES = Path(__file__).resolve().parent / "okf_samples" / "bundle"


def test_real_okf_bundle_is_structurally_okf_conformant():
    assert okf_conformance(SAMPLES) == []


def test_real_okf_bundle_validates_at_profile_0():
    # The superset guarantee: a real OKF bundle has zero errors at Profile 0.
    issues = validate_objects(SAMPLES, profile=0)
    assert not has_errors(issues), "\n".join(str(i) for i in issues)


def test_freeform_okf_types_are_tolerated_not_rejected():
    # Google's samples use freeform types like "BigQuery Dataset" / "BigQuery
    # Table". VKF must tolerate them (INFO), never error on them.
    issues = validate_objects(SAMPLES, profile=0)
    assert any(i.level == "INFO" and "unregistered type" in i.message for i in issues)
    assert not any(i.level == "ERROR" for i in issues)


def test_profile_1_flags_real_world_okf_drift():
    # Honest finding from real data: Google's stackoverflow sample encodes `tags`
    # as a comma-string rather than a YAML list. Profile 0 tolerates it (the OKF
    # 'never reject' rule); the opt-in governed profile surfaces it. This asserts
    # the profile model behaves differently on the *same* real bundle.
    p0 = summarize(validate_objects(SAMPLES, profile=0))
    p1 = summarize(validate_objects(SAMPLES, profile=1))
    assert p0["ERROR"] == 0
    assert p1["ERROR"] >= 1
