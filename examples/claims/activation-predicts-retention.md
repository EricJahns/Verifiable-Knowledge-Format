---
vkf_version: 0.2.0
id: claim:activation_predicts_retention
type: claim
title: Early Activation Predicts Retention
summary: Users who activate within the window retain at higher rates (drafted by an agent, pending review).
status: draft
owners:
  - team:analytics
visibility: internal
created: 2026-06-24
depends_on:
  - dataset:user_events
  - metric:activation_rate
confidence: medium
---

# Early Activation Predicts Retention

This claim was **drafted by an agent** from a correlation observed in the user
events data. It is `draft` and not authoritative until an owner verifies it. See
the accompanying record in `examples/transactions/`.

:::claim
---
id: claim:activation_predicts_retention_value
confidence: medium
evidence:
  - source: dataset:user_events
    type: dataset
    strength: moderate
---
New users who complete the activation event within the activation window retain
at a higher 90-day rate than those who do not.
:::
