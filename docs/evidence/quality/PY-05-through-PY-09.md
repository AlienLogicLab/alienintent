# PY-05 through PY-09 — cross-BIU comparison

> **Terminal reconciliation notice — Superseded by:** [Wave 1 Closure Manifest](../wave1-closure-manifest.md) and [evidence reconciliation](../wave1-evidence-reconciliation.md) for terminal counts, timestamps and comparisons. This document is retained as historical observation/interpretation at its original capture boundary; it is not the current Wave 1 aggregate. No historical hypothesis becomes a terminal causal conclusion.


Derived from the five Quality Evidence documents in this directory and their trajectories in [`../execution-trajectories/`](../execution-trajectories/). PY-02–PY-04 figures are carried from the existing records for context and are not re-derived here.

> **PY-09 is in flight at the 2026-09-21T02:45Z capture boundary.** Its row is interim. Any trend reading that depends on PY-09's terminal outcome is marked HYPOTHESIS.

## The table

| | PY-05 | PY-06 | PY-07 | PY-08 | PY-09 |
|---|---|---|---|---|---|
| Purpose | Work Management ACL + webhook ingress | Invocation runtime + candidate custody | HumanDecisionRequired + Decision Inbox | Operator Control Plane CLI (P0) | Doctor / pre-autonomy validation |
| Agent-Ready locality | LOW | MEDIUM | LOW | MEDIUM | LOW |
| Owner clarifications | 0 | 0 | 0 | 0 | 0 |
| First-pass accepted | no | no | no | no | no |
| Verifier cycles | 3 | 5 | 6 | 7 | 3 *(so far)* |
| Rejection cycles | 2 | 4 | 5 | 6 | 3 *(so far)* |
| Findings by cycle | 6→1→0 | 9→6→5→2→0 | 4→2→3→3→1→0 | 12→14→11→10→8→3→0 | 5→2→5 |
| Proof regressions | 0 | 0 | 0 | **2** | 0 |
| Behavioural regressions | 0 | 0 | **1** | **2** | 0 |
| Defects introduced by repair | 0 | 0 | 1 | **3** | 0 |
| Authority interruptions | 0 | 1 | 2 | 1 | 1 |
| **Genuine human decisions required** | **0** | **0** | **0** | **0** | **1** |
| Provider-capacity failures | 0 | 0 | 0 | 0 | **1** |
| Liveness incidents | 0 | 0 | **2** | **1** | 0 |
| Liveness suppressions | 0 | 0 | 0 | 0 | **1** |
| Operator interventions | 0 | 0 | 2 | 1 | 0 |
| Candidate custody failures | 0 | 0 | 0 | 0 | 0 |
| Architecture violations | 0 | 0 | 0 | 0 | 0 |
| Tests at landing | 87 | 110 | 129 | 158 | UNKNOWN |
| Release → DONE | 4,302 s | 7,939 s | 11,057 s | 11,443 s | UNKNOWN |
| Implementation active | 2,363 s | 3,582 s | 6,597 s | 5,337 s | 1,913 s *(3 cycles)* |
| Verification active | 1,530 s | 2,218 s | 3,153 s | 4,220 s | 1,758 s *(3 cycles)* |
| Human-blocked | 0 s | 106 s | 806 s | 134 s | 532 s |
| Issue-closure lag after DONE | 1 s | **20,997 s** | **6,482 s** | 134 s | n/a |
| Major lesson | proof that cannot go red | object without an executed path; baseline identity discipline | release records; liveness vs judgment | verification-first sequencing | prove your own tests before publishing |
| Lesson made durable | **no** | baseline: **yes — gated**; executed-path: **no** | **yes — gated** ×2 | **yes — documented / prompted** | not yet — Issue comment only |
| Consumed by a later BIU | — | yes (PY-08, PY-09 releases; PY-09 worktree retention) | yes (PY-08 release; PY-09 capacity recovery) | yes (PY-09 contract, assessment, release) | UNKNOWN — PY-09 cycle 4 unfinished |

For context, the earlier cohort: PY-02 — 2 cycles, 1 rejection, 3 blocking findings, 3,788 s, **1 Founder decision**, 1,832 s blocked. PY-03 — 2 cycles, 1 rejection, 4 findings, 10,533 s, **1 Founder decision**, 1 provider-capacity failure. PY-04 — 9 rejections, 21,810 s, **1 Founder decision** (SWF-22 custody transfer), 7,074 s blocked, 1 false authority request.

