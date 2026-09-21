# BIU execution cycle counter — SWF-32

Date: 2026-09-21. Status: **Proposal Intake canonicalization**, binding as to ownership and semantics.
Source: [PROP-2026-0008](../proposals/PROP-2026-0008-biu-execution-cycle-counter.md) (`workflow_semantics`,
`authority_level: unresolved`), plus the Founder's stated required semantics of 2026-09-21.

## Classification

Workflow semantics over **execution-domain state**. It creates no lifecycle state, changes no lifecycle
meaning, and authorizes no implementation. It names a fact the execution kernel must already be able to
answer deterministically: *which implementation/verification pass is this BIU on?*

## Canonical owner: SF-REQ-009, by amendment

**SF-REQ-009 — Deterministic execution kernel** reads: *"Lifecycle, policy, reservations, WIP, retries,
capabilities, budgets, candidate identity, and verdict admissibility are deterministic. No LLM owns
canonical execution state."*

The cycle number is lifecycle-derived canonical execution state that must be deterministic, idempotent
under duplicate delivery, and reconstructible after restart. That is the same class as **candidate
identity**, which SF-REQ-009 already owns. No new requirement is created.

### Overlap analysis — why not the others

| Candidate | Relationship |
|---|---|
| **SF-REQ-029 Engineering Trajectory** (P4) | **Consumer.** Trajectory records observations *about* execution; if it owned the counter, evidence would define state instead of describing it. It associates invocations and findings with a cycle it is given. |
| **SF-REQ-024 Factory yield** (P2) | **Consumer.** Already measures "average rework cycles per accepted BIU" — it consumes the count; measuring a thing is not owning it. |
| **SF-REQ-034 Operator Control Plane** | **Consumer.** `status` and `explain` display the cycle. A display surface cannot own execution state. |
| **SF-REQ-049 Convergent repair** | **Consumer.** Uses cycle as stable context for repair history. |
| **SF-REQ-052 Convergence assistance** | **Consumer**, explicitly. Policy may read cycle thresholds; policy must not define the counter. |
| **SF-REQ-005 Work Management abstraction** | Governs reading *upstream* work through a port. The downstream direction is FD-01's, below. |
| **FD-01** | Already settles the projection half: AlienIntent is canonical for execution-control state once a READY BIU is released, and Work Management receives projections. No amendment needed. |
| A new SF-REQ | **Rejected.** It would split "canonical execution state" across two owners — the fragmentation SWF-28 corrected for SF-REQ-030/054. Nothing about the cycle counter distorts SF-REQ-009; it is an instance of what that requirement already says. |

## Canonical semantics

1. The first authoritative transition into `IMPLEMENT` establishes **cycle 1**.
2. `IMPLEMENT → VERIFY` **inherits** the current cycle; entering VERIFY never increments.
3. `VERIFY → IMPLEMENT` increments by **exactly one**.
4. The following `IMPLEMENT → VERIFY` remains at that cycle.
5. Any later authoritative transition into `IMPLEMENT` from another lifecycle state — including an
   authorized `ACCEPT → IMPLEMENT` for material rework — increments by exactly one.
6. Retry, restart, provider failover or a replacement worker **within the same IMPLEMENT phase** does
   not increment.
7. A verifier restart **within the same VERIFY phase** does not increment.
8. Liveness recovery or replay that resumes the same lifecycle state does not increment.
9. Duplicate delivery of one authoritative transition must not increment twice.
10. Restart, replay and reconciliation must preserve or deterministically reconstruct the same cycle.
11. `ACCEPT`, `DONE` and other states retain the current value as history and do not increment.

## Cycle is not invocation count

> **A cycle is a lifecycle fact. An invocation attempt is a worker fact. Neither is derivable from the
> other.**

PY-09's cycle 4 is the worked example, and the reason this proposal exists:

```
PY-09  cycle 4
  PRODUCER e84d12a0  codex   — provider-capacity interruption at 02:12:46Z, partial work preserved
  PRODUCER 9979bdcc  claude  — continuation of the same cycle under an authorized provider change
  VERIFIER …                 — same cycle
```

Two producer invocations, one cycle. There was no verifier rejection between them and no repair pass
began; only the provider changed. A counter derived from invocation count would have read 5 and told
every downstream consumer — operator display, yield metrics, convergence policy — that PY-09 had
repaired one more time than it had. See
[the incident record](../evidence/2026-09-21-py09-provider-capacity-interruption.md).

The inverse error is equally available: a single invocation that crashes and is relaunched inside one
IMPLEMENT phase is still cycle *n*. Invocation attempts remain separately identifiable, and Engineering
Trajectory must be able to represent **BIU → cycle → invocation attempts** as a hierarchy.

## Work Management projection

Direction is fixed by FD-01 and is not negotiable by the adapter:

```
AlienIntent execution state  →  Work Management projection
```

never the reverse. For GitHub Projects the intended presentation is a numeric `Cycle` field, so a board
shows `PY-09 IMPLEMENT Cycle 4`. The field is a **projection only**: editing it externally must not
change canonical state, and must not be readable back as execution authority. The existing projection
mechanism already carries lifecycle state to Project fields, so no new transport concept is required.

**No manually maintained Project counter may be added as a shortcut.** A hand-updated field would be a
second source of truth with no reconciliation, which is precisely the authority inversion FD-01 forbids.
The field is added when canonical state and projection exist to drive it.

## Cycle is evidence, not verdict

A high cycle number does not by itself mean bad decomposition, a failing producer, an unreasonable
verifier, a required split, or a need for Founder intervention. Wave 1 has already produced high counts
from proof sequencing (PY-08), from masked defects surfacing once a crash was fixed (PY-08 cycles 3–4),
and from provider interruption (PY-09). Attention and convergence policy may consume cycle thresholds;
that policy is separate from the meaning of the counter.

## Scope — nothing is retrofitted

This amendment adds no obligation to the live Node bootstrap, changes no released BIU contract, and
alters no current lifecycle state, dispatcher semantics or Project field. PY-09 and PY-10 are untouched.
The capability belongs to canonical Python and is implemented under a future BIU, not by this record.

## Unresolved Founder decision — scheduling

**Priority and Wave are not assigned, and the coordinator may not invent them.**

SF-REQ-009 is P0/Wave 1 and its Wave 1 scope is materially complete. Folding an unbuilt obligation into
it without saying so would imply Wave 1 must deliver the counter — the retrofit ambiguity
[SWF-29](2026-09-20-liveness-reconciliation.md) rejected amendment to avoid. The semantics above are
canonical now; **the implementation obligation carries no wave until the Founder assigns one.** That is
the single open decision from this intake.
