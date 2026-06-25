---
vkf_version: 0.3.0
id: metric:activation_window
type: metric
title: Activation Window
summary: Activation window definition.
status: verified
owners:
  - team:analytics
visibility: internal
created: 2026-02-01
last_verified: 2026-05-01
valid_until: 2026-12-31
supersedes:
  - metric:activation_window_v1
---

# Activation Window

The activation window is 14 days: a user is counted as activated if they
complete the activation event within 14 days of signup.
