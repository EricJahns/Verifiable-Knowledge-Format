# Agent Guide

This document defines how AI agents should use VKF bundles.

For hosts that support the Claude Code / pi **skill** convention, the rules
below are packaged as two runnable procedures: [`skills/vkf-retrieve/SKILL.md`](../skills/vkf-retrieve/SKILL.md)
(finding and citing knowledge) and [`skills/vkf-propose/SKILL.md`](../skills/vkf-propose/SKILL.md)
(the propose-don't-promote flow for adding knowledge).

## What the bundle's profile guarantees you

Check the bundle's declared profile (`vkf.bundle.yaml` → `profile`). It is a
contract you can rely on:

- **Profile 0 (`okf-compatible`)** — only that every concept has a `type`.
  Treat governance fields as best-effort; verify before relying on them.
- **Profile 1 (`governed`)** — live objects have owners, dates are valid,
  typed references resolve, there are no dependency cycles, and claim blocks are
  well-formed. You can trust `status`, `owners`, and the typed relationship graph.
- **Profile 2 (`verified`)** — additionally, claims carry evidence and
  `verified` objects carry `last_verified`. You can surface evidence and
  freshness with confidence.

Do not assume Profile 1/2 guarantees on a Profile 0 bundle.

## Retrieval behavior

When answering questions:

1. Prefer `verified` and `active` objects.
2. Warn when using `stale`, `draft`, `deprecated`, `superseded`, `disputed`, or `retracted` objects.
3. Respect `visibility` and contextual `access` metadata.
4. Prefer objects with evidence over unsupported claims.
5. Surface conflicts rather than hiding them.
6. Cite object IDs and source files in generated answers.

## Update behavior

Agents may:

- propose new objects
- mark objects as possibly stale
- suggest evidence links
- identify conflicts
- generate transaction records
- generate derived summaries

Agents should not:

- silently mark a claim as verified
- remove conflicting evidence without review
- upgrade restricted content into public output
- modify canonical knowledge without transaction records

### The continuous-loop pattern

VKF is designed for an agent run on a schedule (or in a long-running loop) that
periodically walks the bundle to **grow and maintain** it: derive new claims from
existing objects, propose evidence links, flag objects that look stale or
mutually conflicting, and draft new objects for facts the base is missing. This
is the package's primary motivating use case.

The loop stays safe because the agent only ever *proposes*. Every new or changed
object an agent writes lands at `status: draft` (or `proposed`); the agent
**never** promotes its own work to `active` or `verified`. Promotion through the
`draft → active → verified` lifecycle is a human action, and the conformance
profiles plus retrieval defaults (prefer `verified`/`active`, warn on `draft`)
mean unverified agent output is treated cautiously until a human reviews and
promotes it. Surface each pass as an ordinary Git change with a transaction
record so a human can review it as a normal pull request — see the
propose-don't-promote flow in [AUTHORING.md](AUTHORING.md).

## Answer style

When answering from VKF, agents should include:

- answer
- source object IDs
- confidence level
- freshness status
- permission caveats when relevant
- conflicts or missing evidence when relevant

## Tooling an agent can call

The reference implementation exposes this behavior directly, so an agent host
doesn't have to reimplement it:

- **Permission-aware retrieval** — `GET /search?q=...&use=<context>&role=<role>`
  (or `KnowledgeService.search(q, use, role)`) returns only concepts the agent
  may use in that context. A confidential concept is never returned for a
  `public_release` query, so it cannot leak into a public answer.
- **Per-object check** — `vkf check <file> --use <context> [--role <role>]`
  (or `permissions.can_use(metadata, use, role)`) returns allow / deny /
  allow-but-requires-review with a reason.
- **Freshness** — `GET /freshness` or `vkf freshness` flags stale and superseded
  objects so the agent can warn or prefer replacements.

This is the mechanism behind the benchmark result in `benchmark/`: governed,
permission-aware retrieval measurably reduces permission leaks versus OKF or
plain RAG.

The same behavior is available over the **Model Context Protocol** via
`vkf mcp <bundle>`, so an MCP host (Claude Code, Claude Desktop, Gemini CLI, …)
gets `search`, `check_permission`, `get_concept`, `list_concepts`, `freshness`,
`validate`, and `graph` as tools with no integration code — see
[MCP.md](MCP.md). Always pass a `use` context to `search` so permission-restricted
concepts are filtered out before they can enter an answer.
