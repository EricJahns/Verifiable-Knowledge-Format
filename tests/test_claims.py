from vkf.claims import parse_claims


def test_parse_well_formed_claim():
    body = """
Intro text.

:::claim
---
id: claim:example
confidence: high
evidence:
  - source: dataset:x
    strength: strong
---
The body of the claim.
:::

Trailing text.
"""
    claims = parse_claims(body)
    assert len(claims) == 1
    c = claims[0]
    assert c.id == "claim:example"
    assert c.metadata["confidence"] == "high"
    assert c.metadata["evidence"][0]["source"] == "dataset:x"
    assert c.text == "The body of the claim."
    assert not c.errors


def test_parse_claim_without_metadata():
    body = ":::claim\nA bare assertion.\n:::"
    claims = parse_claims(body)
    assert len(claims) == 1
    assert claims[0].metadata == {}
    assert claims[0].text == "A bare assertion."
    assert not claims[0].errors


def test_unclosed_claim_reports_error():
    body = ":::claim\n---\nid: claim:x\n---\nnever closed"
    claims = parse_claims(body)
    assert len(claims) == 1
    assert any("not closed" in e for e in claims[0].errors)


def test_unclosed_metadata_reports_error():
    body = ":::claim\n---\nid: claim:x\nbody\n:::"
    claims = parse_claims(body)
    assert claims[0].errors


def test_multiple_claims():
    body = ":::claim\nfirst\n:::\n\n:::claim\nsecond\n:::"
    claims = parse_claims(body)
    assert [c.text for c in claims] == ["first", "second"]


def test_no_claims():
    assert parse_claims("# Just a heading\n\nProse.") == []
