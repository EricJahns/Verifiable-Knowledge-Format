# Serving a VKF bundle over MCP

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is how agent
hosts — Claude Desktop, Claude Code, the Gemini CLI, Cursor, and others — discover
and call tools. VKF ships an MCP server so any MCP-speaking agent can consume a
bundle with **zero custom integration code**: point the host at `vkf mcp <bundle>`
and the agent gets permission-aware retrieval, freshness, and validation as tools.

The server is a thin wrapper over the same `KnowledgeService` that powers
`vkf serve` and `vkf html`, so the governance guarantees are identical — a
confidential concept that `vkf serve` would withhold from a `public_release`
query is withheld here too.

---

## Install

```bash
pip install -e ".[mcp]"     # or: pip install "vkf[mcp]"
```

This pulls in the official `mcp` Python SDK.

---

## Run it

```bash
vkf mcp examples
```

The server speaks MCP over **stdio** (the transport every host supports). It
prints one line to *stderr* and then waits for a client — that's expected; stdio
servers are launched *by* the host, not run by hand. To sanity-check that it
starts and exits cleanly:

```bash
vkf mcp examples < /dev/null
```

---

## Tools the agent gets

| Tool | What it does |
|---|---|
| `search(q, use, role, limit)` | **Permission-aware** retrieval. Pass the `use` context (e.g. `public_release`) and concepts that may not be used there are never returned. |
| `check_permission(ref, use, role)` | Explicit allow / deny / needs-review verdict for one concept in one context, with a reason. |
| `get_concept(ref)` | Full concept: frontmatter, body, and parsed claim blocks. |
| `list_concepts(type, status, tag)` | Inventory with type, status, visibility, and freshness. |
| `freshness()` | Which concepts are stale or expired. |
| `validate(profile)` | What the bundle's conformance profile guarantees. |
| `graph(typed_only)` | Concept nodes and their typed/untyped relationships. |

`ref` is a concept's stable id/alias (`metric:activation_rate`) or its
bundle-relative path without `.md` (`metrics/activation`).

The server also sends the host a short **instructions** string telling the agent
to always pass a `use` context, prefer `verified`/`active` concepts, warn on
stale/draft ones, and cite concept ids — so governance-aware behavior is the
default even before you tune your own prompt.

---

## Connect a host

### Claude Code

```bash
claude mcp add vkf -- vkf mcp /absolute/path/to/your-bundle
```

Then in a session: `/mcp` lists the connected server, and the agent can call the
tools above. Use an absolute path to the bundle so it resolves regardless of the
working directory.

### Claude Desktop

Edit the config file
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows) and add:

```json
{
  "mcpServers": {
    "vkf": {
      "command": "vkf",
      "args": ["mcp", "/absolute/path/to/your-bundle"]
    }
  }
}
```

Restart Claude Desktop; the VKF tools appear under the tools (plug) icon.

### Any other MCP host (Cursor, Gemini CLI, custom clients)

The same command/args pair works anywhere that launches stdio MCP servers:

```json
{ "command": "vkf", "args": ["mcp", "/absolute/path/to/your-bundle"] }
```

If `vkf` is not on the host's `PATH` (common with GUI apps), use the interpreter
from the environment you installed into:

```json
{ "command": "/path/to/venv/bin/python", "args": ["-m", "vkf.cli", "mcp", "/absolute/path/to/your-bundle"] }
```

---

## Try it end-to-end

With the `examples` bundle connected, ask the agent things that exercise the
governance layer:

- *"What's our activation rate metric, and is it current?"* — the agent calls
  `search` + `freshness` and can report the `active` status and `valid_until`.
- *"Draft a public blog post using our user-events data."* — with a
  `public_release` use context, `search` never surfaces the confidential
  `dataset:user_events`, so it cannot leak into the post. `check_permission`
  confirms the denial with a reason.
- *"What does this bundle guarantee?"* — `validate` reports the conformance
  profile (Profile 1 for `examples`).

This is the same mechanism measured in [`benchmark/`](../benchmark/README.md):
permission-aware retrieval, now available to any MCP client.

---

## Security note

Like `vkf serve`, the MCP server enforces a **cooperative** permission model for
trusted agents — it is not a hard access boundary. The stdio server runs with the
privileges of whoever launched it and reads whatever bundle path it's given. Only
point it at bundles you trust, and see [SECURITY.md](../SECURITY.md) and
[SECURITY_AND_PERMISSIONS.md](SECURITY_AND_PERMISSIONS.md) for the full model.