## Trends

Distinguishing **FACT** (directly observed), **INFERENCE** (supported but not isolated) and **HYPOTHESIS** (consistent, not established).

### 1. Is first-pass quality improving?

**FACT: no BIU in Wave 1 has ever been accepted first-pass.** Eight for eight across PY-02–PY-09 — seven accepted, each after at least one rejection, plus PY-09 rejected on its first candidate and still in flight. Rework is the normal path in this factory, not the exception.

**FACT:** the *shape* of the first rejection has changed. PY-05 and PY-06 opened on behavioural defects. PY-08 and PY-09 opened on the command surface or the check set never having executed at all against a real composition root. The first rejection is increasingly about what was never exercised rather than about what was exercised wrongly.

### 2. Are repair cycles becoming fewer or more targeted?

**FACT: not fewer.** 2 → 4 → 5 → 6 rejections across PY-05 → PY-08, and PY-09 is at 3 and unfinished. Cycle count rose monotonically through the cohort.

**INFERENCE:** cycle count tracks **contract breadth**, not defect density. PY-05 (narrow adapter, LOW locality) took 2; PY-08 (a whole command surface plus proof obligations, MEDIUM locality) took 6. Agent-Ready locality predicts the direction in four of five cases; PY-07 is the exception — LOW locality, 5 rejections.

**FACT:** repairs became more targeted *within* the harder BIUs once directed to be. PY-07's final two candidates were +189/−23 and +55/−13; PY-08's cycle-6 was a directed verification-only cycle; PY-05's final repair was three insertions in one test.

### 3. Are previously learned defects recurring?

**FACT: yes, and this is the strongest signal in the dataset.** The class *"a check that passes because it cannot fail"* was recorded as a PY-02 candidate learning and left unpromoted. It then appeared as PY-05 finding 1, PY-05 finding 7 (a whole extra cycle against correct production code), PY-06's weak malformed-locator negative control concealing a real defect, PY-08 AC 4 / the verification requirements for five consecutive cycles, and PY-09's gutted-`_require` control returning zero red tests twice.

**FACT:** the class *"a correct object with no executed path that uses it"* was named by the PY-06 verifier in three consecutive cycles, recurred as PY-08's duck-typed profile shape, and recurred again as PY-09's aggregator over callables nothing constructs.

Model cognition is still rediscovering both classes at every BIU.

### 4. Is proof becoming more discriminating?

**FACT: yes, and measurably.**

| BIU | Strongest proof technique the verifier applied |
|---|---|
| PY-05 | independently re-derived 13-mutation battery, twice |
| PY-06 | end-to-end execution against real worktrees, remote and fresh clone; red–green by reverting only the repaired source files |
| PY-07 | probes against the real SQLite store that exposed a branch unreachable in production; red–green on the candidate's own regression test |
| PY-08 | the shipped CLI driven as a subprocess against a real composition root, with a published command/exit-status table at every cycle |
| PY-09 | a standing, repeated gutted-validator negative control, plus a per-check mutation table |

Each verifier built on the previous one's method without any mechanism requiring it to.

### 5. Are regressions decreasing?

**FACT:** PY-05 0, PY-06 0, PY-07 1 behavioural, PY-08 2 proof + 2 behavioural + 3 introduced defects, PY-09 0 in three cycles.

**INFERENCE:** regressions concentrate where the proof harness is thinnest, not where the code is largest. PY-06's candidate grew to +962/−2 across five cycles with zero regressions and zero tests dropped, because every cycle's inventory was diffed. PY-08 regressed twice while its two proof obligations went untouched.

### 6. Is AlienIntent moving known failure classes toward deterministic enforcement?

**Partially, and only for control-plane classes.** Two of the four durable lessons in this cohort reached a gate; the two engineering-quality lessons did not. See [the factory-incident and learning record](../wave1-factory-incidents-and-learning-PY-05-to-PY-09.md) for the graduation table.

### 7. Is model cognition increasingly focused on novel failures?

**FACT: no.** Of the 58 per-cycle finding reports in PY-08, at least 14 are re-reports of the same five carried items, and two whole classes (§3 above) are rediscovered from scratch in every BIU. The verifiers are spending cognition on failures AlienIntent already knows about.

