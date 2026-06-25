# VKF Specification v0.2.0

**Verifiable Knowledge Format (VKF)** is a Git-native, human-readable,
agent-operable knowledge format. VKF is a **strict superset of the Open
Knowledge Format (OKF) v0.1**: it adds a *trust and governance layer* —
provenance, evidence, confidence, lifecycle/freshness, contextual permissions,
typed relationships, executable verification, and opt-in conformance profiles —
without breaking OKF compatibility.

> **Relationship to OKF (normative).** Every conformant OKF v0.1 bundle is a
> conformant VKF bundle at Profile 0. Every VKF bundle, with VKF-specific
> frontmatter keys removed, is a conformant OKF bundle. VKF places all its
> additions in the producer-extension key space that OKF reserves and requires
> consumers to tolerate and preserve.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted
as in RFC 2119.

---

## 1. Bundles, files, and identity

A **bundle** is a directory tree of UTF-8 markdown files. Each non-reserved
`.md` file is one **concept**. This is inherited unchanged from OKF.

- **Canonical identity** of a concept is its bundle-relative path minus the
  `.md` extension (OKF rule). Example: `sales/tables/orders.md` →
  `sales/tables/orders`.
- The filenames `index.md` (navigation) and `log.md` (change history) are
  **reserved** and MUST NOT be used for concepts.
- A concept MAY declare an optional **stable alias** `id` of the form
  `<type>:<slug>` (e.g. `metric:activation_rate`). The alias is a durable
  handle that survives file moves and enables cross-bundle references. When
  present it MUST be unique within the bundle and match
  `^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9_-]*$`.

References elsewhere in the bundle MAY target either the path identity or the
alias; both resolve to the same concept.

---

## 2. Frontmatter fields

Each concept document begins with YAML frontmatter. The only field OKF (and
therefore VKF Profile 0) requires is `type`.

| Field | OKF | VKF role | Notes |
|---|---|---|---|
| `type` | required | required | Freeform string. VKF defines a *registry* of known types (§4) that unlock type-specific checks; unknown types are tolerated. |
| `title` | recommended | recommended | Human-readable name. |
| `description` / `summary` | recommended | recommended | One-sentence summary. |
| `resource` | recommended | recommended | URI uniquely identifying the underlying asset. |
| `tags` | recommended | recommended | List of strings. |
| `timestamp` | recommended | recommended | ISO 8601 datetime of last meaningful change. |
| `id` | — | optional | Stable alias (§1). |
| `vkf_version` | — | optional | VKF version targeted. |
| `status` | — | governed | Lifecycle state (§5). |
| `owners` | — | governed | List of owner identifiers; required for live objects. |
| `visibility` | — | governed | `public`, `internal`, `confidential`, `restricted`, `private`. |
| `created`, `last_verified`, `valid_until` | — | governed | ISO 8601 dates (§6). |
| `depends_on`, `supersedes`, `superseded_by`, `conflicts_with`, `derived_from` | — | governed | Typed references (§7). |
| `confidence` | — | governed | `low`, `medium`, `high`, `very_high`. |
| `evidence` | — | governed | List of evidence records (§8). |
| `access` | — | governed | Contextual permissions (§9). |
| `verification` | — | governed | Executable verification (§10). |
| `profile` | — | optional | Per-document profile override (§3). |

Consumers MUST tolerate and SHOULD preserve unknown keys (OKF rule).

---

## 3. Conformance profiles

VKF reconciles OKF's "consumers MUST NOT reject" rule with the need for
validation that can fail CI by making strictness **opt-in and declared**. A
bundle declares its target profile in `vkf.bundle.yaml` (`profile: N`); a
document MAY override it with a `profile` frontmatter key.

| Profile | Name | Guarantees (in addition to lower profiles) |
|---|---|---|
| **0** | `okf-compatible` | Structural OKF conformance only: every concept has a non-empty `type`. A validator MUST NOT emit errors beyond this at Profile 0. |
| **1** | `governed` | Schema conformance; ISO-8601 dates; `owners` on `active`/`verified` objects; unique aliases; all **typed** references resolve; no dependency cycles; well-formed claim blocks. |
| **2** | `verified` | `last_verified` on `verified` objects; evidence on claims; reciprocal supersession; type-specific completeness (e.g. metrics define numerator/denominator). |

A bundle that declares Profile *N* asserts a contract: consumers and agents MAY
rely on the Profile *N* guarantees holding for every concept in it.

---

## 4. Object types

