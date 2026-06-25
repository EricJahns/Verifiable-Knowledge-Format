---
vkf_version: 0.2.0
id: runbook:database_failover
type: runbook
title: Database Failover
summary: Steps for promoting the read replica during primary database outage.
status: active
owners:
  - team:infrastructure
visibility: internal
created: 2026-06-24
last_verified: 2026-06-24
valid_until: 2026-09-24
depends_on:
  - policy:public_release
---

# Database Failover

## Trigger

Use this runbook when the primary database is unavailable for more than five minutes.

## Steps

1. Confirm primary outage.
2. Pause write-heavy jobs.
3. Promote the read replica.
4. Update service configuration.
5. Validate application health.

## Rollback

If promotion fails, restore the previous configuration and escalate.

## Escalation

Contact the infrastructure on-call lead.
