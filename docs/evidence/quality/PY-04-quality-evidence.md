# PY-04 — terminal Quality Evidence

Supersedes the pre-closure summary at `10cc81620511af56befbb6140504d1991bb02846` (if present). Historical JSONL events remain explicitly superseded for terminal aggregation. This summary uses the `wave1-terminal` projection only.

Issue [#52](https://github.com/AlienLogicLab/alienintent/issues/52): **DONE**, Issue **CLOSED**. Agent-Ready **READY**. 9 combined verifier rejections; 10 verdicts; 10 execution cycles; first-pass accepted: **false**.

Accepted `03896f6267e06cd9a52afe4ab63dee32d221c538`; landed `0170af0b3d995935835c8b7790341f93b5b23eb4`. Final Python test observation: **65**. Worker DONE signal `2026-09-20T12:26:19Z`; dispatcher DONE `2026-09-20T12:26:25.430Z`; Issue closure `2026-09-20T12:31:12Z`. These are three distinct observations.

| Verdict sequence | Outcome | Directed report groups | Source |
|---|---|---|---|
| 1 | REJECT | 5 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5748256385) |
| 2 | REJECT | 5 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5748347948) |
| 3 | REJECT | 10 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749047406) |
| 4 | REJECT | 3 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749103419) |
| 5 | REJECT | 2 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749232876) |
| 6 | REJECT | 1 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749297024) |
| 7 | REJECT | 1 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749371003) |
| 8 | REJECT | 1 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749550646) |
| 9 | REJECT | 2 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749643685) |
| 10 | ACCEPT | 0 | [report](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749754285) |

Counts are report-local groups, not unique defects; ACCEPT closes blocking obligations, not every non-blocking observation. Detailed incidents, corrections and proof limitations: [closure reconciliation](../wave1-evidence-reconciliation.md).

Machine-readable measurement: [PY-04-quality-evidence.json](PY-04-quality-evidence.json). Prior measurements are retained in `superseded_measurement`, excluded from current aggregates.
