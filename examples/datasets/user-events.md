---
vkf_version: 0.2.0
id: dataset:user_events
type: dataset
title: User Events
summary: Product event stream used for growth and activation metrics.
status: active
owners:
  - team:data-platform
visibility: confidential
created: 2026-06-24
last_verified: 2026-06-24
valid_until: 2026-09-24
tags: [events, product, analytics]
license: internal-use-only
lineage:
  source_system: product_event_pipeline
  refresh: daily
access:
  allowed_uses:
    - internal_question_answering
    - internal_strategy
  forbidden_uses:
    - public_release
    - model_training
---

# User Events

The user events dataset stores product interaction events. It is used by growth, analytics, and experimentation workflows.

## Access

This dataset is confidential and should not be quoted in public-facing materials.
