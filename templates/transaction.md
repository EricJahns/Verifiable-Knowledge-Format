---
vkf_version: 0.2.0
id: transaction:replace_me
type: transaction
title: "Replace me: describe the change"
visibility: internal
created: 2026-06-24
actor: agent:replace_me
action: created
target: replace_me
timestamp: 2026-06-24T00:00:00Z
reason: >-
  Replace with a concise explanation of why this change was made and what
  evidence motivated it.
evidence:
  - source: replace_me
    strength: moderate
requires_human_approval: true
changed_fields:
  - "replace_me: describe the specific field(s) or object(s) changed"
---

# Transaction: replace me

A record of a human or agent edit, following the **propose-don't-promote** flow
(see [docs/AUTHORING.md](../docs/AUTHORING.md) and
[GOVERNANCE.md](../GOVERNANCE.md)).

## What the actor did

Describe the change: what was created, updated, or proposed, and its status
after this transaction.

## What it did NOT do

- List anything the actor deliberately avoided doing (e.g. did not promote a
  claim to `active`/`verified`, did not modify an existing authoritative
  object, did not resolve a conflict).

## What a human must do

If `requires_human_approval` is `true`, describe who must review the change,
what they need to check, and what happens once it is approved or rejected.
