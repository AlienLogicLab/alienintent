# Wave 1 closure policy — SWF-16 through SWF-20

Date: 2026-09-20. Status: **Founder decision — binding**.
Source: direct Founder instruction resolving the PY-02 post-ACCEPT authority exception ([issue #50](https://github.com/AlienLogicLab/alienintent/issues/50)).
Predecessors: [SWF-01–07](2026-09-19-software-factory-wave1-founder-decisions.md), [SWF-08–11](2026-09-20-wave1-plan-approval-d1-d2.md), [SWF-12–15](2026-09-20-wave1-execution-decisions.md).

## SWF-16 — PY-02 landing authorized

Landing of the accepted PY-02 candidate `8689771b9fccb9f86c7fdcc2e9d4f571408765f2` (branch `b-disp/dd26bda4-rework`) into `main` is authorized, using a **normal merge commit**.

Prohibited: rebase; squash; rewriting the accepted SHA; modifying accepted candidate content. The accepted SHA must remain reachable in `main` ancestry.

After landing: run only the required post-merge checks, confirm required CI on the merge result, complete closure, and transition PY-02 to DONE.

If the merge unexpectedly changes candidate content or constitutes a material implementation change, stop and `RETURN_TO_IMPLEMENT`.

## SWF-17 — Standing ACCEPT → DONE policy

Applies to PY-02 and future Wave 1 BIUs unless a BIU explicitly requires different closure actions.

After ACCEPT, the closure worker performs **only the minimum remaining actions required to reach DONE**, evaluating this explicit checklist:

- landing required?
- deployment required?
- publication/release required?
- live verification required?
- other BIU-specific closure action required?

For each item:

| Case | Action |
|---|---|
| **A** already satisfied | record durable evidence and continue |
| **B** required, incomplete, already authorized | perform only that action |
| **C** not required | record the reason and continue |
| **D** required but missing authority | emit `FOUNDER_EXCEPTION` and stop |
| **E** requires material implementation change | `RETURN_TO_IMPLEMENT` and require normal VERIFY again |

Closure **must not** perform: opportunistic refactoring; unrelated cleanup; speculative abstraction; unrelated documentation work; unrelated tests; architecture redesign; additional feature work; or repeated verification already supported by trusted accepted evidence, unless the closure contract explicitly requires it.

> **Objective: the minimum necessary closure work required to transform an accepted candidate into an operationally complete DONE BIU.**

## SWF-18 — Closure-efficiency measurement

Record closure-efficiency evidence wherever current infrastructure allows, without delaying Wave 1:

- closure start/end time;
- actions evaluated;
- actions performed;
- actions determined unnecessary;
- tool/command count if available;
- changed files;
- token/cost data if available;
- authority interruptions;
- time blocked awaiting human authority;
- `RETURN_TO_IMPLEMENT` occurrences.

**Do not build a new telemetry subsystem during Wave 1 merely to collect this.** Preserve available evidence now; formal factory-yield instrumentation (SF-REQ-024) comes later.

## SWF-19 — Contract normalization: default source-control closure policy

Wave 1 BIU contracts state their required closure actions explicitly, so a landing question covered by this policy never requires another Founder exception.

Default policy for an accepted Git-backed implementation candidate: **if** landing is required and repository policy permits it, **and** landing does not alter accepted candidate content, **and** no stronger BIU-specific policy applies, **then** a normal merge preserving the accepted candidate SHA is authorized as routine closure.

Merge is **not** a lifecycle state. Landing is a closure operation.

## SWF-20 — Minimum necessary work invariant (cross-lifecycle requirement)

Recorded as a cross-lifecycle AlienIntent requirement, **SF-REQ-048**:

> At IMPLEMENT, VERIFY, REVIEW, ACCEPT and closure-to-DONE, agents perform only the work necessary to satisfy the BIU, current lifecycle obligations, applicable architecture/policy, and required evidence.

- Where mechanically detectable, over-scope work should fail verification.
- Where judgment is required, REVIEW/ACCEPT explicitly assesses unnecessary work, unnecessary abstraction, scope expansion, and whether a simpler correct implementation was available.

Priority and wave assignment for SF-REQ-048 remain Founder input and are not assumed here.
