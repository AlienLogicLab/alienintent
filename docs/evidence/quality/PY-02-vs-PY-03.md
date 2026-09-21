# PY-02 vs PY-03

> **Terminal reconciliation notice — Superseded by:** [Wave 1 Closure Manifest](../wave1-closure-manifest.md) and [evidence reconciliation](../wave1-evidence-reconciliation.md) for terminal counts, timestamps and comparisons. This document is retained as historical observation/interpretation at its original capture boundary; it is not the current Wave 1 aggregate. No historical hypothesis becomes a terminal causal conclusion.


## Direct comparison

| Measure | PY-02 | PY-03 |
|---|---:|---:|
| Total elapsed seconds | 3,788 | 10,533 |
| Producer candidate attempts | 2 | 3 |
| Verifier cycles | 2 | 2 |
| Repair cycles | 1 | 1 |
| Blocking findings | 3 | 4 |
| First-pass accepted | no | no |
| Human attention blocked seconds | 1,832 | 125 |
| Closure seconds | 2,206 | 8,152 |
| Provider capacity failures | 0 observed | 1 observed |
| Final outcome | ACCEPTED_AND_DONE | ACCEPTED_AND_DONE |

## Early observations

- **OBSERVATION:** Both BIUs required one independent-rejection/rework/acceptance sequence and ended landed and DONE.
- **OBSERVATION:** PY-03 had an observed model-capacity failure during closure; PY-02 had an explicit landing-authority wait.
- **INFERENCE:** The larger PY-03 closure interval cannot be attributed wholly to provider capacity because the durable record does not explain the entire post-failure gap.
- **UNKNOWN:** Two BIUs do not establish a trend in quality, cost, capacity, or delivery speed.
- **UNKNOWN:** End-to-end cost comparison is unavailable because producer cost telemetry is absent in both records.
