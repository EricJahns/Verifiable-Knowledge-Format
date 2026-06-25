---
vkf_version: 0.2.0
id: transaction:propose_activation_claim_20260624
type: transaction
title: "Proposed: claim:activation_predicts_retention (draft)"
visibility: internal
created: 2026-06-24
actor: agent:knowledge-curator
action: created
target: claim:activation_predicts_retention
timestamp: 2026-06-24T15:30:00Z
reason: >-
  Agent observed a correlation in dataset:user_events and drafted a new claim.
  Submitted as draft for owner review; not authoritative until a human verifies it.
evidence:
  - source: dataset:user_events
    strength: moderate
requires_human_approval: true
changed_fields:
  - "created claim:activation_predicts_retention (status: draft)"
---

# Transaction: proposed new claim

A record of an agent-proposed change, demonstrating the **propose-don't-promote**
flow (see [docs/AUTHORING.md](../../docs/AUTHORING.md) and
[GOVERNANCE.md](../../GOVERNANCE.md)).

## What the agent did

Drafted `claim:activation_predicts_retention` (status `draft`) from a correlation
observed in `dataset:user_events`, and opened it for review.

## What it did NOT do

- It did **not** mark the claim `active` or `verified`.
- It did **not** modify any existing authoritative object.
- It did **not** remove or override conflicting evidence.

## What a human must do

An owner on `team:analytics` validates the correlation (and checks for
confounders), then promotes the claim `draft → active`/`verified` — or rejects
it. Until then, agents must not treat the claim as authoritative
(`requires_human_approval: true`).
