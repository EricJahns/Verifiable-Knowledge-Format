---
vkf_version: 0.2.0
id: metric:activation_rate
type: metric
title: Activation Rate
summary: Fraction of new users who complete the activation event within seven days.
status: active
owners:
  - team:analytics
visibility: internal
created: 2026-06-24
last_verified: 2026-06-24
valid_until: 2026-12-31
tags: [growth, analytics]
depends_on:
  - dataset:user_events
  - decision:activation_event_definition
numerator: New users who complete the activation event within seven days of signup.
denominator: Total new users in the same cohort.
---

# Activation Rate

Activation rate measures the fraction of new users who complete the activation
event within seven days of signup.

:::claim
---
id: claim:activation_rate_definition
confidence: high
evidence:
  - source: dataset:user_events
    type: dataset
    strength: strong
  - source: decision:activation_event_definition
    type: decision
    strength: definitive
---
Activation rate is defined as activated new users divided by total new users
in the same signup cohort.
:::
