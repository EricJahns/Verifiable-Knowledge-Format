from vkf.permissions import can_use


def test_forbidden_use_denied():
    meta = {"access": {"forbidden_uses": ["public_release"]}}
    assert not can_use(meta, "public_release")


def test_allowlist_excludes_other_uses():
    meta = {"access": {"allowed_uses": ["internal_question_answering"]}}
    assert can_use(meta, "internal_question_answering")
    assert not can_use(meta, "public_release")


def test_confidential_blocked_from_external_by_default():
    meta = {"visibility": "confidential"}
    assert not can_use(meta, "public_release")
    assert can_use(meta, "internal_question_answering")


def test_role_denied():
    meta = {"access": {"denied_roles": ["contractor"]}}
    d = can_use(meta, "internal_question_answering", role="contractor")
    assert not d
    assert "contractor" in d.reason


def test_allowed_roles_gate():
    meta = {"access": {"allowed_roles": ["employee"]}}
    assert can_use(meta, "x", role="employee")
    assert not can_use(meta, "x", role="vendor")


def test_requires_review_allows_but_flags():
    meta = {"access": {"requires_review_for": ["public_release"]}, "visibility": "public"}
    d = can_use(meta, "public_release")
    assert d.allowed
    assert d.requires_review
