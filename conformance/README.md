# VKF Conformance Corpus

A shared, inspectable set of bundles with **expected validation outcomes**. This
is what separates a *standard* from a library: any implementation of VKF can run
this corpus and check that it agrees with the reference validator.

- `cases/<name>/` — a minimal bundle exercising one rule.
- `expectations.yaml` — for each case, the expected outcome (`pass` / `error`)
  at conformance profiles 0, 1, and 2.

`tests/test_conformance.py` runs every case at every profile and asserts the
reference validator matches. The cases double as executable documentation of the
profile model:

| Case | Demonstrates |
|---|---|
| `okf-minimal`, `unregistered-type-tolerated` | every conformant OKF bundle is valid VKF at all profiles (superset) |
| `okf-no-type` | the one OKF requirement (`type`) is enforced even at Profile 0 |
| `governed-clean` | a fully-governed bundle passes every profile |
| `missing-owner`, `dangling-ref`, `dependency-cycle`, `bad-date`, `duplicate-alias`, `malformed-claim` | Profile 1 (`governed`) adds teeth — these pass at 0, error at 1 |
| `verified-no-last-verified`, `claim-no-evidence` | Profile 2 (`verified`) is stricter still — these pass at 1, error at 2 |

To add a rule: drop a bundle under `cases/`, add its expected outcomes to
`expectations.yaml`, and the parametrized test picks it up automatically.
