# Shortest path to a self-building Python factory

**Decision, 2026-09-29:** The first milestone is a Python AlienIntent factory that can continue building AlienIntent. Issue 125 finishes under Node first. The separate shutdown owner then stops Node and its managed services; Claude and Codex work through the [hand-fed build period](manual-python-build-handoff.md) with separate working directories, independent review and a distinct closure step. Only after those bounded improvements does Python take control of the full work cycle.

## What exists

The Python tree already contains a coordinator, durable state, real GitHub queue and worker adapters, a sandbox run profile, release checks and health probes. The prior Python sandbox proof completed six seeded tasks with automatic refill and restart. The first missing connection is between Python's preparation and assessment path and the existing live queue; [the first candidate work unit](../work-units/python/PY-SELF-01.md) defines that handoff and has an Agent Ready READY result. It has not been released to Claude. Later work must close quality, independent closure and resource-cleanup gaps before claiming self-building.

## Minimum build sequence

| Step | Work | Done when |
|---|---|---|
| 0. Finish the old run | Let issue 125 reach real completion; read back claims, effects and candidate custody. The shutdown owner stops Node and its managed services. | No competing factory writer or unexamined effect remains. |
| 1. Hand-feed bounded work | Agent Ready assesses each exact small work unit. Claude implements in its own temporary working directory; Codex reviews the published revision in another; a separate closure process lands accepted work, proves the outcome and marks it complete. | The review and closure evidence can be traced to the exact same revision; temporary resources have an owner and cleanup rule. |
| 2. Join preparation to execution | Reuse Python's existing preparation and runner paths; complete the assessed handoff work unit, then the remaining real requirement and quality-gate units. | An authorized AlienIntent requirement becomes assessed ready work without manual copying or lane edits, and wrong or unsupported work cannot pass. |
| 3. Prove the factory can build itself | Python runs a real AlienIntent change through independent review, landing, outcome proof, restart and automatic next-work selection. | The full path succeeds with one writer and no manual message relay; failure becomes an honest, recoverable block. |
| 4. Clean up | Apply bounded cleanup to each new temporary object. Inventory old directories and branches against claims and retained evidence before any removal. | New work leaves no unowned temporary resources; older leftovers are classified and safely resolved with before/after receipts. |

These steps are a plan, not Issue numbers. The first handoff work unit has passed Agent Ready but has not been released. Assess the following units separately. Reuse existing Python code and keep one implementation unit in progress at a time.

## First-milestone acceptance

Start with an authorized AlienIntent requirement, have Python prepare its assessed work and complete a real change to this codebase. A separate review and closure path must prove the exact published revision and actual product behavior. Kill and restart Python at a worker or external-effect boundary; it must recover and take the next eligible item without manual lane edits. Retain source, assessment, revision, review, landing, outcome, claim, effect and cleanup receipts. A completed label alone is insufficient.

The minimum slop gate is mandatory now: conserve requirements through the BIU, reject an unauthorized or duplicate design, verify independently against exact code, refuse fabricated proof, preserve prior behavior during repair and test the landed outcome. Broader REST/MCP interfaces, multiple projects, parallel WIP, dashboards, adaptive Director cognition and a clean-room rewrite are outside this first milestone.

**Next action:** after issue 125 and the separately owned shutdown are read back, release the assessed [first handoff work unit](../work-units/python/PY-SELF-01.md) against a pinned baseline. Claude uses a separate working directory, Codex reviews independently, and a separate closure owner lands only the accepted revision. Follow the [hand-fed build and cleanup plan](manual-python-build-handoff.md).

Stopping Node for the hand-fed build period is an operational pause. Formal retirement remains a separate proof: liveness, observation, admission, attention, aliases and launch duties need Python successor readbacks. A successful self-building run alone does not declare them retired.

Sources: `docs/architecture/alienintent-factory-v2-formal-design.md`, `docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`, `docs/evidence/wave2-dependency-dag.json`, and the companion agent-slop problem/gap documents. Prior Project/runtime observations are snapshots; refresh custody before a live claim.
