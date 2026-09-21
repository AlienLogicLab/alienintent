---
proposal_id: PROP-2026-0008
title: BIU Execution Cycle Counter — canonical cycle identity and Work Management projection
submitted_by: founder
submitted_at: 2026-09-21
proposal_type: workflow_semantics
authority_level: unresolved
status: submitted
---

# BIU Execution Cycle Counter

## Intent

Make the current implementation/verification cycle of a released BIU a first-class AlienIntent execution fact, so operators can see convergence progress directly on the Work Management surface and execution evidence can distinguish repair cycles from worker invocation attempts.

## Motivating evidence

Wave 1 has shown that **BIU repair cycle** and **worker invocation attempt** are different concepts.

The intended lifecycle shape is:

```text
READY
  -> IMPLEMENT   Cycle 1
  -> VERIFY      Cycle 1
  -> IMPLEMENT   Cycle 2
  -> VERIFY      Cycle 2
  -> ...
```

Each authoritative transition back into `IMPLEMENT` represents another implementation/verification cycle.

PY-09 exposed why the counter cannot be derived from invocation count. During cycle 4, its PRODUCER invocation was interrupted by provider-capacity exhaustion. The partial work was preserved and the same cycle resumed under another provider. That recovery created another PRODUCER invocation but did **not** create another verifier rejection or another repair cycle.

Without a canonical cycle identity, trajectory, operator visibility and convergence metrics can incorrectly conflate:

- repair cycles;
- producer retries/restarts;
- provider failover;
- liveness recovery;
- duplicate/replayed delivery;
- verifier restarts.

The current GitHub Project board visualizes lifecycle state but does not show the current cycle number.

## Proposed rule

AlienIntent maintains a canonical **execution cycle number** for every released BIU.

1. The first authoritative transition into `IMPLEMENT` establishes `cycle = 1`.
2. Every subsequent authoritative transition into `IMPLEMENT` from a different lifecycle state increments the cycle by exactly one.
3. `VERIFY` inherits the current cycle number; entering VERIFY does not increment it.
4. `ACCEPT`, `DONE` and other lifecycle states retain the current cycle value for history/evidence but do not increment it.
5. An authorized transition such as `ACCEPT -> IMPLEMENT` for material rework increments the cycle because it begins another implementation/verification pass.
6. Re-entry, retry or replacement **within the same IMPLEMENT phase** does not increment the cycle.
7. Duplicate/replayed delivery of the same authoritative transition must not increment the cycle twice.
8. Restart/replay/reconciliation must reconstruct or preserve the same canonical cycle deterministically.
9. Worker invocation attempts remain separately identifiable. Cycle number must never be inferred from invocation count.

Conceptually:

```text
BIU
  Cycle 1
    Producer invocation(s)
    Verifier invocation(s)

  Cycle 2
    Producer invocation(s)
    Verifier invocation(s)
```

## Work Management projection

AlienIntent owns the canonical cycle after release.

The configured Work Management Provider, including GitHub Projects, receives the cycle as a projection for operator visibility.

For GitHub Projects, the intended presentation is a numeric field such as:

```text
Cycle = 4
```

so a board can show:

```text
PY-09   IMPLEMENT   Cycle 4
PY-10   VERIFY      Cycle 2
```

The Work Management field is a projection only. Editing the projected value externally must not become execution authority or independently change AlienIntent's canonical cycle.

## Cycle is evidence, not verdict

A high cycle number is an operational/convergence signal, not proof that:

- the BIU is badly decomposed;
- the producer is failing;
- the verifier is unreasonable;
- the work should be split;
- a Founder decision is required.

Wave 1 has already shown that multiple cycles may result from proof sequencing, newly exposed masked defects, provider interruptions, or other causes.

Attention or convergence policy may use cycle thresholds, but such policy is separate from the meaning of the counter itself.

## Acceptance semantics if approved

The capability should eventually prove at least:

1. `READY -> IMPLEMENT` produces cycle 1.
2. `IMPLEMENT -> VERIFY` remains cycle 1.
3. `VERIFY -> IMPLEMENT` produces cycle 2.
4. the following `IMPLEMENT -> VERIFY` remains cycle 2.
5. duplicate/replayed handling of one `VERIFY -> IMPLEMENT` transition does not increment twice.
6. producer crash/restart within IMPLEMENT does not increment.
7. provider failover within IMPLEMENT does not increment.
8. liveness recovery that resumes the same lifecycle phase does not increment.
9. `ACCEPT -> IMPLEMENT` for authorized material rework increments.
10. restart/replay/reconciliation preserves the same cycle.
11. Engineering Trajectory can associate findings and invocations with the correct cycle.
12. GitHub Project projection reflects canonical AlienIntent state and cannot become an independent authority.

## What the rule does not do

- It does not create a new lifecycle state.
- It does not change the meaning of IMPLEMENT, VERIFY, REVIEW, ACCEPT or DONE.
- It does not define retry policy.
- It does not define convergence thresholds or when a BIU should be split.
- It does not count worker invocations as cycles.
- It does not make GitHub Project state canonical after release.
- It does not modify the current Wave 1 Node bootstrap unless separately authorized.
- It does not assign Priority or Wave.
- It does not create a BIU or authorize implementation.

## Relationship to existing authority

Proposal Intake should determine the smallest canonical owner rather than creating duplicate authority.

Likely related existing owners include:

- **FD-01 / Work Management and Execution authority boundary** — AlienIntent owns execution-control state after explicit release; Work Management receives projections.
- **SF-REQ-029 Engineering Trajectory** — cycle identity is useful execution trajectory context.
- **SF-REQ-024 Factory yield metrics** — repair/rework cycles are already a factory-yield concern.
- **SF-REQ-034 Operator Control Plane** — cycle should be visible in status/explain/operator surfaces.
- **SF-REQ-049 Convergent Repair / Monotonic Progress** — cycle identity provides stable context for repair history.
- **SF-REQ-052 Convergence Assistance / Distance-to-Done Optimization** — may consume cycle count as evidence but should not own the underlying identity.
- **SF-REQ-009 Deterministic execution kernel** — canonical lifecycle-derived cycle state must be deterministic and replay-safe.

A new Product Requirement is **not presumed**. If one existing requirement cleanly owns canonical execution-cycle identity and projection, prefer amendment. If no existing requirement can own the capability without semantic distortion, Proposal Intake may create a new requirement.

## Application if approved

Do not retrofit or disturb live Wave 1 execution merely to display the field.

The canonical Python design should:

- represent cycle as durable execution state;
- update it atomically/idempotently with authoritative lifecycle transition handling;
- expose it in Engineering Trajectory and operator status;
- project it to configured Work Management providers;
- preserve cycle across restart/replay/reconciliation;
- keep invocation attempts separately identifiable.

Any GitHub Project field should be added only when the canonical state and projection semantics are designed/implemented, not as an independently maintained manual counter.

## Open question for the Founder

Should AlienIntent make the BIU execution cycle a canonical execution-domain fact, incremented on each authoritative transition into `IMPLEMENT`, inherited through `VERIFY`, and projected to the Work Management surface for operator visibility and convergence evidence, while keeping worker invocation attempts as a separate concept?
