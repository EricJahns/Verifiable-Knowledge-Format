# VKF — Verifiable Knowledge Format

> **Status: v0.x, experimental.** This is an independent proposal and reference
> implementation. It is **not affiliated with, endorsed by, or produced by
> Google**; "OKF" and "Open Knowledge Format" refer to Google Cloud's published
> format, which VKF builds on top of. The spec is a candidate, not a finished
> standard — expect breaking changes before 1.0.

**VKF is a Git-native, human-readable knowledge format that lets agents *author*
knowledge — not just read it — while a human stays the gatekeeper of what becomes
authoritative. It makes organizational knowledge *trustworthy enough for agents
to act on*, because nothing an agent writes is trusted until a human verifies it.**

It is a **strict superset of Google's [Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)**.
OKF makes knowledge *portable* — a directory of markdown files with YAML
frontmatter. VKF adds the layer OKF deliberately left out: a **trust and
governance layer** so an agent can tell *which source is authoritative, whether
a fact is stale, whether a claim has evidence, whether two documents disagree,
and whether something may be used externally*.

```
OKF:  knowledge that is portable.
VKF:  knowledge that is portable AND verifiable.
```

---

## Why VKF

OKF is intentionally minimal: its only required field is `type`, and consumers
must never reject a bundle. That is great for adoption and terrible for trust.
VKF keeps full OKF compatibility and adds, as optional governance fields:

| OKF leaves out | VKF adds | Why an agent needs it |
|---|---|---|
| Authority / ownership | `owners` (required for live objects) | Who to trust / escalate to |
| Structured provenance | claim blocks + `evidence` (type, strength) | The agent can *check* a claim, not just read it |
| Confidence | `confidence` on claims | The agent can hedge or refuse |
| Lifecycle | `status` + `last_verified` + `valid_until` | The agent knows when to stop trusting a fact |
| Typed relationships | `depends_on`, `conflicts_with`, `supersedes`, … | Surface contradictions, prefer replacements |
| Use rules | `visibility` + contextual `access` | Don't leak internal knowledge into public answers |
| Reproducibility | `verification` (command + expected) | Re-run a metric/experiment instead of trusting it |
| Validation teeth | opt-in conformance **profiles** | Trust becomes a contract, not a hope |

**Backward compatible, both ways:** every conformant OKF bundle is a valid VKF
bundle (Profile 0); every VKF bundle, with VKF keys stripped, is a valid OKF
bundle (`vkf to-okf`). Adopt VKF incrementally, field by field — Google's own
OKF tooling can still consume your bundles. This isn't just asserted: the test
suite validates **Google's actual published OKF sample bundles** (the
`crypto_bitcoin` and `stackoverflow` BigQuery bundles) and confirms they pass at
Profile 0 (see `tests/okf_samples/`).

---

## Agents that grow the knowledge base, humans who verify it

Those governance fields unlock VKF's primary motivating use case: agents that
*author* knowledge, not just read it. OKF is a read-oriented portability format;
VKF is designed so you can put an agent in a loop — periodically crawling the
bundle, deriving new claims, linking evidence, flagging stale or conflicting
facts, and *proposing* new objects — and stay safe doing it.

What makes the loop safe is that trust in VKF is structural, not editorial:

- An agent can freely add objects and claims, but only at `status: draft` /
  `proposed`. Agents **never self-promote to `verified`** — promotion through the
  `draft → active → verified` lifecycle is a human action, enforced by the
  validator and the conformance profiles.
- Until a human verifies it, the rest of the system already knows to treat it
  cautiously: retrieval prefers `verified`/`active` objects and warns on drafts,
  and `serve` can withhold unverified content from answers.
- Every agent contribution arrives as an ordinary Git change — a PR a human
  reviews, with `vkf validate` as the gate — so an agent expanding the knowledge
  base looks exactly like a contributor opening a pull request.

The result is a knowledge base an autonomous agent can continuously *grow* while
the human stays the gatekeeper of what becomes authoritative. For the mechanics,
see the propose-don't-promote flow in [Authoring knowledge](#authoring-knowledge)
and the agent rules in [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md).

---

## Conformance profiles

VKF squares OKF's "never reject" rule with CI gates by making strictness opt-in:

| Profile | Name | Adds |
|---|---|---|
| **0** | `okf-compatible` | Nothing — pure OKF, never errors. |
| **1** | `governed` | Owners on live objects, ISO dates, resolvable typed refs, unique ids, no dependency cycles, well-formed claims. |
| **2** | `verified` | Evidence on claims, `last_verified` on verified objects, reciprocal supersession, type completeness. |

A bundle declares its profile in `vkf.bundle.yaml`. See [docs/SPEC.md](docs/SPEC.md).

---

## Quick start

```bash
pip install -e .                       # or: pip install vkf

vkf validate examples                  # profile read from examples/vkf.bundle.yaml
vkf validate examples --profile 2 --v   # try the strictest profile
vkf freshness examples                 # what's stale?
vkf graph examples --out graph.json    # typed + claim-evidence edges
vkf check examples/datasets/user-events.md --use public_release   # -> DENY
vkf to-okf examples --out ./okf-export # prove the OKF superset claim
vkf import-okf ./some-okf-bundle --enrich   # check OKF conformance + upgrade plan
vkf html examples --out graph.html     # self-contained interactive visualizer
vkf serve examples                     # permission-aware retrieval API (needs vkf[server])
vkf init my-bundle                     # scaffold a new bundle
```

