# Security Policy

VKF is an experimental v0.x project. We still take security seriously and
welcome reports.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** — do not open a public
issue for anything exploitable:

- Use GitHub's **[Private vulnerability reporting](https://github.com/EricJahns/Verifiable-Knowledge-Format/security/advisories/new)**
  (Security → Report a vulnerability), or
- email the maintainer (see the GitHub profile for **EricJahns**).

Please include reproduction steps and the affected version/commit. We'll
acknowledge within a reasonable time and coordinate a fix and disclosure.

## Threat model — what VKF does and does not protect

Read this before deploying VKF anywhere untrusted.

- **Permissions are a cooperative control, not access control.** `visibility`,
  `access`, and permission-aware retrieval (`vkf check`, `GET /search?use=...`)
  help *trusted* agents and retrieval pipelines avoid misusing knowledge they
  were already allowed to read. They are **not** an authorization boundary.
  Enforce real authorization at your storage, API, and network layers — VKF
  does not encrypt content, authenticate callers, or stop a process that has the
  files from reading any of them.

- **`vkf serve` has no authentication.** It binds to `127.0.0.1` by default and
  is intended for local development and trusted networks. Anyone who can reach
  the port can read every concept in the bundle, including `confidential` ones
  (the permission filter only applies when a `use` context is supplied). Put
  your own authn/authz in front of it before exposing it.

- **`verification.command` is descriptive metadata, not executed by default.**
  A concept may declare a `verification.command` (e.g. a script to reproduce a
  metric). The validator and tooling in this repo **do not run it**. If you
  build a verification runner, treat those commands as **untrusted input** and
  execute them only in a sandbox you control — a malicious or compromised bundle
  could otherwise achieve code execution on your machine.

- **Bundles are untrusted input.** Markdown, YAML frontmatter, and claim blocks
  come from people and agents. The loader uses `yaml.safe_load` and never
  executes bundle content, but downstream consumers should validate
  (`vkf validate`) and apply their own trust policy before acting on a bundle —
  especially one from outside your organization.

- **The benchmark calls an external API.** `vkf benchmark --live` sends bundle
  content to Anthropic's API. Don't run it against confidential bundles unless
  that data flow is acceptable, and never commit API keys.

## Supported versions

Pre-1.0: only the latest `main` is supported. Pin a commit if you need stability.
