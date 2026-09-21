# PY-09 execution trajectory — IN FLIGHT

> **Capture boundary: 2026-09-21T02:45:00Z.** PY-09 was active when this record was made. Issue #57 is OPEN, Project Status `IMPLEMENT`, three verifier rejections recorded, repair cycle 4 interrupted by provider quota exhaustion and restarted on a different provider adapter under Founder authorization, and PRODUCER invocation `9979bdcc` still running. Final verdict, accepted candidate, landing SHA, DONE timestamp and total cycle count are **UNKNOWN**. Nothing below is a prediction of the outcome.

Raw events: [`PY-09.jsonl`](PY-09.jsonl). Derived measures: [`../quality/PY-09-quality-evidence.json`](../quality/PY-09-quality-evidence.json).

## Why this BIU matters to the record

PY-09 is the first BIU released with the PY-08 lesson already binding on it. This record exists to test whether that changed behaviour, and it must be read as an interim measurement.

## The lesson was present before execution, in three places

1. **The contract.** `docs/work-units/python/PY-09.md` carries SWF-23 §4b.
2. **The Agent-Ready assessment**, produced before release and independent of the release comment, lists as a material risk: *"The verification harness must be established before broad repair work, with discriminating proof for changed paths."*
3. **The release comment**, which makes §4b binding, states the PY-08 evidence that produced it, and adds: *"Your own Agent-Ready assessment names this as a material risk; treat it as the first obligation, not the last."*

This is a complete propagation chain — observed → generalized → made durable (SWF-23 §4b, commit `9f64ebf`) → carried into a contract and an assessment → present before execution. That much is **FACT**.

## Cycles to the capture boundary

| Cycle | Candidate | Verifier | Verdict | Blocking findings | pytest | Fitness |
|---|---|---|---|---:|---:|---|
| 1 | `57826f02` | `08ec7d64` | REJECT | 5 | 173 | not reported |
| 2 | `c1674ffc` | `483a8a7b` | REJECT | 2 | 183 | not reported |
| 3 | `c9563214` | `923ee4d9` | REJECT | 5 | 189 | PASS |

All three rejections open by reproducing the producer's claims and confirming AC 9 is satisfied. None rests on a red suite.

## What the verifier did differently

The verifier turned §4b step 2 into a **standing negative control it repeats every cycle**: delete the validation body of `_require`, so all six delegated checks unconditionally return PASS, and re-run the suite.

| Cycle | Gutted-`_require` result |
|---|---|
| 1 | not applicable — no check logic existed to gut |
| 2 | **183 passed, zero tests red** |
| 3 | **189 passed, zero tests red** |

It also, at cycle 3, mutation-tested each check individually and published the table: six checks now produce 1–2 failing tests when made unconditionally passing. That is the harness beginning to exist, proven rather than asserted.

The cycle-1 rejection cites §4b step 1 by name: *"confirm the required verification harness exists — present and executable, not planned, not deferred. That harness does not exist in the candidate. Inline stub lambdas defined in the assertion body are not fixtures or doubles; they cannot go red when a check breaks, because there is no check."*

## What the producer did

Cycle 1 shipped an aggregator over caller-supplied callables — **0 of 8 Scope §2 checks implemented** — while every substrate the checks needed already existed at the baseline. Cycle 2 moved the delegation one level down: six of eight checks still received a dataclass of booleans the adapter itself decided. Reproduced by the verifier: doctor returned PASS / exit 0 / `ready=True` against a real SQLite store whose `preflight()` rejects the schema **and** a profile whose lifecycle mapping is genuinely ambiguous — two of the five negative-evidence conditions the contract names by name, present in the installation, undetected.

Cycle 3 closed four of AC 2's five named cases with real check logic and real fixtures. Five blocking findings remain, including one check (`execution`) with no evidence path at all, so doctor cannot reach PASS on evidence; the boolean escape hatch surviving as the candidate's *only* passing path; and AC 4 still unable to go red for a write — an injected file write went undetected across 189 tests.

## Cycle 4 — a provider-capacity interruption, and the first genuine human decision in the cohort

At 02:08:12Z the coordinator posted its cycle-3 convergence assessment. Its direction is the first in PY-09 addressed to the **producer** rather than describing verifier findings:

