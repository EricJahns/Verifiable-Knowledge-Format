# Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.6.0] - 2026-07-23

### Added
- **Core `vkf search`/`vkf get`/`vkf list` CLI commands.** Previously the only
  way to query a bundle's contents was `vkf serve` or `vkf mcp`, both optional
  extras. These wrap the same framework-agnostic `KnowledgeService` with zero
  new dependencies, so any agent with a plain `pip install vkf` can search,
  fetch, and list concepts (`--json` for structured output; `search` supports
  `--use`/`--role`/`--limit`/`--include-denied`, matching the server/MCP
  permission-aware behavior).
- **`templates/transaction.md`.** AUTHORING.md's agent propose-don't-promote
  flow always required a transaction record, but shipped no starter template
  for one — agents had to copy the worked example by hand.
- **`skills/vkf-retrieve/` and `skills/vkf-propose/`.** Two Claude Code/pi
  `SKILL.md` files that package AGENT_GUIDE.md's retrieval rules and
  AUTHORING.md's propose-don't-promote flow into runnable step-by-step
  procedures, so an agent host doesn't re-derive the access-path decision or
  the trust rules from prose every time. Linked from README.md and
  AGENT_GUIDE.md.

## [0.5.1] - 2026-07-01

### Fixed
- **`vkf html`: clicking a node now opens its detail panel.** Starting a node
  press captured the pointer on the `<svg>`, which retargets the native `click`
  to the svg — so the per-node click handler never fired and the background
  handler cleared the selection instead. Selection now happens on
  pointerup-without-movement (a tap), tracked independently of `click`; a node is
  pinned only once an actual drag passes a small movement threshold, so a plain
  tap selects without pinning.

## [0.5.0] - 2026-07-01

### Added
- **Redesigned `vkf html` visualizer.** The single-file graph viewer now runs a
  live cooling force-directed layout with full interaction: scroll/pinch to zoom,
  drag the background to pan, drag a node to pin it (double-click to release),
  Fit-view, Re-layout, and Freeze controls. Hovering a node focuses the graph on
  it and its neighbours (everything else dims); there's full-text search and
  click-to-toggle type filters. Nodes are filled by freshness, ringed by
  visibility, and carry a type glyph; edges are curved and directed with
  per-relation arrowheads. Long identifiers stay readable — labels truncate onto
  a legible pill and expand on focus, with the full id in the tooltip and detail
  panel — fixing the previous overlap-into-soup behaviour on real bundles.
- **MCP server** (`vkf mcp <bundle>`, `vkf.mcp_server.create_mcp`): serves a
  bundle to any Model Context Protocol host (Claude Code, Claude Desktop, Gemini
  CLI, Cursor, …) over stdio, exposing permission-aware `search`,
  `check_permission`, `get_concept`, `list_concepts`, `freshness`, `validate`,
  and `graph` as tools. Backed by the same `KnowledgeService` as `vkf serve`, so
  a `public_release` search still withholds confidential concepts. New optional
  extra `vkf[mcp]`; setup and client configs in `docs/MCP.md`. Added
  `KnowledgeService.check(ref, use, role)` for id/alias-based permission checks.
- **Real-OKF interoperability proof**: vendored Google's actual published OKF
  sample bundles (`crypto_bitcoin`, `stackoverflow`) under `tests/okf_samples/`
  (Apache-2.0, attributed in NOTICE.md) and a test suite proving they validate
  as VKF at Profile 0 — substantiating the "strict superset of OKF" claim
  against real data rather than only synthetic fixtures. Surfaced a real-world
  finding: Google's sample encodes `tags` as a string, which Profile 0 tolerates
  and Profile 1 flags.
- `SECURITY.md`: vulnerability reporting plus an explicit threat model
  (permissions are a cooperative control not access control; `vkf serve` has no
  auth; `verification.command` is not executed; bundles are untrusted input).

### Changed
- License is **MIT** consistently (`LICENSE` file and `pyproject.toml` now agree;
  previously `pyproject` declared Apache-2.0).
- Replaced placeholder project URLs with the real repository, and set the schema
  `$id` to a URL under the project's own repo (was an unowned domain).
- README now carries an explicit "experimental v0.x, not affiliated with Google"
  disclaimer and a no-auth warning on `vkf serve`.

## [0.4.0] - 2026-06-24

Added a reproducible benchmark for the core thesis: governance changes agent
behavior; a conformance corpus; and docs aligned to the implemented behavior.

### Added
- **Conformance corpus** (`conformance/`): 12 minimal bundles with expected
  pass/fail outcomes per profile in `expectations.yaml`, run by a parametrized
  test — pins the Profile 0/1/2 semantics so any implementation can check itself.
