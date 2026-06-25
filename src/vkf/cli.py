from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import frontmatter

from . import __version__
from .freshness import freshness_report
from .graph import build_graph
from .interop import enrichment_report, okf_conformance, to_okf
from .manifest import PROFILE_NAMES, resolve_profile
from .permissions import can_use
from .validate import has_errors, summarize, validate_objects


def _profile_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile", type=int, choices=[0, 1, 2], default=None,
        help="Override conformance profile (0=okf-compatible, 1=governed, 2=verified).",
    )


def cmd_validate(args) -> int:
    profile = resolve_profile(args.root, args.profile)
    issues = validate_objects(args.root, profile=args.profile)
    if args.format == "json":
        print(json.dumps({
            "profile": profile,
            "profile_name": PROFILE_NAMES.get(profile),
            "summary": summarize(issues),
            "issues": [{"level": i.level, "path": i.path, "message": i.message} for i in issues],
        }, indent=2))
    else:
        for issue in issues:
            if issue.level == "INFO" and not args.verbose:
                continue
            print(issue)
        counts = summarize(issues)
        name = PROFILE_NAMES.get(profile)
        print(f"\nProfile {profile} ({name}): "
              f"{counts['ERROR']} error(s), {counts['WARNING']} warning(s), {counts['INFO']} info")
        if not has_errors(issues):
            print("VKF validation passed")
    return 1 if has_errors(issues) else 0


def cmd_freshness(args) -> int:
    print(json.dumps(freshness_report(args.root), indent=2))
    return 0


def cmd_graph(args) -> int:
    graph = build_graph(args.root, include_body_links=not args.typed_only)
    text = json.dumps(graph, indent=2)
    if args.out:
        Path(args.out).write_text(text)
        print(f"Wrote graph to {args.out} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")
    else:
        print(text)
    return 0


def cmd_check(args) -> int:
    post = frontmatter.load(args.path)
    decision = can_use(dict(post.metadata), args.use, role=args.role)
    result = {
        "path": args.path,
        "use_context": args.use,
        "role": args.role,
        "allowed": decision.allowed,
        "requires_review": decision.requires_review,
        "reason": decision.reason,
    }
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        verdict = "ALLOW" if decision.allowed else "DENY"
        if decision.requires_review:
            verdict = "ALLOW (requires review)"
        print(f"{verdict}: {decision.reason}")
    return 0 if decision.allowed else 2


def cmd_to_okf(args) -> int:
    count = to_okf(args.root, args.out)
    print(f"Wrote {count} OKF concept file(s) to {args.out}")
    return 0


def cmd_import_okf(args) -> int:
    issues = okf_conformance(args.root)
    for issue in issues:
        print(issue)
    if issues:
        print(f"\n{len(issues)} OKF conformance issue(s)")
        return 1
    print("Bundle is OKF-conformant (valid at VKF Profile 0)")
    if args.enrich:
        print("\nEnrichment plan to reach the 'governed' profile:")
        print(json.dumps(enrichment_report(args.root), indent=2))
    return 0


def cmd_html(args) -> int:
    from .html import write_html
    out = write_html(args.root, args.out, title=args.title)
    print(f"Wrote self-contained visualizer to {out}")
    return 0


def cmd_serve(args) -> int:  # pragma: no cover - exercised manually
    from .server import serve
    print(f"Serving VKF bundle '{args.root}' at http://{args.host}:{args.port}")
    serve(args.root, host=args.host, port=args.port)
    return 0


def cmd_benchmark(args) -> int:
    from . import benchmark as bench
    scenarios = bench.load_scenarios(args.scenarios)
    agent: bench.Agent
    if args.live:
        agent = bench.AnthropicAgent(model=args.model)
    else:
        agent = bench.MockAgent()
        print("Running with the MOCK agent (no API key). Use --live to run against Claude.\n")
    results = bench.run(args.bundle, scenarios, agent, progress=print)
    report = bench.render_report(results, agent.name)
    print("\n" + report)
    if args.out:
        Path(args.out).write_text(json.dumps(bench.results_to_dicts(results), indent=2))
        print(f"\nWrote detailed results to {args.out}")
    if args.update_readme:
        readme = Path(args.update_readme)
        n = bench.update_readme(readme, report)
        print(f"\nUpdated results section in {readme}" if n else
              f"\nNo <!-- RESULTS:START/END --> markers found in {readme}")
    return 0


def cmd_init(args) -> int:
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "vkf.bundle.yaml"
    if not manifest.exists():
        manifest.write_text(
            "vkf_version: 0.2.0\n"
            "okf_version: \"0.1\"\n"
            f"name: {root.name}\n"
            "summary: A VKF knowledge bundle.\n"
            "profile: 1\n"
        )
    sample = root / "concepts" / "example.md"
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_text(
            "---\n"
            "type: concept\n"
            "id: concept:example\n"
            "title: Example Concept\n"
            "status: draft\n"
            "owners:\n  - team:yours\n"
            "visibility: internal\n"
            "---\n\n# Example Concept\n\nReplace this with real knowledge.\n"
        )
    print(f"Initialized VKF bundle at {root}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="vkf", description="Verifiable Knowledge Format toolkit")
    parser.add_argument("--version", action="version", version=f"vkf {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="Validate a VKF bundle")
    p.add_argument("root")
    _profile_arg(p)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--verbose", action="store_true", help="Include INFO-level issues")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("freshness", help="Report freshness state")
    p.add_argument("root")
    p.set_defaults(func=cmd_freshness)

    p = sub.add_parser("graph", help="Export the knowledge graph")
    p.add_argument("root")
    p.add_argument("--out")
    p.add_argument("--typed-only", action="store_true", help="Exclude untyped body links")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("check", help="Check whether an object may be used in a context")
    p.add_argument("path")
    p.add_argument("--use", required=True, help="Use context, e.g. public_release")
    p.add_argument("--role", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("to-okf", help="Project a VKF bundle down to pure OKF")
    p.add_argument("root")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_to_okf)

    p = sub.add_parser("import-okf", help="Check OKF conformance and plan enrichment")
    p.add_argument("root")
    p.add_argument("--enrich", action="store_true", help="Print the governance enrichment plan")
    p.set_defaults(func=cmd_import_okf)

    p = sub.add_parser("html", help="Write a self-contained HTML graph visualizer")
    p.add_argument("root")
    p.add_argument("--out", required=True)
    p.add_argument("--title", default=None)
    p.set_defaults(func=cmd_html)

    p = sub.add_parser("serve", help="Run the permission-aware retrieval API (needs 'vkf[server]')")
    p.add_argument("root")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("benchmark", help="Run the VKF vs OKF vs RAG benchmark")
    p.add_argument("--bundle", default="benchmark/bundle")
    p.add_argument("--scenarios", default="benchmark/scenarios.yaml")
    p.add_argument("--live", action="store_true", help="Call Claude (needs 'anthropic' + ANTHROPIC_API_KEY)")
    p.add_argument("--model", default="claude-opus-4-8")
    p.add_argument("--out", help="Write detailed per-answer results as JSON")
    p.add_argument("--update-readme", nargs="?", const="benchmark/README.md",
                   help="Write the results table into a README's RESULTS markers "
                        "(default: benchmark/README.md)")
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("init", help="Scaffold a new VKF bundle")
    p.add_argument("root")
    p.set_defaults(func=cmd_init)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