A concept file:

```markdown
---
type: metric
id: metric:activation_rate
title: Activation Rate
status: active
owners: [team:analytics]
visibility: internal
last_verified: 2026-06-24
valid_until: 2026-12-31
depends_on: [dataset:user_events]
---

# Activation Rate

:::claim
---
id: claim:activation_rate_definition
confidence: high
evidence:
  - source: dataset:user_events
    strength: strong
---
Activation rate is activated new users divided by total new users.
:::
```

Strip the VKF keys and it is still valid OKF. Keep them and an agent knows it is
an `active`, `internal`, team-owned metric, fresh until 2026-12-31, backed by a
high-confidence claim with strong dataset evidence.

---

## Authoring knowledge

A knowledge file is just a Markdown file in Git — there's no database or import
step. A **human owner** authors it directly; an **AI agent** may draft and
*propose* one, but a human approves authority (agents never self-promote to
`verified`). The path to "integrated" is the ordinary Git flow, with the
validator as the gate:

```text
copy a template → fill frontmatter → vkf validate → open a PR
   → Knowledge CI validates → an owner reviews & promotes (draft→active→verified)
   → merge → vkf graph / html / serve recompile from the source
```

```bash
cp templates/metric.md examples/metrics/net-revenue-retention.md   # or: vkf init my-bundle
$EDITOR examples/metrics/net-revenue-retention.md                  # set type/owners/status…
vkf validate examples                                              # gate it before review
```

The full walkthrough — naming, placement, the lifecycle, a worked example, and
the agent propose-don't-promote path — is in
**[docs/AUTHORING.md](docs/AUTHORING.md)**.

---

## Serve it to agents (permission-aware retrieval)

```bash
pip install -e ".[server]"
vkf serve examples            # http://127.0.0.1:8000
```

The `/search` endpoint filters by *use context*, ensuring an agent
asking for public-facing material never even sees confidential concepts:

```bash
# Returns the confidential user_events dataset:
curl "localhost:8000/search?q=events&use=internal_question_answering"
# Excludes it (forbidden for public release):
curl "localhost:8000/search?q=events&use=public_release"
```

Other endpoints: `/concepts`, `/concepts/{id-or-path}`, `/graph`, `/freshness`,
`/validate?profile=2`. The same engine (`vkf.service.KnowledgeService`) powers
the offline `vkf html` visualizer, whose nodes are coloured by freshness and
edges styled by typed relation.

> ⚠️ `vkf serve` ships **no authentication** and binds to localhost by default —
> it's for local development and trusted networks. Don't expose it publicly
> without putting your own auth/authorization in front of it. The permission
> model is a *cooperative* control for trusted agents, not a hard access boundary
> (see [SECURITY.md](SECURITY.md)).

---

## Does governance actually help? (benchmark)

`vkf benchmark` tests the thesis directly: three conditions (plain RAG, OKF,
VKF) answer the same questions with the same prompt, model, and retrieval
ranking — only the context differs. Scoring is deterministic (canary tokens),
so it's reproducible without an LLM judge.

```bash
vkf benchmark                      # mock agent, no API key — validates the harness
                                   # and the retrieval-layer permission result
pip install -e ".[bench]"
vkf benchmark --live --out r.json  # full run against Claude (claude-opus-4-8)
```

In a live run on `claude-opus-4-8` (5 scenarios), VKF scored **1.00** overall
vs **0.38** for both RAG and OKF. The honest, per-category reading matters more
than the headline number:

- **Permission:** when a confidential doc has *no* embargo warning in its text,
  RAG/OKF state the secret figure and VKF withholds it — VKF's safety is
  structural, not dependent on the model's goodwill.
- **Staleness / authority:** when currency/authority lives in metadata (not
  restated in prose), RAG/OKF can only *abstain* ("two conflicting values…");
  VKF answers correctly from `status`/`valid_until`/`confidence`.
- **Conflict:** a tie — both views get retrieved regardless.

This is an illustrative benchmark (small N, one model) that demonstrates
*mechanisms*, not an effect size — see
[benchmark/README.md](benchmark/README.md) for the full results, caveats, and
the conditions under which RAG/OKF also succeed.

---

## Repository layout

```text
docs/SPEC.md                 the specification (VKF as a governed profile of OKF)
docs/AUTHORING.md            how to create a knowledge file and get it merged
docs/                        design principles, agent guide, security model, CI
src/vkf/                     reference implementation
  loader.py  claims.py  validate.py  graph.py  freshness.py
  permissions.py  interop.py  manifest.py  cli.py  schemas/
  service.py  server.py  html.py    retrieval engine, HTTP API, visualizer
examples/                    a conformant bundle (profile: 1) + vkf.bundle.yaml
templates/                   one starter per object type
conformance/                 pass/fail corpus pinning the profile semantics
benchmark/                   VKF vs OKF vs RAG benchmark (bundle + scenarios)
tests/                       parser, profile, permission, interop, conformance tests
.github/workflows/           lint, type-check, test, validate, OKF round-trip
```

---

## Status

Like OKF, VKF is a reference implementation and a candidate specification — not yet a
finalized standard. It is designed to be adopted incrementally on top of OKF.
See [docs/ROADMAP.md](docs/ROADMAP.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

Sources: [Google Cloud — OKF announcement](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) ·
[OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
