# PY-02 — terminal Quality Evidence

Supersedes the pre-closure summary at `10cc81620511af56befbb6140504d1991bb02846` (if present). Historical JSONL events remain explicitly superseded for terminal aggregation. This summary uses the `wave1-terminal` projection only.

Issue [#50](https://github.com/AlienLogicLab/alienintent/issues/50): **DONE**, Issue **CLOSED**. Agent-Ready **READY**. 1 combined verifier rejections; 2 verdicts; 2 execution cycles; first-pass accepted: **false**.

Accepted `8689771b9fccb9f86c7fdcc2e9d4f571408765f2`; landed `ab4efe54df752a4d7a35f047054435a24a21ddaf`. Final Python test observation: **23**. Worker DONE signal `2026-09-20T03:14:14Z`; dispatcher DONE `2026-09-20T03:14:20.229Z`; Issue closure `2026-09-20T03:31:11Z`. These are three distinct observations.

| Verdict sequence | Outcome | Directed report groups | Source |
|---|---|---|---|
| 1 | REJECT | 3 | [report](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747048805) |
| 2 | ACCEPT | 0 | [report](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747096363) |

Counts are report-local groups, not unique defects; ACCEPT closes blocking obligations, not every non-blocking observation. Detailed incidents, corrections and proof limitations: [closure reconciliation](../wave1-evidence-reconciliation.md).

Machine-readable measurement: [PY-02-quality-evidence.json](PY-02-quality-evidence.json). Prior measurements are retained in `superseded_measurement`, excluded from current aggregates.
