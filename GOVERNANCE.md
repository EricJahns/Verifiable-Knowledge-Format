# Governance Model

VKF is intended for knowledge that agents may act on. Governance is therefore part of the format, not an afterthought.

## Roles

- **Owner**: accountable for correctness and freshness.
- **Reviewer**: validates changes before promotion.
- **Maintainer**: manages schema, CI, and repository hygiene.
- **Agent**: can propose changes, detect issues, and generate derived artifacts, but should not silently make authoritative changes.

## Promotion flow

```text
draft -> active -> verified
             \-> stale -> deprecated -> archived
             \-> disputed -> resolved
```

## Agent edits

Agent edits should create transaction records under `examples/transactions/` or the equivalent production directory.

A transaction should include:

- actor
- action
- target object
- reason
- evidence used
- changed fields
- whether human approval is required

## Public release rule

No public artifact should cite an evidence object whose visibility is `confidential`, `restricted`, or `private` unless an explicit policy allows it.