VKF registers these known types; each unlocks type-specific validation. Other
type strings (e.g. OKF's `"BigQuery Table"`) are valid and tolerated but
receive only generic checks.

| Type | Purpose |
|---|---|
| `concept` | A domain concept or shared vocabulary. |
| `claim` | An assertion with evidence and confidence. |
| `decision` | A choice, its rationale, and consequences. |
| `policy` | A rule or requirement. |
| `runbook` | An operational procedure. |
| `dataset` | A data asset with lineage and access. |
| `metric` | A measurement (numerator/denominator/owner). |
| `experiment` | A test or evaluation, ideally reproducible. |
| `artifact` | A generated output or external object. |
| `transaction` | A human or agent edit record (§11). |

---

## 5. Lifecycle states

`draft, active, verified, stale, deprecated, superseded, archived, disputed, retracted`

Recommended agent behavior:

- `verified` — safe to cite within permission constraints.
- `active` — usable; check evidence and freshness.
- `draft` — MUST NOT be presented as authoritative.
- `stale` — warn the user.
- `deprecated` / `superseded` — prefer the replacement.
- `disputed` — present competing views; do not hide the conflict.
- `retracted` — do not rely on except for historical explanation.

---

## 6. Freshness

- `created`, `last_verified`, `valid_until` are ISO-8601 dates;
  `timestamp` is an ISO-8601 datetime.
- A concept is **stale** if `valid_until` is in the past, or if its status is a
  stale-like lifecycle state.
- At Profile 1, non-ISO dates are errors. At Profile 2, a `verified` object
  without `last_verified` is an error.

---

## 7. Relationships

OKF expresses relationships only as untyped markdown links in the body, which
consumers treat as untyped directed edges. VKF **preserves** these and adds
**typed** frontmatter relations:

```yaml
depends_on:    [dataset:user_events]
supersedes:    [policy:old_discounting]
superseded_by: policy:new_discounting
conflicts_with: [claim:contradictory_finding]
derived_from:  [experiment:source_study]
```

At Profile 1, every typed reference MUST resolve to a concept in the bundle
(by path or alias), and the `depends_on` graph MUST be acyclic. Untyped body
links MAY dangle (they may represent future knowledge), exactly as in OKF.

---

## 8. Claims and evidence

An important assertion SHOULD be a first-class **claim block** so it can carry
its own provenance. The grammar mirrors document frontmatter and degrades to
inert text for plain-markdown consumers:

```markdown
:::claim
---
id: claim:usage_correlates_with_willingness_to_pay
confidence: medium
evidence:
  - source: dataset:customer_usage_logs
    type: dataset
    strength: strong
  - source: analysis:pricing_survey_2026
    type: survey
    strength: moderate
forbidden_uses: [public_release]
---
Customers with higher usage show higher willingness to pay.
:::
```

- A block opens with a line containing only `:::claim` and closes with a line
  containing only `:::`.
- An optional YAML metadata header is delimited by `---` fences immediately
  after the opening line.
- Evidence records require a `source` and SHOULD declare `type` and `strength`
  (`weak`, `moderate`, `strong`, `definitive`).

At Profile 1, malformed claim blocks are errors. At Profile 2, a claim with no
evidence is an error.

---

## 9. Contextual permissions

Visibility is not the same as permitted use. A concept MAY declare an `access`
block:

```yaml
access:
  allowed_uses: [internal_question_answering]
  forbidden_uses: [public_release, training_data]
  allowed_roles: [employee]
  denied_roles: [contractor]
  requires_review_for: [external_sharing]
```

Resolution rules (see the reference `vkf check`):

1. A denied role, or a role outside a non-empty `allowed_roles`, denies use.
2. A use in `forbidden_uses`, or a use outside a non-empty `allowed_uses`,
   denies use.
3. By default, `confidential`/`restricted`/`private` visibility MUST NOT be used
   for external contexts (`public_release`, `external_sharing`, `training_data`).
4. A use in `requires_review_for` is allowed but flagged for human review.

---

## 10. Executable verification

A concept MAY declare how to reproduce or check it:

```yaml
verification:
  command: python scripts/reproduce.py
  expected: { accuracy_min: 0.90 }
  artifacts: [results/output.json]
```

Validators MUST NOT execute commands by default; verification is a separate,
explicitly invoked mode.

---

## 11. Transactions and audit

Agent or human edits MAY be recorded as `transaction` concepts (or in `log.md`)
capturing `actor`, `action`, `target`, `timestamp`, and `reason`. This supports
the principle that **agents propose; humans approve authority**.

---

## 12. Compilation targets

A VKF bundle is useful as files alone, but MAY be compiled into static docs,
vector-search chunks, knowledge-graph edges, permission indexes, freshness
dashboards, agent-memory bundles, and audit reports. The source markdown
remains canonical.

---

## 13. Versioning

VKF follows semantic versioning. Minor bumps add backward-compatible optional
fields, conventional sections, or known types; major bumps may rename fields or
change reserved filenames. Consumers encountering an unknown version SHOULD
attempt best-effort consumption rather than rejecting (OKF rule).
