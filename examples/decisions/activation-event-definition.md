---
vkf_version: 0.2.0
id: decision:activation_event_definition
type: decision
title: Activation Event Definition
summary: Defines the event that counts as user activation.
status: verified
owners:
  - team:product
visibility: internal
created: 2026-06-24
last_verified: 2026-06-24
valid_until: 2026-12-31
depends_on:
  - dataset:user_events
---

# Activation Event Definition

## Decision

A user is considered activated when they complete the first successful project creation event.

## Rationale

This event is more stable than login, page view, or onboarding-start events because it reflects meaningful product value.

## Alternatives considered

- First login
- First invite sent
- First dashboard view
