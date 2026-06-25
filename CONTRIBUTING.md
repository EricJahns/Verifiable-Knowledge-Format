# Contributing

VKF treats knowledge like code. Contributions should be readable by humans and useful to agents.

New here? **[docs/AUTHORING.md](docs/AUTHORING.md)** is the step-by-step how-to
for creating a knowledge file and getting it merged. This page is the checklist
each file must pass before review.

## Contribution checklist

Before opening a pull request:

- Every file has valid YAML frontmatter.
- Every object has a stable `id`.
- Every object has a valid `type`.
- Every object has an `owner`.
- Every active claim has evidence or is explicitly marked as an assumption.
- Every object has a lifecycle `status`.
- Public-facing content does not cite confidential or restricted evidence.
- Deprecated objects name their replacement when possible.
- Metrics define numerator, denominator, and owner.
- Policies define scope and enforcement.
- Runbooks define triggers, steps, rollback, and escalation.

## Human review

Agent-generated changes should be reviewed by a human owner before being marked `verified` or `active`.

## Object ID style

Use namespaced IDs:

```text
claim:customer_churn_driven_by_price
metric:gross_margin
policy:data_retention
runbook:database_failover
decision:pricing_model_v2
```

IDs should be stable. Do not rename an ID just because the title changes.
