---
vkf_version: 0.2.0
id: policy:public_release
type: policy
title: Public Release Policy
summary: Rules for using internal knowledge in public artifacts.
status: active
owners:
  - team:legal
  - team:security
visibility: internal
created: 2026-06-24
last_verified: 2026-06-24
valid_until: 2026-12-31
tags: [governance, security]
---

# Public Release Policy

Public artifacts must not cite or quote confidential, restricted, or private sources unless a documented exception exists.

## Enforcement

Knowledge CI should fail if a public object directly depends on confidential, restricted, or private evidence.
