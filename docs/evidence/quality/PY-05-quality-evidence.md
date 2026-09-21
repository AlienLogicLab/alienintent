# PY-05 quality evidence

Derived from [PY-05-quality-evidence.json](PY-05-quality-evidence.json), which is reconciled against [the trajectory](../execution-trajectories/PY-05.jsonl) by a deterministic consistency check. Not a raw authority source.

## What it was trying to prove

Connect the offline loop to the real upstream backlog through an Anti-Corruption Layer and authenticated webhook ingress, without letting GitHub concepts into the core. SF-REQ-005 primary.

## Verdict

`ACCEPTED_AND_DONE` after two independent rejections and two repair cycles. Not first-pass. Landed by normal merge `5b617a3e`; both required merge-result Actions succeeded.

| Measure | Value |
|---|---:|
| Verifier cycles / rejections | 3 / 2 |
| Blocking findings by cycle | 6 → 1 → 0 |
| Candidate additions by cycle | 472 → 189 → 3 |
| Proof regressions | 0 |
| Behavioural regressions | 0 |
| Authority interruptions | 0 |
| Liveness incidents | 0 |
| Release → DONE | 4,302 s |
| Tests at landing | 87 |

## How difficult convergence was

Easiest in the cohort. Findings and candidate size both fell monotonically, the final repair was three insertions in one test, and the verifier re-derived its own mutation battery rather than trusting the producer's. Repair mode: **CONVERGING**.

## Major failure classes

Four `BEHAVIORAL_DEFECT` and three `EVIDENCE_PROOF_DEFECT`. The single blocking finding that cost a whole extra cycle was a proof defect against **correct production behaviour**: the stale-revision fence worked, and its test could not go red. That is the SWF-24 standard applied twice in one BIU.

## What verification contributed

Both rejections came from a green suite. Neither would have been caught by running the tests. The verifier's independent thirteen-mutation battery is what distinguished proven behaviour from behaviour that merely happened to be correct.

## Regressions and monotonicity

None. One test was removed and **explicitly superseded** under SWF-23 §3 — the only authorized supersession in PY-05–PY-09.

## Founder authority and factory malfunction

Neither. No Founder decision was requested or supplied; no liveness incident, no operator intervention, no capacity failure.

## Lessons

- **CANDIDATE LEARNING — NOT PROMOTED:** an acceptance criterion whose test is overdetermined by an unmapped input is not proof. This is the third independent occurrence of the PY-02 "check that cannot fail" class and it remains unmechanized.
- **CANDIDATE LEARNING — NOT PROMOTED:** a fail-closed rule that rejects complete, unambiguous upstream data has inverted its criterion. Detectable by a positive control on the ordinary case.
- **OBSERVATION:** the producer's `npm test` count (310) and the verifier's observation (330) disagreed in all three cycles. Immaterial to the verdict, but it is a claim that was never reconciled.

## Unknown

Provider and model identity, token usage and monetary cost are **UNKNOWN** for every invocation. Attention-queue coverage for PY-05's window does not exist — absent telemetry, not zero.
