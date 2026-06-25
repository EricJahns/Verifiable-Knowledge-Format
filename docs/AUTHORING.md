# Authoring & Integrating Knowledge

This is the practical "how do I add knowledge?" guide. For the *rules* a file
must satisfy see [CONTRIBUTING.md](../CONTRIBUTING.md); for *who* may promote it
see [GOVERNANCE.md](../GOVERNANCE.md); for field meanings see
[SPEC.md](SPEC.md). This page is the workflow that connects them.

## Who creates knowledge files

Two kinds of author, with the same end state but different trust on the way in:

- **A human owner** — a person on the team accountable for a domain (analytics,
  legal, infra…). They author the file directly and own its correctness.
- **An AI agent** — drafts or updates a file and *proposes* it. **An agent never
  promotes its own work to `active`/`verified`** (see GOVERNANCE → Roles). It
  opens the change for a human owner to review, and records what it did.

In both cases a knowledge file is **just a Markdown file in Git**. "Integrating"
it means the normal Git path — create → validate → review → merge — with VKF's
validator as a gate. No database, no special tool, no import step.

## The lifecycle a file moves through

```
draft ──▶ active ──▶ verified
  │           └──▶ stale ──▶ deprecated/superseded ──▶ archived
  └──▶ (abandoned drafts can be deleted)
```

- **`draft`** — author is still writing; agents must not treat it as authoritative.
- **`active`** — usable; an owner stands behind it. Requires `owners` at Profile 1.
- **`verified`** — checked and trusted; requires `last_verified` at Profile 2.
- Later, freshness/lifecycle moves it to `stale`, `deprecated`/`superseded`, `archived`.

You set `status` in frontmatter; promotion is a deliberate edit a human makes
(often the moment a reviewer approves the PR).

## Step by step: add a new knowledge file

### 1. Start from a template (or scaffold a bundle)

```bash
# An existing bundle — copy the closest template into the right folder:
cp templates/metric.md examples/metrics/net-revenue-retention.md

# A brand-new bundle:
vkf init my-bundle          # writes vkf.bundle.yaml + concepts/example.md
```

`templates/` has one starter per object type (`concept`, `claim`, `decision`,
`policy`, `runbook`, `dataset`, `metric`, `experiment`).

### 2. Put it in the right place and name it

- **Identity is the file path** (OKF rule): `examples/metrics/net-revenue-retention.md`
  → concept id `metrics/net-revenue-retention`. Group by type/domain in folders.
- Optionally add a **stable alias** `id: metric:net_revenue_retention` so other
  files can reference it even if the file moves. Aliases are `<type>:<slug>` and
  must be unique. Don't rename an alias just because the title changed.

### 3. Fill in the frontmatter

The only field OKF/Profile 0 requires is `type`. For a **governed** bundle
(Profile 1), live objects also need `owners`; Profile 2 adds evidence on claims
and `last_verified` on verified objects. A typical new metric:

```markdown
---
type: metric
id: metric:net_revenue_retention
title: Net Revenue Retention
status: draft                 # start as draft
owners: [team:analytics]      # who is accountable
visibility: internal
created: 2026-06-24
depends_on: [dataset:user_events]
numerator: Revenue this period from cohorts active last period.
denominator: Revenue last period from those same cohorts.
---

# Net Revenue Retention

NRR measures expansion net of churn for an existing cohort…
```

Mark important assertions as **claim blocks** so they carry their own evidence
(see [SPEC.md](SPEC.md) §8). Reference other concepts with typed relations
(`depends_on`, `supersedes`, `conflicts_with`) or plain Markdown links.

### 4. Validate locally

```bash
vkf validate examples              # profile read from examples/vkf.bundle.yaml
vkf validate examples --profile 2  # try the strictest bar before review
vkf freshness examples             # sanity-check dates
```

Fix any errors. At Profile 1 the validator will catch missing owners, dangling
references, bad dates, dependency cycles, and malformed claim blocks.

### 5. Open a pull request

Commit the file and open a PR. **Knowledge CI** (`.github/workflows/knowledge-ci.yml`)
runs the same `vkf validate`, the tests, and the OKF round-trip on every PR — so
a broken reference or an unowned `active` object fails the build, just like a
failing unit test. Work against the checklist in [CONTRIBUTING.md](../CONTRIBUTING.md).

### 6. Review and promote

A human **owner/reviewer** reads the PR. On approval they (or the author) bump
`status` `draft → active`, and to `verified` once the facts are checked
(setting `last_verified`). This human step is the point of the format: **agents
propose, humans approve authority.** Merge.

### 7. It's integrated — now it compiles

Once merged, the file *is* the knowledge base. Downstream consumers recompile
from the canonical Markdown:

```bash
vkf graph examples --out graph.json   # typed + claim-evidence edges
vkf html  examples --out graph.html   # offline visualizer
vkf serve examples                    # permission-aware retrieval API for agents
```

Nothing else "ingests" the file — these are projections of the source of truth.

## How an agent contributes (the propose-don't-promote path)

1. The agent drafts or edits a file with `status: draft` and opens a PR (or hands
   the diff to its host to open one).
2. It records what it did as a `transaction` object (see GOVERNANCE → Agent
   edits): actor, action, target, reason, evidence used, and whether human
   approval is required.
3. A human owner reviews and promotes. The agent does **not** set `verified`/`active`
   on its own work, remove conflicting evidence without review, or push restricted
   content into public output.

This keeps the audit trail and the authority decision with people, while letting
agents do the drafting, conflict-spotting, and summarizing.

**A worked artifact lives in the repo:** the agent-drafted claim
[`examples/claims/activation-predicts-retention.md`](../examples/claims/activation-predicts-retention.md)
(status `draft`) and its proposal record
[`examples/transactions/2026-06-24-propose-activation-claim.md`](../examples/transactions/2026-06-24-propose-activation-claim.md).
Together they show exactly what an agent's PR looks like: a new draft object plus
a `transaction` that says what it did, what it deliberately did *not* do, and what
a human must do to promote it. Both validate at Profile 2.

## Quick reference

| I want to… | Do this |
|---|---|
| Start a new bundle | `vkf init <dir>` |
| Add an object | copy `templates/<type>.md` into the right folder, edit frontmatter |
| Check it before review | `vkf validate <root>` (add `--profile 2` for the strict bar) |
| See what's stale | `vkf freshness <root>` |
| Check if it's safe to share | `vkf check <file> --use public_release` |
| Integrate it | open a PR; CI validates; an owner reviews and promotes |
| Use it downstream | `vkf graph` / `vkf html` / `vkf serve` |
