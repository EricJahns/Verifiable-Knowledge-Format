---
name: vkf-retrieve
description: Find and cite information in a VKF (Verifiable Knowledge Format) bundle — a Git-native knowledge base of Markdown + YAML objects with governance metadata (status, owners, visibility, evidence). Use whenever a task needs an answer sourced from a VKF bundle, including checking whether something already exists before writing new knowledge into one.
---

# Retrieve from a VKF bundle

Your job: get the right answer out of a VKF bundle, respect its governance
metadata, and cite what you used. Never claim a governance check happened if it
didn't.

## 1. Pick the access path (in priority order)

1. **MCP tools already in this session** (`search`, `get_concept`,
   `list_concepts`, `freshness`, `graph`, `validate`, `check_permission`) —
   prefer these. They're backed by the same permission-aware service as the
   CLI, so filtering is automatic.
2. **No MCP, but `vkf` is installed** — use the core CLI (all commands below
   accept `--json` for structured output; drop it for human-readable text):
   ```bash
   vkf validate <root>                                          # profile + issues
   vkf search <root> "<query>" --use <context> --json            # --role, --limit, --include-denied also available
   vkf get <root> <ref> --json                                   # ref = id, alias, or path (no .md)
   vkf list <root> --type <type> --status <status> --tag <tag> --json
   vkf freshness <root>
   vkf graph <root> --out graph.json                             # typed relationship graph (--typed-only to drop body links)
   ```
3. **Last resort — no `vkf` and no MCP** — read the raw Markdown/YAML
   frontmatter directly. **Say so explicitly in your answer**: profile
   guarantees, permission filtering, and freshness checks were NOT enforced,
   so don't claim you checked access or trust rules — you didn't, a human did
   not review it through the tool, and the object may not even be well-formed.

## 2. Check the bundle's declared profile first

Read `profile` from `vkf.bundle.yaml` (or the `profile`/`profile_name` field in
`vkf validate --format json` output / the `validate` MCP tool). This tells you
what you're allowed to trust:

| Profile | Guarantees | Don't over-trust |
|---|---|---|
| 0 `okf-compatible` | only that every object has a `type` | treat `status`, `owners`, refs as best-effort/unverified |
| 1 `governed` | live objects have owners; dates valid; typed refs resolve; no dependency cycles; claim blocks well-formed | you may trust `status`/`owners`/the typed graph |
| 2 `verified` | + claims carry evidence; `verified` objects carry `last_verified` | below 2, don't present evidence/freshness as confidently checked |

## 3. Retrieval rules (apply every time)

- Prefer `verified`/`active` objects over other statuses.
- **Warn** when you must use `stale`, `draft`, `deprecated`, `superseded`,
  `disputed`, or `retracted` objects — say so in the answer, don't silently use them.
- Always pass `--use <context>` (e.g. `internal_question_answering`,
  `public_release`) to `search` — this filters permission-restricted concepts
  *before* they can leak into your answer. Never search without a `use`
  context if the answer could become public or cross a role boundary.
- Prefer objects with `evidence` on their `:::claim` blocks over unsupported claims.
- If an object has `conflicts_with`, **surface the conflict** — present both
  sides, don't silently pick one.
- Cite: object `id`, and its source file path (from `get`'s `concept_id`/path
  or the MCP `get_concept` result) in any answer you produce from the bundle.

## 4. Worked example

Question: *"What's our activation rate metric, and can I use it in an internal answer?"*

```bash
# 1. Check the profile
vkf validate examples --format json | head -5
# → profile 1 ("governed"): trust status/owners/refs; don't over-trust evidence/freshness

# 2. Search with a use context
vkf search examples "activation" --use internal_question_answering --json
# → top hit: metric:activation_rate, status=active, allowed=true

# 3. Fetch the full object
vkf get examples metric:activation_rate --json
# → status: active, owners: [team:analytics], last_verified: 2026-06-24
#   claim:activation_rate_definition, confidence: high,
#   evidence: dataset:user_events (strong), decision:activation_event_definition (definitive)
```

Answer: *"Activation rate = new users completing the activation event within 7
days of signup, divided by total new users in that cohort
(`metric:activation_rate`, `examples/metrics/activation-rate.md`). Status:
active, owned by team:analytics, last verified 2026-06-24. Definition backed by
strong/definitive evidence. Bundle is Profile 1 (governed), so status/owners
are trustworthy; this bundle doesn't commit to Profile 2, so treat the evidence
strength as reported-but-unverified."*

If instead you were asked to draft public-facing copy, you'd rerun the search
with `--use public_release`; `dataset:user_events` (visibility: confidential)
would be filtered out or flagged `allowed=false`, and you must not include it.

## 5. Before writing anything new

If your task might lead to proposing a new or changed object, use this same
access path first to check for an existing equivalent and any `conflicts_with`
— then switch to the **vkf-propose** skill.
