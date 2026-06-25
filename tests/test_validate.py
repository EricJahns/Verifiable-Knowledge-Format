import textwrap

import pytest

from vkf.validate import has_errors, validate_objects


def write(root, relpath, text):
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).lstrip())
    return p


def test_okf_minimal_passes_every_profile(tmp_path):
    # An OKF concept with only `type` must validate at all profiles (superset).
    write(tmp_path, "concepts/thing.md", """
        ---
        type: concept
        title: A Thing
        ---
        Body.
    """)
    for profile in (0, 1, 2):
        assert not has_errors(validate_objects(tmp_path, profile=profile))


def test_missing_type_fails_at_profile_0(tmp_path):
    # The one OKF requirement is enforced even at the most permissive profile.
    write(tmp_path, "concepts/notype.md", """
        ---
        title: No type here
        ---
        Body.
    """)
    issues = validate_objects(tmp_path, profile=0)
    assert has_errors(issues)
    assert any("type" in i.message for i in issues if i.level == "ERROR")


def test_active_without_owners_is_warning_at_0_error_at_1(tmp_path):
    write(tmp_path, "concepts/live.md", """
        ---
        type: concept
        title: Live
        status: active
        ---
        Body.
    """)
    assert not has_errors(validate_objects(tmp_path, profile=0))
    assert has_errors(validate_objects(tmp_path, profile=1))


def test_dangling_typed_reference_errors_at_governed(tmp_path):
    write(tmp_path, "concepts/a.md", """
        ---
        type: concept
        title: A
        status: active
        owners: [team:x]
        depends_on: [concept:does_not_exist]
        ---
        Body.
    """)
    assert has_errors(validate_objects(tmp_path, profile=1))
    assert not has_errors(validate_objects(tmp_path, profile=0))


def test_path_reference_resolves(tmp_path):
    write(tmp_path, "a.md", """
        ---
        type: concept
        status: active
        owners: [team:x]
        depends_on: [b]
        ---
    """)
    write(tmp_path, "b.md", """
        ---
        type: concept
        status: active
        owners: [team:x]
        ---
    """)
    # `b` resolves by path identity even with no `id` alias.
    assert not has_errors(validate_objects(tmp_path, profile=1))


def test_bad_date_errors_at_governed(tmp_path):
    write(tmp_path, "c.md", """
        ---
        type: concept
        status: active
        owners: [team:x]
        last_verified: "not-a-date"
        ---
    """)
    issues = validate_objects(tmp_path, profile=1)
    assert any("ISO 8601" in i.message for i in issues)
    assert has_errors(issues)


def test_dependency_cycle_detected(tmp_path):
    write(tmp_path, "a.md", """
        ---
        type: concept
        id: concept:a
        status: active
        owners: [team:x]
        depends_on: [concept:b]
        ---
    """)
    write(tmp_path, "b.md", """
        ---
        type: concept
        id: concept:b
        status: active
        owners: [team:x]
        depends_on: [concept:a]
        ---
    """)
    issues = validate_objects(tmp_path, profile=1)
    assert any("cycle" in i.message for i in issues)


def test_duplicate_alias_errors(tmp_path):
    for name in ("a.md", "b.md"):
        write(tmp_path, name, """
            ---
            type: concept
            id: concept:dup
            ---
        """)
    issues = validate_objects(tmp_path, profile=1)
    assert any("duplicate id alias" in i.message for i in issues)


def test_unregistered_type_is_tolerated(tmp_path):
    write(tmp_path, "x.md", """
        ---
        type: BigQuery Table
        title: Orders
        ---
    """)
    issues = validate_objects(tmp_path, profile=1)
    assert not has_errors(issues)
    assert any(i.level == "INFO" and "unregistered" in i.message for i in issues)


def test_claim_without_evidence_errors_only_at_verified(tmp_path):
    write(tmp_path, "m.md", """
        ---
        type: concept
        status: active
        owners: [team:x]
        ---
        :::claim
        ---
        id: claim:bare
        confidence: high
        ---
        An assertion with no evidence.
        :::
    """)
    assert not has_errors(validate_objects(tmp_path, profile=1))
    assert has_errors(validate_objects(tmp_path, profile=2))


def test_per_document_profile_override(tmp_path):
    write(tmp_path, "strict.md", """
        ---
        type: concept
        title: Strict
        status: active
        profile: 1
        ---
    """)
    # Bundle defaults to profile 0, but the document opts into 1 and fails (no owners).
    assert has_errors(validate_objects(tmp_path, profile=0))
