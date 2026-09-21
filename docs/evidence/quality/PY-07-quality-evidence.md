# PY-07 quality evidence

Derived from [PY-07-quality-evidence.json](PY-07-quality-evidence.json), reconciled against [the trajectory](../execution-trajectories/PY-07.jsonl) by a deterministic consistency check. Not a raw authority source.

## What it was trying to prove

Make missing authority a first-class, non-fatal, scoped execution outcome that escalates with decision-ready context, keeps independent work running, and re-admits automatically once a decision is durably recorded. SF-REQ-006 and SF-REQ-035 primary.

## Verdict

`ACCEPTED_AND_DONE` after two authority interruptions, two liveness incidents, five independent rejections and five repair cycles. Landed by normal merge `946e3cc0`; both required merge-result Actions succeeded.

| Measure | Value |
|---|---:|
| Verifier cycles / rejections | 6 / 5 |
| Blocking findings by cycle | 4 → 2 → 3 → 3 → 1 → 0 |
| Proof regressions | 0 |
| Behavioural regressions | **1** |
| Authority interruptions | 2 |
| Founder decisions required | **0** |
| Liveness incidents / operator interventions | 2 / 2 |
| Attention items | 5 |
| Release → DONE | 11,057 s |
| Tests at landing | 129 |

## How difficult convergence was

Harder than the finding counts suggest. Blocking findings went 4 → 2 → 3 → 3 → 1 → 0: they did not fall monotonically, and the middle three cycles are where the difficulty sits. Repair mode: **CONVERGING_AFTER_A_STAGNANT_PHASE**.

The stagnant phase has a structural marker. Cycles 2, 3 and 4 were **re-implementations on the release baseline**, not descendants of the candidate being repaired — the verifier said so each time. Across exactly those three cycles the same Scope §2 requirement was reported unsatisfied three times in three different shapes. Commit `822ca38` — *"start PY-07 repair cycle 5 from rejected candidate"* — marks the switch to descendant repair; the reviewable delta collapses to +189/−23 and then +55/−13, and the BIU converges in two cycles.

**INFERENCE, not established:** that re-implementation caused the stagnation. One BIU cannot separate that from the work simply having narrowed. Recorded so PY-10 can test it.

## Major failure classes

Nine `BEHAVIORAL_DEFECT`, two `EVIDENCE_PROOF_DEFECT`, two `ARCHITECTURE_CONFORMANCE`. Four of the five rejections are one class in four code paths: **an escalation that is registered but not decidable** — recorded, reported, not recoverable. It appeared at the admission path, the unresolved-effect path, the worker-raised path, and in `defer`, the escalation's own recommended disposition, which was terminal on every path.

## What verification contributed

The decisive contribution was proving branches against the **real operational store** rather than a double. Cycle 3's blocker was that the unresolved-effect escalation could not execute at all against `SQLiteOperationalStore` — its first action is a commit to the aggregate the FD-05 guard blocks — and was proven only against a subclass that fabricated a state the real store cannot hold. The candidate's own test passed with every effect row `confirmed`.

## Regressions

One behavioural regression, introduced and closed inside PY-07. Cycle 5's repair made `cancelled-by-decision` a non-terminal outcome, so a cancelled BIU was silently re-dispatched and completed by the next loop tick — and since `resume_after_decision()` *is* `start()`, deciding **any unrelated escalation** revived it. The durable record said `cancel`; the store said `DONE / success`. The candidate's own test asserted only the instant after submission.

No proof regression: no previously required test, negative control or fitness check was removed in any cycle.

## Founder authority

None required. Both `FOUNDER_EXCEPTION`s were producers correctly refusing a release performed without a release record. The coordinator's own words: *"The producers were right to refuse, and the omission is the coordinator's."*

## Did the factory malfunction

Yes, twice, and both became durable rules:

- **Release without a release record.** Fixed as an amendment to SF-REQ-002 plus the SWF-21 checklist, implemented as `release_admission.py` with 14 tests, and replayed against PY-07 as it stood — the gate refuses on exactly the two grounds the producers cited.
- **Liveness retried a completed judgment-required effect.** Fixed in SWF-29; implemented as `judgment_suppression` with `test_liveness_suppression.py`, 8 tests.

Both are recorded in [`../2026-09-21-liveness-retry-and-release-admission.md`](../2026-09-21-liveness-retry-and-release-admission.md).

## Lessons

- **PROMOTED, GATED:** a release must carry a complete release record before a worker launches. Mechanized in `release_admission.py`; a failed check is a refusal, not a warning.
- **PROMOTED, GATED:** liveness repairs missing effects and must not retry completed effects whose result requires judgment. Mechanized as `judgment_suppression`.
- **CANDIDATE LEARNING — NOT PROMOTED:** restarting a repair from the baseline rather than from the rejected candidate discards the reviewable delta and, here, coincided with three cycles of restating the same defect.
- **CANDIDATE LEARNING — NOT PROMOTED:** a test that asserts only the instant after a state change does not prove the change is terminal. Two ticks, or a decision on an unrelated item, is the discriminating case.

## Unknown

Provider and model identity, token usage and monetary cost are **UNKNOWN**. Per-cycle candidate diffs for cycles 2–4 are not comparable with cycles 5–6 because the parents differ in kind.
