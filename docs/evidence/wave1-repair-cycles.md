# Wave 1 repair-cycle data — terminal

Supersedes the interim PY-02…PY-09 extraction at `10cc81620511af56befbb6140504d1991bb02846`. The previous records remain in `superseded_records` in [JSON](wave1-repair-cycles.json); they are not execution cycles.

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

The current 44 records are independent verifier verdicts: 33 REJECT + 11 ACCEPT. `cycle` is the reconstructed verification/execution pass; FOUNDER_EXCEPTION, provider interruptions and same-phase retries are not verdict records.

`repair_finding_groups` counts directed report finding groups, retaining grouping rather than counting mentions or expanding subpoints. `findings_total` and unique findings are UNKNOWN when no complete source count exists. ACCEPT supports zero blocking groups under the verifier contract, not zero open non-blocking observations. Carried groups count as per-cycle occurrences only.

Corrections and source-specific definitions: [reconciliation](wave1-evidence-reconciliation.md). Regenerate offline with `rtk proxy python3 tools/evidence/reconcile_wave1.py --write`; verify with `rtk proxy python3 tools/evidence/check_wave1.py`.
