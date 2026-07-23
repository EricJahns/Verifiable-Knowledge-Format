---
name: vkf-propose
description: Propose new or changed knowledge into a VKF (Verifiable Knowledge Format) bundle safely — draft the object, validate it, write the required transaction record, and hand off for human review. Use whenever a task asks you to add, update, or correct knowledge in a VKF bundle. Never promotes anything to active/verified — that step is always a human's.
---

# Propose into a VKF bundle

Your job: draft knowledge as `status: draft`, prove it validates, leave an
audit trail, and hand off to a human. You never self-promote.

## 1. Search first (avoid duplicates and silent conflicts)

Use the **vkf-retrieve** access path before drafting anything:

```bash
vkf search <root> "<topic>" --use internal_question_answering --json
vkf list <root> --type <type> --json
```

- If an equivalent object already exists, update/extend it instead of duplicating.
- If anything in the bundle would `conflicts_with` your new claim, **surface
  it** in your draft and transaction — don't silently pick a side or bury it.

## 2. Pick the object type and copy its template

```bash
cp templates/<type>.md <root>/<folder>/<slug>.md
```

Types available: `concept`, `claim`, `decision`, `policy`, `runbook`,
`dataset`, `metric`, `experiment`, `transaction`.

- **Identity is the file path** (OKF rule) — place it in the right
  type/domain folder and name it with a slug that matches the title (see
  AUTHORING.md's naming section). Don't rename an existing alias just because
  wording changed.
- Optionally give it a stable alias, `id: <type>:<slug>`, so other files can
  reference it even if the path moves later.

## 3. Fill required frontmatter

- `status: draft` — **mandatory**. Never set `active` or `verified` on your
  own work, no matter how confident you are.
- `owners` — the human/team accountable, even though they haven't reviewed yet.
- Dates in ISO format (`created`, etc.).
- Typed refs that actually resolve: `depends_on`, `conflicts_with`, `supersedes`.
- `visibility` + `access.allowed_uses`/`forbidden_uses` if the content has any
  sensitivity (confidential data, PII, restricted use).
- For `claim` objects targeting Profile 2: include a `:::claim` block with
  `confidence` and `evidence` (each with `source` and `strength`).

## 4. Validate before proposing

```bash
vkf validate <root>              # must pass at the bundle's declared profile
vkf validate <root> --profile 2  # try the strict bar too if the bundle targets it
```

Fix every error before moving on. Warnings are worth reading but won't block CI.

## 5. Always write a transaction record

Never skip this — it's the audit trail, not optional.

```bash
cp templates/transaction.md <root>/transactions/<date>-<slug>.md
```

Fill in:
- `actor`, `action`, `target` (the object id you created/changed)
- `reason` — why, and what evidence motivated it
- `evidence` — source + strength
- `requires_human_approval: true`
- `changed_fields` — precise list of what changed
- Body sections: what you did, what you deliberately did **not** do, what a
  human must do to promote it.

## 6. What you must never do

- Silently mark a claim `verified` (or any object `active`/`verified`).
- Remove conflicting evidence without human review.
- Upgrade restricted/confidential content into public output.
- Modify canonical (non-draft) knowledge without a transaction record.
- Promote your own draft — that decision belongs to a human owner.

## 7. Hand off

Open a PR with the new/changed object(s) plus the transaction record (or hand
the diff to your host to open one). A human owner reviews and — if it holds up
— promotes `draft → active → verified`. You're done once the PR is open and
the transaction record accurately describes what you did.

## 8. Worked example (the canonical pair in this repo)

- `examples/claims/activation-predicts-retention.md` — an agent-drafted claim,
  `status: draft`, with a `:::claim` block (`confidence: medium`, evidence
  `dataset:user_events` at `moderate` strength).
- `examples/transactions/2026-06-24-propose-activation-claim.md` — its
  transaction: `actor: agent:knowledge-curator`, `action: created`,
  `target: claim:activation_predicts_retention`, `requires_human_approval:
  true`, explicit "what it did NOT do" section (didn't mark it active/verified,
  didn't touch existing objects, didn't remove conflicting evidence).

Both validate cleanly:

```bash
vkf validate examples --format json   # 0 errors at Profile 1
```

This pair is what a correct agent PR into a VKF bundle looks like — use it as
the template for structure and tone, not just the file layout.
