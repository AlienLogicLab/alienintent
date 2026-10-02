# Shortest path to a self-building Python factory

**Decision, 2026-09-29:** The first milestone is a Python AlienIntent factory that can continue building AlienIntent. The hand-fed period uses separate PRODUCER, REVIEWER and CLOSURE instances, independent review and distinct closure. Model assignments come from one authoritative runtime source. Only after those bounded improvements does Python take control of the full work cycle.

## What exists

The Python tree already contains a coordinator, durable state, real GitHub queue and worker adapters, a sandbox run profile, release checks and health probes. The prior Python sandbox proof completed six seeded tasks with automatic refill and restart. The preparation and live queue paths are separate. The first [bounded code task](../work-units/python/PY-SELF-00.md) binds the task text and contract to the retained assessment; a following task saves those exact bytes at a fixed repository version; the [reader task](../work-units/python/PY-SELF-01R.md) and [queue handoff](../work-units/python/PY-SELF-01.md) follow. Independent review identified the reader and authorization gaps in the original combined handoff. An earlier, less detailed version received an Agent Ready READY assessment. Independent review found the revised design unready for Founder approval or a new assessment; no PRODUCER has been released. Later work must close quality, independent closure and resource-cleanup gaps before claiming self-building.

## Minimum build sequence

| Step | Work | Done when |
|---|---|---|
| 0. Bind assessed work | Complete the bounded [first packet](../work-units/python/PY-SELF-00.md): prove the current contract and task text match the latest retained assessment. Then save those exact bytes in a reviewed repository commit and make the reader honor that version. | The publication path cannot silently substitute changed or unassessed instructions. |
| 1. Hand-feed bounded work | The Founder reviews each detailed design, then Agent Ready assesses its exact text. A PRODUCER implements in its own temporary directory; a distinct REVIEWER checks in another; a different CLOSURE instance owns closure. | The review, landing, outcome and completed-state evidence trace to the exact same accepted revision; temporary resources have an owner and cleanup rule. |
| 2. Join preparation to execution | Reuse Python's existing preparation and runner paths; complete the assessed handoff work unit, then the remaining real requirement and quality-gate units. | An authorized AlienIntent requirement becomes assessed ready work without manual copying or lane edits, and wrong or unsupported work cannot pass. |
| 3. Prove the factory can build itself | Python runs a real AlienIntent change through independent review, landing, outcome proof, restart and automatic next-work selection. | The full path succeeds with one writer and no manual message relay; failure becomes an honest, recoverable block. |
| 4. Clean up | Apply bounded cleanup to each new temporary object. Inventory old directories and branches against claims and retained evidence before any removal. | New work leaves no unowned temporary resources; older leftovers are classified and safely resolved with before/after receipts. |

These steps are a plan, not Issue numbers. The first handoff design failed independent review and must be completed or split before Founder review and reassessment. Design and assess the following units separately. Reuse existing Python code and keep one implementation unit in progress at a time.

## First-milestone acceptance

Start with an authorized AlienIntent requirement, have Python prepare its assessed work and complete a real change to this codebase. A separate review and closure path must prove the exact published revision and actual product behavior. Kill and restart Python at a worker or external-effect boundary; it must recover and take the next eligible item without manual lane edits. Retain source, assessment, revision, review, landing, outcome, claim, effect and cleanup receipts. A completed label alone is insufficient.

The minimum slop gate is mandatory now: conserve requirements through the BIU, reject an unauthorized or duplicate design, verify independently against exact code, refuse fabricated proof, preserve prior behavior during repair and test the landed outcome. Broader REST/MCP interfaces, multiple projects, parallel WIP, dashboards, adaptive Director cognition and a clean-room rewrite are outside this first milestone.

**Next action:** review the bounded [first packet](../work-units/python/PY-SELF-00.md), drawn from the agreed sequence. After design acceptance, obtain a fresh Agent Ready assessment of its exact text. Design the repository publication step, then continue through the [reader](../work-units/python/PY-SELF-01R.md) and [queue handoff](../work-units/python/PY-SELF-01.md) packets in dependency order. Release only a newly approved and assessed packet against a fixed starting version. A PRODUCER implements, a distinct REVIEWER checks, and a different CLOSURE instance closes only the accepted revision. Follow the [hand-fed build and cleanup plan](manual-python-build-handoff.md).

Stopping Node for the hand-fed build period is an operational pause. Formal retirement remains a separate proof: liveness, observation, admission, attention, aliases and launch duties need Python successor readbacks. A successful self-building run alone does not declare them retired.

Sources: `docs/architecture/alienintent-factory-v2-formal-design.md`, `docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`, `docs/evidence/wave2-dependency-dag.json`, and the companion agent-slop problem/gap documents. Prior Project/runtime observations are snapshots; refresh custody before a live claim.
