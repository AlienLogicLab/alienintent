---
proposal_id: PROP-2026-0003
title: Persistent Control Plane with Bounded Coordinator Episodes
submitted_by: founder
submitted_at: 2026-09-20
proposal_type: workflow_architecture
authority_level: founder
status: submitted
---

# Persistent Control Plane with Bounded Coordinator Episodes

## Intent

AlienIntent should separate the lifetime of the control plane from the lifetime of model-based coordinator reasoning.

The control plane may be continuously available and durable.

Model-based coordinator/director reasoning must have bounded tenure.

The natural default unit of model-based coordination is an **episode**, not an individual event and not an indefinitely persistent model session.

## Durable principles

### 1. Persistent control plane, bounded cognition

AlienIntent's deterministic control plane may live continuously.

A model-based coordinator/director must not be treated as an immortal authoritative mind.

The model invocation may persist across a bounded work episode to preserve useful cognitive continuity, but its tenure must end according to explicit policy.

### 2. Episode is the default unit of coordinator tenure

The default coordinator tenure should be scoped to a bounded episode.

A typical engineering episode is expected to correspond to one BIU from release through its terminal outcome, including repair and verification cycles where continuity is useful.

Conceptually:

```text
Episode starts
    ↓
IMPLEMENT
    ↓
VERIFY
    ↓
repair / re-VERIFY cycles
    ↓
REVIEW
    ↓
ACCEPT / closure
    ↓
DONE
Episode ends
```

This is a default policy, not a permanent invariant that every future model or task must use.

### 3. Conversation is working memory, not authority

A coordinator conversation may be used as temporary working memory during an episode.

Conversation state is never authoritative project state.

Any information required for correct continuation after coordinator replacement must exist in durable project-owned state, such as:

- requirements;
- decisions;
- Design Contracts;
- BIUs;
- HumanDecision records;
- Project Cognition;
- Execution Trajectory;
- Quality Evidence;
- operational state;
- evidence objects;
- other canonical project artifacts.

A new coordinator must not require access to the prior model conversation in order to determine what work is authorized.

### 4. Useful continuity is intentional

AlienIntent should not force one fresh model invocation per event merely to avoid context risk.

Useful cognitive continuity has value, including:

- recognizing convergence versus thrashing;
- understanding the trajectory of a BIU;
- retaining the immediate reasoning context of verifier findings;
- avoiding repeated context reconstruction;
- recognizing recurring failure classes;
- maintaining a coherent short-term plan across related lifecycle events.

Coordinator lifecycle policy should preserve this value where the associated risk remains bounded.

### 5. Coordinator tenure is policy, not hard-coded architecture

The optimal coordinator tenure may change as models improve.

AlienIntent must therefore treat coordinator tenure as configurable policy rather than permanently hard-coding:

- one event per coordinator;
- one BIU per coordinator;
- one session forever;
- a specific time limit.

The architecture must support changing the tenure policy without changing domain semantics or authoritative project state.

### 6. Coordinator tenure must remain bounded

Even when an episode spans multiple lifecycle transitions, coordinator tenure must have explicit bounds.

Candidate renewal/termination conditions include:

- episode reaches a terminal outcome;
- bounded objective changes materially;
- governing authority changes materially;
- architecture authority changes materially;
- context exceeds a configured budget;
- unresolved contradictions accumulate;
- coordinator state becomes stale relative to authoritative project state;
- maximum age or meaningful-transition budget is exceeded;
- prolonged blocking or inactivity;
- provider/model replacement;
- explicit authority requests a restart.

The final policy and thresholds are implementation/design decisions.

### 7. Episode boundaries require durable continuity

When a coordinator episode ends, any information needed by a successor must already be durable or be durably checkpointed before termination.

The successor should reconstruct its working context from authoritative project state and Project Cognition rather than inheriting hidden conversational assumptions.

### 8. Restart equivalence is a target property

AlienIntent should be designed so that replacing the model-based coordinator at an episode boundary does not change the authority or safety envelope of the project.

A new coordinator may reason differently or make better proposals.

It must not gain or lose authority merely because conversational state changed.

A useful target property is:

