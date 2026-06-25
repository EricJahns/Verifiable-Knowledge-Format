# Design Principles

## 1. Plain files are the source of truth

VKF should work in Git, code review, local editors, and static hosting. No database is required to author knowledge.

## 2. Human-readable first, agent-readable second

Humans must be able to inspect, edit, and review knowledge without specialized tools. Machine-readable metadata should enhance the document, not bury it.

## 3. Claims are smaller than documents

Documents contain many statements. Important statements should have IDs, evidence, confidence, and scope.

## 4. Knowledge has a lifecycle

Knowledge can become stale, disputed, superseded, deprecated, or retracted. The format must represent this directly.

## 5. Permissions are contextual

Knowing something internally does not mean an agent can quote it externally, train on it, or send it to another tool.

## 6. Agents propose; humans approve authority

Agents may draft, summarize, update, and detect conflicts. Human owners decide what becomes authoritative.

## 7. Compilation is optional

A bundle should be useful as files alone, but powerful systems can compile it into graphs, RAG indexes, APIs, dashboards, and reports.

## 8. Extend OKF, don't fork it

VKF is a strict superset of OKF v0.1. Every VKF addition lives in the
producer-extension key space OKF already reserves, so any conformant OKF bundle
is a valid VKF bundle and any VKF bundle degrades cleanly back to OKF. Adoption
is incremental — a team turns on governance field by field — and OKF tooling
keeps working.

## 9. Strictness is opt-in

OKF requires that consumers never reject a bundle. VKF honors that at Profile 0
and adds *opt-in* conformance profiles for teams that want validation with teeth.
A bundle declares the contract it commits to; nobody has strictness forced on them.
