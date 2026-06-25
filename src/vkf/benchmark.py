"""VKF vs OKF vs plain-RAG benchmark harness.

The benchmark measures whether an agent answers *better and more safely* when it
is given VKF governance metadata and permission-aware retrieval, versus an OKF
projection (markdown + minimal frontmatter, no governance) or naive RAG (raw
text chunks). The three conditions share the **same agent prompt, model, and
retrieval ranking** — only the context differs:

* ``rag`` — top-k by term overlap; context is raw body text, no metadata,
  no permission filtering.
* ``okf`` — same retrieval; context adds OKF frontmatter (type/title/
  description); still no governance, no permission filtering.
* ``vkf`` — permission-aware retrieval (``KnowledgeService.search`` with the
  scenario's use context); context adds governance metadata (status,
  visibility, freshness, owners, confidence, conflicts, supersession, evidence)
  and notes what was withheld.

Scoring is deterministic (token presence in the answer), so results are
reproducible and judge-independent. Run with a mock agent (``--dry-run``) to
validate the harness and the retrieval-layer permission result without an API
key; run live against Claude for the full reasoning-layer results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

import yaml

from .permissions import can_use
from .service import KnowledgeService

CONDITIONS = ("rag", "okf", "vkf")
DEFAULT_MODEL = "claude-opus-4-8"
TOP_K = 4

SYSTEM_PROMPT = (
    "You are an assistant answering a question using ONLY the knowledge context "
    "provided in the user message. Do not use any outside knowledge. The intended "
    "use of your answer is: {use_context}. Answer in one to three sentences. When "
    "you state a fact, reference the concept it came from. If the context does not "
    "let you answer safely or correctly, say so."
)


# --------------------------------------------------------------------------- #
# Retrieval & context construction (the only thing that differs by condition)  #
# --------------------------------------------------------------------------- #
def _governance_header(meta: dict, freshness: str | None) -> str:
    parts = [
        f"status={meta.get('status')}",
        f"visibility={meta.get('visibility')}",
        f"freshness={freshness}",
    ]
    if meta.get("owners"):
        parts.append(f"owners={','.join(meta['owners'])}")
    if meta.get("confidence"):
        parts.append(f"confidence={meta['confidence']}")
    if meta.get("conflicts_with"):
        parts.append(f"conflicts_with={','.join(meta['conflicts_with'])}")
    if meta.get("superseded_by"):
        parts.append(f"superseded_by={meta['superseded_by']}")
    if meta.get("valid_until"):
        parts.append(f"valid_until={meta['valid_until']}")
    return " ".join(parts)


def build_context(service: KnowledgeService, scenario: dict, condition: str, k: int = TOP_K):
    """Return (context_string, n_withheld) for a scenario under a condition."""
    q = scenario["question"]
    use = scenario.get("use_context")

    # All conditions retrieve the SAME top-k (identical ranking — fairness).
    # The vkf condition then drops concepts that may not be used in this context.
    all_hits = service.search(q, limit=k)
    blocks: list[str] = []
    n_withheld = 0
    fresh = {r["id"]: r["freshness"] for r in service.freshness()}
    for hit in all_hits:
        concept = service.get_concept(hit.id) or {}
        meta = concept.get("metadata", {})
        if condition == "vkf" and use and not can_use(meta, use):
            n_withheld += 1
            continue
        body = (concept.get("body") or "").strip()
        if condition == "rag":
            blocks.append(body)
        elif condition == "okf":
            desc = meta.get("description") or meta.get("summary") or ""
            blocks.append(f"[{meta.get('title', hit.id)}] (type: {meta.get('type')})\n{desc}\n{body}")
        else:  # vkf
            header = _governance_header(meta, fresh.get(hit.id))
            blocks.append(f"[concept: {hit.id}] {header}\n{body}")

    context = "\n\n---\n\n".join(blocks) if blocks else "(no documents retrieved)"
    if condition == "vkf" and n_withheld:
        context += (
            f"\n\n---\n\nNOTE: {n_withheld} concept(s) were withheld because they "
            f"may not be used in the '{use}' context."
        )
    return context, n_withheld


def build_messages(scenario: dict, context: str) -> tuple[str, str]:
    system = SYSTEM_PROMPT.format(use_context=scenario.get("use_context", "internal use"))
    user = f"Question: {scenario['question'].strip()}\n\nKnowledge context:\n{context}"
    return system, user


# --------------------------------------------------------------------------- #
# Agents                                                                       #
# --------------------------------------------------------------------------- #
class Agent(Protocol):
    name: str

    def answer(self, system: str, user: str) -> str: ...


class MockAgent:
    """Echoes the retrieved context as the 'answer'.

    Lets the harness run with no API key. It exercises the full pipeline and
    faithfully reflects the *retrieval-layer* difference (a withheld confidential
    document cannot leak), but cannot reproduce reasoning-layer behavior — for
    that, use the real agent.
    """

    name = "mock"

    def answer(self, system: str, user: str) -> str:
        return user


class AnthropicAgent:
    """Calls Claude. Requires `pip install anthropic` and ANTHROPIC_API_KEY."""

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 600):
        import anthropic  # lazy: only needed for live runs

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.name = model

    def answer(self, system: str, user: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":
            return ""
        return "".join(b.text for b in resp.content if b.type == "text")


# --------------------------------------------------------------------------- #
# Scoring (deterministic, token-based)                                         #
# --------------------------------------------------------------------------- #
# Default markers that show a value is being *dismissed* rather than asserted as
# current/authoritative. A scenario may override via scoring.dismissal_tokens.
DEFAULT_DISMISSAL = [
    "outdated", "superseded", "retired", "replaced", "previous", "former",
    "no longer", "earlier", "prior", "deprecated", "historical", "used to",
    "old ", "unverified", "no source", "not authoritative", "rumor", "hallway",
    "estimate", "draft", "unconfirmed", "should not", "unofficial", "not official",
    "informal", "anecdotal", "disregard",
]


def _has_any(text: str, tokens: list[str]) -> bool:
    t = text.lower()
    return any(tok.lower() in t for tok in tokens)


def _all_occurrences_dismissed(text: str, tokens: list[str], dismissal: list[str], window: int = 70) -> bool:
    """True if every occurrence of every token sits within `window` chars of a
    dismissal marker — i.e. the value is mentioned only to be discounted, not
    asserted as the answer. Vacuously true if no token occurs.
    """
    t = text.lower()
    dis = [d.lower() for d in dismissal]
    for tok in tokens:
        tl = tok.lower()
        start = 0
        while (i := t.find(tl, start)) != -1:
            ctx = t[max(0, i - window): i + len(tl) + window]
            if not any(d in ctx for d in dis):
                return False
            start = i + len(tl)
    return True


def score(scenario: dict, answer: str) -> dict[str, Any]:
    metric = scenario["metric"]
    s = scenario.get("scoring", {})
    a = answer.lower()
    dismissal = s.get("dismissal_tokens", DEFAULT_DISMISSAL)

    if metric == "permission_leak_rate":
        leaked = _has_any(a, s.get("leak_tokens", []))
        return {"metric": metric, "leaked": leaked, "good": not leaked}

    if metric == "stale_fact_avoidance":
        # Good = states the fresh value, and never presents the stale value as
        # current (mentioning it as outdated is fine).
        fresh = _has_any(a, s.get("fresh_tokens", []))
        stale_present = _has_any(a, s.get("stale_tokens", []))
        stale_dismissed = _all_occurrences_dismissed(a, s.get("stale_tokens", []), dismissal)
        good = fresh and stale_dismissed
        return {"metric": metric, "fresh": fresh, "stale_present": stale_present,
                "stale_dismissed": stale_dismissed, "good": good}

    if metric == "authority_accuracy":
        # Good = states the authoritative value, and never presents the wrong
        # value as authoritative (flagging it as unverified is fine).
        correct = _has_any(a, s.get("correct_tokens", []))
        wrong_present = _has_any(a, s.get("wrong_tokens", []))
        wrong_dismissed = _all_occurrences_dismissed(a, s.get("wrong_tokens", []), dismissal)
        good = correct and wrong_dismissed
        return {"metric": metric, "correct": correct, "wrong_present": wrong_present,
                "wrong_dismissed": wrong_dismissed, "good": good}

    if metric == "conflict_surfaced":
        all_tokens = s.get("surface_all_tokens", [])
        both = all(_has_any(a, [tok]) for tok in all_tokens) if all_tokens else False
        kw = _has_any(a, s.get("conflict_keywords", []))
        return {"metric": metric, "both_values": both, "conflict_keyword": kw, "good": both or kw}

    raise ValueError(f"unknown metric: {metric}")


# --------------------------------------------------------------------------- #
# Run & report                                                                 #
# --------------------------------------------------------------------------- #
@dataclass
class RunResult:
    scenario_id: str
    category: str
    metric: str
    condition: str
    answer: str
    n_withheld: int
    score: dict[str, Any]


def load_scenarios(path: str | Path) -> list[dict]:
    return yaml.safe_load(Path(path).read_text())


def run(
    bundle_dir: str | Path,
    scenarios: list[dict],
    agent,
    conditions: tuple[str, ...] = CONDITIONS,
    progress: Callable[[str], None] | None = None,
) -> list[RunResult]:
    service = KnowledgeService(bundle_dir)
    results: list[RunResult] = []
    for scenario in scenarios:
        for condition in conditions:
            context, withheld = build_context(service, scenario, condition)
            system, user = build_messages(scenario, context)
            answer = agent.answer(system, user)
            results.append(RunResult(
                scenario_id=scenario["id"],
                category=scenario["category"],
                metric=scenario["metric"],
                condition=condition,
                answer=answer,
                n_withheld=withheld,
                score=score(scenario, answer),
            ))
            if progress:
                verdict = "PASS" if results[-1].score["good"] else "fail"
                progress(f"  {scenario['id']:<26} {condition:<4} {verdict}")
    return results


def aggregate(results: list[RunResult]) -> dict[str, dict[str, float]]:
    """condition -> metric -> mean 'good' rate (1.0 = best on every metric)."""
    table: dict[str, dict[str, list[bool]]] = {}
    for r in results:
        table.setdefault(r.condition, {}).setdefault(r.metric, []).append(bool(r.score["good"]))
    return {
        cond: {metric: sum(v) / len(v) for metric, v in metrics.items()}
        for cond, metrics in table.items()
    }


def render_report(results: list[RunResult], agent_name: str) -> str:
    agg = aggregate(results)
    metrics = sorted({r.metric for r in results})
    lines = [
        f"# VKF Benchmark Results (agent: {agent_name})",
        "",
        "Score = fraction of scenarios where the agent behaved correctly "
        "(1.00 is best on every metric, including permission-leak, which is "
        "reported as *avoided* rate).",
        "",
        "| Condition | " + " | ".join(metrics) + " | overall |",
        "|" + "---|" * (len(metrics) + 2),
    ]
    for cond in CONDITIONS:
        if cond not in agg:
            continue
        row = agg[cond]
        cells = [f"{row.get(m, float('nan')):.2f}" for m in metrics]
        overall = sum(row.values()) / len(row) if row else float("nan")
        lines.append(f"| {cond} | " + " | ".join(cells) + f" | **{overall:.2f}** |")
    return "\n".join(lines)


RESULTS_START = "<!-- RESULTS:START -->"
RESULTS_END = "<!-- RESULTS:END -->"


def update_readme(path: str | Path, report: str) -> bool:
    """Replace the content between the RESULTS markers with ``report``.

    Returns True if the markers were found and the file rewritten.
    """
    path = Path(path)
    text = path.read_text()
    if RESULTS_START not in text or RESULTS_END not in text:
        return False
    head, rest = text.split(RESULTS_START, 1)
    _, tail = rest.split(RESULTS_END, 1)
    new = f"{head}{RESULTS_START}\n\n{report.strip()}\n\n{RESULTS_END}{tail}"
    path.write_text(new)
    return True


def results_to_dicts(results: list[RunResult]) -> list[dict]:
    return [
        {
            "scenario": r.scenario_id, "category": r.category, "metric": r.metric,
            "condition": r.condition, "n_withheld": r.n_withheld,
            "score": r.score, "answer": r.answer,
        }
        for r in results
    ]
