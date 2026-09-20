# Persistent Control Plane with Bounded Coordinator Episodes — SWF-27

Date: 2026-09-20. Status: **Founder decision — binding workflow/architecture semantics**.
Source: [PROP-2026-0003](../proposals/PROP-2026-0003-persistent-control-plane-bounded-coordinator-episodes.md), submitted by the Founder 2026-09-20 (`authority_level: founder`, `proposal_type: workflow_architecture`).
Canonical requirement: **SF-REQ-053**.

**Founder assignment (2026-09-20):** Priority **P0**; Wave **2**. This
assignment does not create a BIU or authorize implementation.

## Principle

> **Durable project cognition + durable authority + durable evidence + replaceable model reasoning.**

The lifetime of the control plane is separated from the lifetime of model-based coordinator reasoning. The deterministic control plane may live continuously; model-based coordination has **bounded tenure**.

## Durable rules

1. **Persistent control plane, bounded cognition.** A model-based coordinator is never an immortal authoritative mind. Its invocation may persist across a bounded episode to preserve useful continuity, but tenure ends according to explicit policy.
2. **The episode is the default unit of coordinator tenure.** A typical engineering episode corresponds to **one BIU** from release through its terminal outcome, including repair and verification cycles. This is a default policy, not a permanent invariant.
3. **Conversation is working memory, never authority.** Anything required for correct continuation after coordinator replacement must exist in durable project-owned state — requirements, decisions, Design Contracts, BIUs, HumanDecision records, Project Cognition, Execution Trajectory, Quality Evidence, operational state, evidence objects. A new coordinator must not need the prior conversation to determine what work is authorized.
4. **Useful continuity is intentional.** One fresh invocation per event is not required merely to avoid context risk; continuity has real value for recognizing convergence versus thrashing, BIU trajectory, verifier-finding context, recurring failure classes and short-term plan coherence.
5. **Tenure is policy, not hard-coded architecture.** Tenure policy changes without changing domain semantics or authoritative state.
6. **Tenure remains bounded.** Renewal/termination conditions include terminal outcome, material change of objective or governing/architecture authority, context budget, accumulated contradictions, staleness relative to authoritative state, age or transition budget, prolonged blocking, provider/model replacement, or explicit authority request. Thresholds are design decisions.
7. **Episode boundaries require durable continuity.** A successor reconstructs context from authoritative state and Project Cognition, never from inherited conversational assumptions.
8. **Restart equivalence is a target property.** Given the same durable authoritative state and external events, replacing the coordinator must not materially change what work is authorized or what lifecycle state exists.
9. **Long-lived sessions must not become hidden state stores.** If killing the coordinator would make correct continuation impossible, required state has not been made durable.
10. **Temporary coordinator controls remain explicit exceptions**, carrying defined scope, authority basis, expiration condition, durable provenance and a replacement target. **Temporary coordinator behaviour must not silently become architecture through continued use.**

## Architectural separation

The deterministic control plane owns lifecycle state, WIP and reservations, dependency eligibility, event correlation, idempotency, invocation identity, candidate identity, effect intent/outbox, authority checks, recovery/reconciliation and decisions already made.

The model-based coordinator handles judgment: proposal classification, design reasoning, ambiguity diagnosis, convergence diagnosis, non-mechanical review, identifying authority gaps, proposing new rules or controls. Exact boundaries remain subject to design verification (SF-REQ-051).

A coordinator episode operates on explicitly assembled context — bounded objective, authoritative objects, governing decisions, relevant Project Cognition, lifecycle state, evidence, permitted and prohibited actions, unresolved questions, budget, and the current authoritative-state version.

**Staleness protection:** a stale coordinator result must never silently overwrite newer authoritative state. State versions, optimistic concurrency, leases or epochs are candidate mechanisms; the choice is design work.

## Relationship to existing authority

- **SF-REQ-009 deterministic kernel** (#11) — "no LLM owns canonical execution state" is the same principle applied to execution; this extends it to coordinator tenure and replaceability.
- **SF-REQ-008 crash-safe execution** (#10) — process crash recovery; restart *equivalence* across coordinator replacement is a distinct property built on the same durable state.
- **SF-REQ-034 Operator Control Plane** (#13) — the persistent surface whose lifetime this separates from model reasoning.
- **Plan §Deterministic kernel** — "Intelligence proposes; deterministic policy disposes."
- **SWF-21 / SWF-26** — rule 10 is already practised: SWF-21 is explicitly temporary and expiring, and SWF-26 was expired at PY-04 DONE rather than allowed to become architecture.
- **SF-REQ-051 Design Contract and Design Verification** (#62) — the boundary between deterministic and judgment work is design-verified, not assumed.

## Bootstrap evidence — monitoring decoupled from coordinator tenure (2026-09-20)

Rule 9 says no model session may be the sole durable holder of information required for safe continuation. A weaker form of the same coupling was found in the bootstrap itself: the liveness watch and the lifecycle watchers ran as **child processes of the Claude coordinator session**, and their scripts lived in that session's scratch directory. Ending the episode would have stopped monitoring and deleted the monitors. That made the episode model in rule 2 unexercisable — the coordinator could not end an episode without degrading the factory.

Two durable statements follow, and are recorded here as binding bootstrap interpretation of this decision:

> **Persistent monitoring is operational infrastructure and must not determine the tenure of a model-based coordinator episode.**

> **A coordinator episode may end while deterministic monitoring continues.**

Applied: deterministic monitoring moved to `systemd --user` (`alienintent-liveness.service`, `alienintent-observer.service`), parented by the user manager rather than any Claude session, single-instance via `flock`, writing durable observations a successor reconstructs state from. Model judgment was **not** moved into a daemon: the observer takes no decision and performs no recovery, and the liveness watch acts only under the already-authorized SWF-29 rule. See `docs/operations.md`.

This is bootstrap evidence for SF-REQ-053, not a new requirement: the existing authority already contains it.

## Scope and non-goals

No change to the current Wave 1 coordinator, worker or verifier behaviour, and no change to Node/B-DISP bootstrap behaviour. No coordinator-lifecycle experiment is started. No visible lifecycle state is created — existing authority does not require one. No fixed context-size or time thresholds are selected. No implementation, and no BIU is created from this record.
