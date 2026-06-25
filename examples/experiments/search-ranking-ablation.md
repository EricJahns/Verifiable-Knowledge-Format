---
vkf_version: 0.2.0
id: experiment:search_ranking_ablation
type: experiment
title: Search Ranking Ablation
summary: Compares baseline ranking against feature-enhanced ranking.
status: draft
owners:
  - team:search
visibility: internal
created: 2026-06-24
last_verified:
valid_until: 2026-08-24
depends_on:
  - dataset:user_events
confidence: medium
verification:
  command: python experiments/search_ranking_ablation.py
  expected:
    ndcg_delta_min: 0.01
  artifacts:
    - results/search_ranking_ablation.json
---

# Search Ranking Ablation

This experiment compares baseline ranking against a feature-enhanced ranking model.

## Result

Preliminary results suggest a positive NDCG lift, but the object is still marked draft until reproduced.
