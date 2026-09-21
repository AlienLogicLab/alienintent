# Wave 1 final yield snapshot

FACTS only; no causal attribution or learning consolidation. Supersedes interim yield tables at the terminal boundary.

| BIU / Issue | Final state | Rejections | Verdicts / cycles | First-pass | Tests |
|---|---|---:|---:|---|---:|
| [PY-01 #2](https://github.com/AlienLogicLab/alienintent/issues/2) | DONE / CLOSED | 2 | 3 / 3 | False | 6 |
| [PY-02 #50](https://github.com/AlienLogicLab/alienintent/issues/50) | DONE / CLOSED | 1 | 2 / 2 | False | 23 |
| [PY-03 #51](https://github.com/AlienLogicLab/alienintent/issues/51) | DONE / CLOSED | 1 | 2 / 2 | False | 40 |
| [PY-04 #52](https://github.com/AlienLogicLab/alienintent/issues/52) | DONE / CLOSED | 9 | 10 / 10 | False | 65 |
| [PY-05 #53](https://github.com/AlienLogicLab/alienintent/issues/53) | DONE / CLOSED | 2 | 3 / 3 | False | 87 |
| [PY-06 #54](https://github.com/AlienLogicLab/alienintent/issues/54) | DONE / CLOSED | 4 | 5 / 5 | False | 110 |
| [PY-07 #55](https://github.com/AlienLogicLab/alienintent/issues/55) | DONE / CLOSED | 5 | 6 / 6 | False | 129 |
| [PY-08 #56](https://github.com/AlienLogicLab/alienintent/issues/56) | DONE / CLOSED | 6 | 7 / 7 | False | 158 |
| [PY-09 #57](https://github.com/AlienLogicLab/alienintent/issues/57) | DONE / CLOSED | 3 | 4 / 4 | False | 209 |
| [PY-09B #68](https://github.com/AlienLogicLab/alienintent/issues/68) | DONE / CLOSED | 0 | 1 / 1 | True | 308 |
| [PY-10 #58](https://github.com/AlienLogicLab/alienintent/issues/58) | DONE / CLOSED | 0 | 1 / 1 | True | 344 |

- Executed: 11; first-pass accepted: 2/11 (18.18%). **PY-09B first-pass accepted; PY-10 first-pass accepted.**
- Earlier eight (PY-01…PY-08): 0/8; earlier nine including PY-09: 0/9.
- Combined verifier rejections: 33; distribution (rejections: BIU count): `{0: 2, 1: 2, 2: 2, 3: 1, 4: 1, 5: 1, 6: 1, 9: 1}`.
- Repair-return distribution is the same; execution cycles = 1 + repair returns: `{1: 2, 2: 2, 3: 2, 4: 1, 5: 1, 6: 1, 7: 1, 10: 1}`. Same-phase retries and provider failover excluded.
- Python suite growth at accepted milestones: 6 → 23 → 40 → 65 → 87 → 110 → 129 → 158 → 209 → 308 → 344; net +338 from PY-01. These are historical verifier/closure observations, not fresh reruns of eleven revisions.
- FOUNDER_EXCEPTION protocol markers: 9; not equivalent to genuine authority gaps.
- Known execution provider-capacity interruptions: 2 (PY-03 closure, PY-09 IMPLEMENT); Agent-Ready quota/failover episode separately scoped. Complete provider interruption telemetry: UNKNOWN.
- Known regressions: PY-04 lost proof; PY-08 behavioral/proof regressions reported in its trajectory. A globally deduplicated defect/regression total is UNKNOWN.
- Inserted/split BIUs: PY-09B inserted from PY-10 by SWF-33; 1 inserted, no renumbering.
- Control-plane incidents: dropped delivery/liveness gap (PY-06); attention activation and release admission (PY-06/07/08); stale Issue projection (PY-06/07); PY-09 no-verdict, duplicate attention identity and false recovery alarm. Incident taxonomy/deduplicated global total UNKNOWN.
- UNKNOWN: end-to-end tokens/cost, per-invocation model attribution, unique defects across carried findings, escaped defects, REVIEW-versus-VERIFY attribution, complete historical transition timestamps.

Sources and limitations: [manifest](wave1-closure-manifest.md), [reconciliation](wave1-evidence-reconciliation.md), [repair records](wave1-repair-cycles.json).

Authority qualification: the two first-pass BIUs used Claude after the PY-09-only recovery; a durable extension of that authorization is UNKNOWN. This does not change their observed verdict histories. See the reconciliation.