- `vkf benchmark --update-readme` writes the results table into a README between
  `<!-- RESULTS:START/END -->` markers (one command to capture a live run).
- Docs (`AGENT_GUIDE`, `SECURITY_AND_PERMISSIONS`, `DESIGN_PRINCIPLES`) updated to
  the implemented profile contract, permission resolution order, roles/review,
  and the `vkf check` / `/search` surface.

### Changed
- **Benchmark scoring is now dismissal-aware**: a correct answer that mentions a
  stale/wrong value *in order to dismiss it* ("…the old 7-day window was
  replaced") now scores correctly. The previous scorer failed these.
- **Benchmark fixtures neutralized**: currency/authority cues were moved out of
  document prose into metadata, so the scenarios isolate the governance variable
  rather than letting RAG/OKF read the answer off the text. Added a robustness
  permission scenario (confidential figure with no in-text warning).
- Captured a live `claude-opus-4-8` run (`benchmark/results.json`,
  `benchmark/README.md`): VKF 1.00 vs RAG/OKF 0.38, with per-category caveats.
- **VKF vs OKF vs plain-RAG benchmark** (`vkf benchmark`, `vkf.benchmark`): three
  conditions answer the same questions with the same prompt, model, and retrieval
  ranking — only the context differs (raw chunks / OKF frontmatter / VKF governance
  + permission-aware retrieval). Four governance-stress scenarios (permission leak,
  staleness, authority, conflict), scored **deterministically** by canary-token
  presence — no LLM judge, fully reproducible.
- A crafted benchmark bundle (`benchmark/bundle/`) and `benchmark/scenarios.yaml`.
- Mock-agent mode (`vkf benchmark`, no API key) validates the harness and the
  retrieval-layer permission result; `--live` runs against Claude (`claude-opus-4-8`).
- Benchmark tests asserting the API-key-free guarantee: VKF withholds the
  confidential concept (leak avoided) while RAG/OKF leak it.
- `bench` optional extra (`pip install "vkf[bench]"`) and a CI mock-benchmark gate.

## [0.3.0] - 2026-06-24

Added a deployable service and an offline visualizer on top of the v0.2 core.

### Added
- **Knowledge service** (`vkf.service.KnowledgeService`): a framework-agnostic
  engine for listing, lookup (by alias or path identity), and **permission-aware
  retrieval** — `search(q, use, role)` returns only concepts an agent may use in
  the given context, with denied results optionally annotated.
- **HTTP API** (`vkf serve`, FastAPI, optional `vkf[server]` extra): `/health`,
  `/concepts`, `/concepts/{ref}`, `/search`, `/graph`, `/freshness`, `/validate`.
- **Self-contained HTML visualizer** (`vkf html`): a single dependency-free file
  (no CDN, no build) rendering the typed graph with freshness/lifecycle node
  colours and relation-styled edges — the trust-layer answer to OKF's viewer.
- Service, server (via Starlette TestClient), and HTML tests.

## [0.2.0] - 2026-06-24

Reframed the project as **VKF (Verifiable Knowledge Format)** — a strict
superset of Google's OKF v0.1 — and turned the starter into a working reference
implementation.

### Added
- **OKF compatibility**: path-based concept identity, reserved `index.md`/`log.md`,
  tolerance for unknown types and keys. Every conformant OKF bundle validates at
  Profile 0.
- **Conformance profiles** (0 `okf-compatible`, 1 `governed`, 2 `verified`),
  declared per bundle in `vkf.bundle.yaml` and overridable per document.
- **Claim-block parser** with an unambiguous grammar (`:::claim` + `---` YAML
  header + body + `:::`) — previously specified but unimplemented.
- **Profile-aware validation**: ISO-date checks, ownership of live objects,
  resolvable typed references, dependency-cycle detection, reciprocal
  supersession, evidence-on-claims, and type-specific checks.
- **Contextual permission engine** (`vkf check`) with roles, use contexts, and
  review flags, plus default external-use protection for non-public visibility.
- **OKF interop** (`vkf to-okf`, `vkf import-okf --enrich`) proving the superset
  claim both directions.
- **Typed knowledge graph** including claim-evidence edges; `vkf init` scaffolding.
- Real test suite (parser, profiles, permissions, interop), ruff + mypy config,
  multi-version CI with an OKF round-trip gate, `.gitignore`, this changelog.

### Fixed
- **Packaging bug**: schemas now ship as package data (`importlib.resources`)
  instead of being resolved relative to the repo, so `pip install` works.
- Removed committed build artifacts (`*.egg-info`, `__pycache__`).

### Changed
- Package renamed `ngkf` → `vkf`; CLI entry point is now `vkf`.
- Dates and references are validated; dangling typed references now fail CI at
  Profile 1 (previously warnings only).