### 8. Did lessons from one BIU measurably affect later BIUs?

**FACT — yes, for the control-plane lessons.** PY-07's release-record defect produced `release_admission.py`; PY-08's release comment records those admission checks running and passing before any worker launched, and PY-08 had no release-record authority block. PY-07's liveness defect produced `judgment_suppression`; PY-08's one liveness gap was a genuine missing effect, not a retried judgment outcome.

**FACT — the strongest instance is PY-09's capacity interruption**, where three separate durable rules did work on a condition none of them was written for. A provider quota killed the cycle-4 producer mid-invocation. SWF-29 (from PY-07) **suppressed** liveness recovery instead of re-emitting into the same wall every grace period. SWF-30 (from PY-06) made the worktree holding 65 insertions of partial work required evidence, exempt from cleanup, and the recovery comment told the next producer to read it rather than rebuild from memory. SWF-09 made provider substitution an operator decision rather than a coordinator one, which is what produced the cohort's first genuine human decision. None of those rules mentions provider quotas.

**FACT — propagation is complete for the PY-08 lesson; effectiveness is not demonstrated.** SWF-23 §4b is in PY-09's contract, in its pre-release Agent-Ready assessment, and in its release comment. PY-09 has nonetheless taken three rejections on the same cause, and its producer's first two candidates widened implementation ahead of the harness.

**HYPOTHESIS:** §4b reduces total cycles. **Not supported at this boundary.** What *is* supported is that it changed the verifier's method — a repeated, discriminating negative control from cycle 2 onward — and that PY-09 carries zero regressions across three cycles.

**INFERENCE:** a rule written for a repair loop binds the coordinator and the verifier immediately and reaches the producer only through the rejection it causes. That is a distributional property of the lesson, not a weakness of its content.

**FACT — the factory reached the same conclusion inside the loop.** PY-09's cycle-3 convergence assessment converts the verifier's method into a pre-publication producer obligation: *"for every test you add or rely on, delete or neuter the code it covers and confirm the suite goes red… run that check yourself before publishing the candidate."* The propagation chain therefore has one more link than it did at release. Whether it changes cycle 4 is **UNKNOWN** — the producer that received the direction died on a provider quota before publishing.

### 9. Which lessons remain only documented?

The two engineering-quality classes — *proof that cannot go red* and *a correct object with no executed path* — plus *restart a repair from the rejected candidate, not the baseline* and *drive the command surface as a subprocess against a real composition root*. All four are mechanizable. None is mechanized.

### 10. Which lessons have become gates or invariants?

Release admission (`release_admission.py`, 14 tests, replayed against the incident it came from) and liveness judgment suppression (`judgment_suppression`, 8 tests). Both are bootstrap-level and explicitly temporary, with canonical owners named (SF-REQ-002 and SF-REQ-056).

## Two readings that the evidence does not support

**"Quality is improving because regressions fell from PY-08 to PY-09."** PY-09 is three cycles into an unfinished BIU with a narrower contract and LOW locality. PY-05 and PY-06 also had zero regressions. The comparison is not like for like.

**"PY-08 was too big and should have been split."** The coordinator referred exactly that question to the Founder and then answered it from evidence: one verification-only cycle closed both never-attempted obligations, both regressions, and introduced nothing. The sequencing was wrong, not the size — and wrong sequencing imitates wrong decomposition.

## What is not measured anywhere in this cohort

Model identity per invocation. Token usage per cycle. Monetary cost, per cycle or end to end. Per-finding discovery cost. Defects escaping one BIU into a later one. All are **UNKNOWN**, in every row, for every BIU. They belong to the canonical factory-yield capability in SF-REQ-024; none was collected during Wave 1 under SWF-18.

**Provider adapter identity is known for exactly one BIU, and only because it failed.** PY-09's capacity incident records the PRODUCER on `codex` under provider-default funding and the VERIFIER on `claude` under a separate subscription. The dispatcher state record carries no provider field, so the same assignment in PY-05–PY-08 is an inference and stays UNKNOWN there. That is worth noticing on its own: the factory learned which provider ran its producers by running one out of quota. The token count that would have made the exhaustion predictable is itself UNKNOWN.
