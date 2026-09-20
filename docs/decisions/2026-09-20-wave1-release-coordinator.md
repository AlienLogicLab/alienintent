# Temporary Wave 1 release-coordinator policy — SWF-21

Date: 2026-09-20. Status: **Founder decision — binding, temporary**.
Source: direct Founder instruction.
Predecessors: [SWF-01–07](2026-09-19-software-factory-wave1-founder-decisions.md), [SWF-08–11](2026-09-20-wave1-plan-approval-d1-d2.md), [SWF-12–15](2026-09-20-wave1-execution-decisions.md), [SWF-16–20](2026-09-20-wave1-closure-policy.md).

## Authority granted

Until canonical Python AlienIntent implements automatic READY release, the coordinator session is authorized to fill the Node B-DISP bootstrap gap by performing the READY → IMPLEMENT transition for eligible Wave 1 BIUs.

This is a **temporary orchestration responsibility only**. It is not the target operating model, and it creates no other authority.

## Explicitly not authorized

- implementing a BIU;
- manually launching PRODUCER or VERIFIER workers;
- bypassing Agent-Ready;
- bypassing dependencies;
- inventing priority;
- releasing blocked work;
- exceeding configured WIP/capacity;
- making unresolved Founder/product/architecture decisions.

## Release conditions — all nine must hold

1. Project Status = READY.
2. Agent-Ready disposition = READY.
3. All declared predecessor dependencies are satisfied.
4. No unresolved Founder/product/architecture authority gap exists.
5. No active invocation already exists for that BIU.
6. Current WIP/capacity permits another active work stream.
7. Automatic release policy is ON for the project.
8. The BIU is not explicitly held.
9. No additional authority is required merely to begin IMPLEMENT.

When all hold: move the BIU from READY to IMPLEMENT, launch no worker, and let the Node AlienIntent bootstrap receive the Project event and launch the PRODUCER. Then monitor only for meaningful lifecycle changes or genuine authority blockers.

When a condition fails: leave the BIU in READY or its current state, and report the blocking reason only if it needs human attention.

## Continuous operation

When a BIU reaches DONE, evaluate the next dependency-eligible Wave 1 BIU. Re-run Agent-Ready if its contract or baseline has changed. If it is READY and all nine conditions hold, release it without waiting for the Founder to reconvene.

> **Objective: keep Wave 1 moving continuously through the approved DAG, and interrupt the Founder only for genuinely missing authority.**

## Expiry

This coordinator behaviour remains in effect **only** until Python AlienIntent provides the canonical automatic-release capability (SF-REQ-001/SF-REQ-002 realized through PY-04 and its successors, operating on the live profile). Once Python AlienIntent takes over the responsibility, manual READY → IMPLEMENT transitions stop.