> **For every test you add or rely on, delete or neuter the code it covers and confirm the suite goes red.** If it stays green, the test is not evidence and does not count toward an acceptance criterion. Run that check yourself before publishing the candidate — the verifier is already running it, and three cycles have now been spent discovering the answer at verification time instead of implementation time.

The cycle-4 producer `e84d12a0` started at 02:06:56Z and died at 02:12:46Z, about 350 seconds in, when its provider returned `turn.failed` on a usage limit. It posted no result marker, so the dispatcher recorded `DURABLE_RESULT_MISSING`. It was working normally — the suite stood at 33 passed / 2 failed and it was mid-edit on `tests/installation/test_doctor.py`.

This is the failure mode SWF-09 anticipates: for CLI providers, token and monetary budget are *measured*, not hard-enforced, so exhaustion surfaces as a dead invocation rather than a clean budget refusal. It is the second provider-capacity interruption in Wave 1, after PY-03's.

**Three earlier lessons were consumed here, visibly:**

- **SWF-29 (from PY-07).** Liveness reconciliation was **suppressed** rather than re-emitted. Relaunching would have started a producer that hit the same wall within minutes and kept doing so every grace period. The coordinator said so explicitly. That is the PY-07 rule applied to a condition PY-07 did not contain.
- **SWF-30 (from PY-06).** Worktree `63097907` holds real uncommitted content — `doctor.py`, `test_doctor.py`, `test_doctor_evidence.py`, 65 insertions / 60 deletions — so under condition 6 it is required evidence and exempt from routine cleanup. The recovery comment instructs the next producer to read it and carry forward what is sound rather than recreate it from memory.
- **SWF-09 budget policy.** Changing a worker's provider is a profile change with budget implications and is explicitly *not* a coordinator decision.

The coordinator's conclusion — *"This needs an operator decision, not a repair"* — produced **the first genuine human decision required by any BIU in PY-05 through PY-09**. The Founder authorized running the PY-09 PRODUCER on the `claude` adapter for this recovery only. Contract, scope, acceptance criteria, baseline and cycle number unchanged; this continues cycle 4 and is not a new repair cycle. 532 seconds from the dead invocation to the authorization.

## Provider identity, for the only time in this cohort

The incident is the only place in PY-05–PY-09 where actor provider identity becomes durable. The PRODUCER adapter is **`codex`** under provider-default funding; the VERIFIER runs on the **`claude`** adapter under a separate subscription, which is why the verifier was unaffected. The dispatcher state record carries no provider field for any invocation, so the same assignment in PY-05–PY-08 is an inference and stays **UNKNOWN** in those records.

## The honest reading at the boundary

**FACT.** Zero SWF-23 regressions across three cycles. Every rejection opens with an explicit "closed since the last cycle, do not rewrite" section listing preserved evidence. No previously proven criterion was traded.

**FACT.** Blocking findings did not fall: 5 → 2 → 5. The test count rose 173 → 183 → 189. Three rejections already exceeds PY-05's two.

**FACT.** The three rejections rest on one cause throughout: implementation exists, the suite is green, and the changed paths carry no coverage that can go red. Repair mode at the boundary is `VERIFICATION_MISSING`.

**INFERENCE.** §4b changed the **verifier's method** more visibly than it changed the **producer's sequencing**. The verifier adopted a repeatable, discriminating negative control from cycle 2 and has applied it identically since. The producer's first two candidates still widened implementation ahead of the harness, which is the order §4b prohibits.

**HYPOTHESIS, unsupported by this evidence.** That §4b will reduce PY-09's total cycle count. It cannot be claimed: the BIU is unfinished and its cycle count already exceeds two of the five BIUs in this cohort. What the evidence supports so far is a change in *how rejections are argued and what they preserve*, not a reduction in how many there are.

**FACT — the gap was identified inside the loop, not only here.** The coordinator's cycle-3 assessment names exactly this: three cycles were spent discovering at verification time what the producer could have checked before publishing, and it converts the verifier's method into a producer obligation. So the propagation chain now has one more link — observed in PY-08 → generalized as SWF-23 §4b → carried into PY-09's contract and assessment → **restated as a pre-publication producer method at PY-09 cycle 3**.

**UNKNOWN.** Whether cycle 4 honours that method. The producer that received the direction died on a provider quota before publishing anything, and its replacement was still running at the capture boundary.