> Given the same durable authoritative state and applicable external events, replacing the coordinator must not materially change what work is authorized or what lifecycle state exists.

### 9. Long-lived model sessions must not become hidden state stores

No model session may become the sole durable holder of:

- authority;
- lifecycle state;
- project decisions;
- required context;
- candidate identity;
- pending obligations;
- accepted evidence;
- release policy;
- temporary-control expiry;
- other information required for safe continuation.

If killing the coordinator would make correct continuation impossible, required state has not been made durable.

### 10. Temporary coordinator controls remain explicit exceptions

A coordinator may operate temporary bootstrap controls only when explicitly authorized.

Such controls must have:

- defined scope;
- authority basis;
- expiration condition;
- durable provenance;
- replacement target where applicable.

Temporary coordinator behavior must not silently become architecture through continued use.

## Architectural separation

The intended architecture separates a durable deterministic coordinator/control-plane kernel from bounded model reasoning.

Conceptually:

```text
Durable authoritative project state
              │
              ▼
    Deterministic control plane
              │
       judgment required
              ▼
    Coordinator episode
    bounded model reasoning
              │
       structured result
              ▼
 deterministic authority/
    consistency checks
              │
              ▼
       durable effect
```

The control plane owns deterministic concerns such as:

- lifecycle state;
- WIP and reservations;
- dependency eligibility;
- event correlation;
- idempotency;
- invocation identity;
- candidate identity;
- effect intent/outbox;
- authority checks;
- recovery/reconciliation;
- durable decisions already made.

The model-based coordinator handles work requiring judgment, such as:

- proposal classification;
- design reasoning;
- ambiguity diagnosis;
- convergence diagnosis;
- non-mechanical review;
- identifying authority gaps;
- proposing new rules or controls.

Exact boundaries remain subject to design verification.

## Coordinator episode context

A coordinator episode should operate on explicitly assembled context rather than relying on unbounded session history.

Candidate episode inputs include:

- bounded objective;
- authoritative objects;
- governing decisions;
- relevant Project Cognition;
- current lifecycle state;
- evidence;
- permitted actions;
- prohibited actions;
- unresolved questions;
- budget;
- current authoritative-state version.

The exact contract is a design concern.

## Staleness and state-version protection

A coordinator may reason for long enough that project state changes during its episode.

AlienIntent should therefore support detecting when a proposed effect was derived from stale authoritative state.

A future design may use state versions, optimistic concurrency, leases, epochs, or equivalent mechanisms.

A stale coordinator result must not silently overwrite newer authoritative state.

## Relationship to Project Cognition

Project Cognition exists partly to make coordinator instances replaceable.

The persistent intelligence belongs to the project, not to a particular provider session.

The architectural objective is:

> durable project cognition + durable authority + durable evidence + replaceable model reasoning.

## Relationship to model maturity

Coordinator-tenure policy should be expected to evolve as model capabilities change.

Relevant future factors may include:

- long-context fidelity;
- context-reconstruction cost;
- retrieval quality;
- self-detection of stale assumptions;
- consistency across long-running reasoning;
- provider cost and latency;
- reliability of structured reasoning.

Changes in model capability may justify shorter or longer episodes without changing the core architecture.

## Initial default policy

The initial design target should use:

> **one bounded work episode, usually one BIU**

as the default coordinator tenure.

This is a starting policy, not a permanent architectural invariant.

Exceptions may be justified for other bounded work types such as:

- proposal canonicalization;
- architecture/design work;
- incident response;
- release/closure work;
- research or evidence reconstruction.

## Non-goals

This proposal does not require:

- changing the current Claude coordinator during Wave 1;
- running a new coordinator-lifecycle experiment now;
- terminating a coordinator after every event;
- preserving a coordinator forever;
- selecting fixed context-size or time thresholds now;
- changing existing worker/verifier lifecycle semantics;
- changing Node/B-DISP bootstrap behavior.

## Desired outcome

AlienIntent gains the benefits of short-lived, replaceable model intelligence without discarding valuable cognitive continuity across related work.

The persistent entity is the project and its control plane.

The coordinator is a bounded cognitive participant whose useful tenure is governed by explicit policy and can evolve as model capability matures.
