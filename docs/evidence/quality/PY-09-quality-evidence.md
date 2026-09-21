# PY-09 quality evidence — INTERIM

> **Capture boundary 2026-09-21T02:45:00Z. PY-09 is in flight.** Every terminal measure is **UNKNOWN**, not zero: final verdict, accepted candidate, landing SHA, DONE timestamp, total cycle count, elapsed time to acceptance, test count at landing.

Derived from [PY-09-quality-evidence.json](PY-09-quality-evidence.json), reconciled against [the trajectory](../execution-trajectories/PY-09.jsonl) by a deterministic consistency check. Not a raw authority source.

## What it is trying to prove

A fail-closed, read-only doctor gate that refuses autonomous work unless the configured profile has positively evidenced configuration, integration, persistence and execution readiness. SF-REQ-038 primary, under SWF-13's confirmed fail-closed semantics.

## State at the boundary

| Measure | Value |
|---|---:|
| Verifier cycles / rejections | 3 / 3 |
| Blocking findings by cycle | 5 → 2 → 5 |
| pytest by cycle | 173 → 183 → 189 |
| Proof regressions | 0 |
| Behavioural regressions | 0 |
| **Provider-capacity failures** | **1** |
| Authority interruptions | 1 (operator decision after the capacity failure) |
| **Genuine human decisions required** | **1** — the first in PY-05–PY-09 |
| Human-blocked | 532 s |
| Liveness incidents / suppressions | 0 / **1** |
| Attention items | 3 (one rejection threshold, two `DURABLE_RESULT_MISSING`) |
| Coordinator convergence assessments | 1 |
| Release → cycle-4 recovery authorization | 4,512 s |
| Final verdict | **UNKNOWN** |

## How difficult convergence is so far

Repair mode at the boundary: **VERIFICATION_MISSING**. All three rejections rest on one cause — implementation exists, the suite is green, and the changed paths carry no coverage that can go red. Blocking findings have not fallen while the test count has risen.

## What verification is contributing

The verifier turned SWF-23 §4b step 2 into a repeatable negative control and has run it identically every cycle: delete the validation body of `_require` so all six delegated checks unconditionally PASS, then re-run the suite.

| Cycle | Result |
|---|---|
| 1 | not applicable — no check logic existed |
| 2 | **183 passed, zero tests red** |
| 3 | **189 passed, zero tests red** |

At cycle 3 it also mutation-tested each check individually and published the table: six checks now yield 1–2 failing tests when made unconditionally passing. That is the harness beginning to exist, and it is proven rather than asserted.

It has twice reproduced the criterion the contract exists for, inverted: doctor returning PASS / exit 0 / `ready=True` against a real SQLite store whose `preflight()` rejects the schema **and** a profile whose lifecycle mapping is genuinely ambiguous — two of the five negative-evidence conditions named in AC 2, present in the installation, undetected.

## Proof monotonicity

Held. Every rejection opens with an explicit *"closed since the last cycle, carried forward, do not rewrite"* section enumerating preserved evidence, and none reports a regression. Zero proof regressions, zero behavioural regressions across three cycles.

## Founder authority and factory malfunction

**One genuine human decision — the first in this cohort.** The cycle-4 producer's provider account exhausted its quota mid-invocation (`turn.failed`, usage limit) and died after about 350 s without posting a result marker. The coordinator's disposition: *"This needs an operator decision, not a repair"* — wait roughly nine hours for the quota reset, add credit, or move the PRODUCER to the `claude` adapter. Changing a worker's provider is a profile change with budget implications under SWF-09 and is explicitly not a coordinator decision. The Founder authorized the `claude` adapter for this recovery only. 532 s blocked.

No `FOUNDER_EXCEPTION` was raised by any worker, and no liveness gap occurred. The factory did not malfunction: it detected a dead invocation, suppressed recovery rather than retrying into the same wall, preserved the partial work, and escalated the one decision it did not own.

**Three earlier lessons were consumed in that sequence** — SWF-29 liveness judgment suppression (from PY-07), SWF-30 worktree retention for real uncommitted content (from PY-06), and SWF-09's rule that provider substitution is not a coordinator decision. This is the clearest instance in the cohort of durable rules doing work on a condition none of them was written for.

## Did the PY-08 lesson reach this BIU

**FACT — propagation is complete and verifiable.** SWF-23 §4b is carried in the PY-09 contract, named as a material risk in the Agent-Ready assessment produced **before** release, and made binding by the release comment, which also states the PY-08 evidence behind it.

**FACT — effectiveness is not yet demonstrated.** Three rejections in three cycles, findings 5 → 2 → 5, already more rejections than PY-05 needed in total. The producer's first two candidates widened implementation ahead of the harness, which is the order §4b prohibits.

**INFERENCE.** The rule has changed the verifier's method more than the producer's sequencing. The verifier adopted a discriminating, repeated negative control from cycle 2; the producer reached a discriminating harness only at cycle 3, after two rejections said so.

**Do not read this as the rule failing.** Zero regressions across three cycles is itself a departure from PY-07 and PY-08, and cycle 3 is the first in the cohort where a verifier published a per-check mutation table. But effectiveness measured as *fewer cycles* is **not supported** by the evidence at this boundary, and claiming it would be the kind of tidy narrative this record exists to prevent.

## Lessons visible so far

- **CANDIDATE LEARNING — NOT PROMOTED:** a rule addressed to a repair loop reaches the coordinator and the verifier directly, and the producer only through the rejection it causes. If PY-10 repeats the pattern, the gap is in how the rule reaches the producing actor.
- **CANDIDATE LEARNING — NOT PROMOTED:** the gutted-validator negative control the verifier runs here is a general, cheap, mechanizable check — *make the validator unconditionally pass and require the suite to go red*. It is currently a habit of one verifier, not a promoted VERIFY capability.
- **OBSERVATION:** a check that receives a boolean the adapter itself decided is weaker evidence than a present config key, which binding rule 2 already names as insufficient. The verifier had to state this twice.

## Provider identity — partially known, for the only time in this cohort

The incident is the only durable statement of actor provider identity in PY-05–PY-09: PRODUCER on the **`codex`** adapter under provider-default funding, VERIFIER on the **`claude`** adapter under a separate subscription, and the recovery producer on `claude` by Founder authorization for this recovery only. The dispatcher state record carries no provider field, so the same assignment in PY-05–PY-08 is an inference and stays UNKNOWN there.

## Unknown

Everything terminal, plus model identity for every invocation, token usage — including the tokens the exhausted invocation consumed, which is the one number that would have made the quota failure predictable — monetary cost, and the outcome of the cycle-4 continuation producer. **This record must be superseded once PY-09 reaches a terminal outcome.**
