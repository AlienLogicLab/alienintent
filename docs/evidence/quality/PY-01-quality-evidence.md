# PY-01 — terminal Quality Evidence

Supersedes the pre-closure summary at `10cc81620511af56befbb6140504d1991bb02846` (if present). Historical JSONL events remain explicitly superseded for terminal aggregation. This summary uses the `wave1-terminal` projection only.

Issue [#2](https://github.com/AlienLogicLab/alienintent/issues/2): **DONE**, Issue **CLOSED**. Agent-Ready **READY**. 2 combined verifier rejections; 3 verdicts; 3 execution cycles; first-pass accepted: **false**.

Accepted `b07ea94768e794702aa2b6bbc038d764b08ee3ea`; landed `ab08449a0fac8d25374a80f4361a4023509118b1`. Final Python test observation: **6**. Worker DONE signal `2026-09-19T10:54:46Z`; dispatcher DONE `2026-09-19T10:54:51.347Z`; Issue closure `2026-09-19T10:59:10Z`. These are three distinct observations.

| Verdict sequence | Outcome | Directed report groups | Source |
|---|---|---|---|
| 1 | REJECT | 3 | [report](https://github.com/AlienLogicLab/alienintent/issues/2#issuecomment-5741009098) |
| 2 | REJECT | 2 | [report](https://github.com/AlienLogicLab/alienintent/issues/2#issuecomment-5741043709) |
| 3 | ACCEPT | 0 | [report](https://github.com/AlienLogicLab/alienintent/issues/2#issuecomment-5741087648) |

Counts are report-local groups, not unique defects; ACCEPT closes blocking obligations, not every non-blocking observation. Detailed incidents, corrections and proof limitations: [closure reconciliation](../wave1-evidence-reconciliation.md).

Machine-readable measurement: [PY-01-quality-evidence.json](PY-01-quality-evidence.json). Prior measurements are retained in `superseded_measurement`, excluded from current aggregates.
