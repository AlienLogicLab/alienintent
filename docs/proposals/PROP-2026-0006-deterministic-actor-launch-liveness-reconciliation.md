---
proposal_id: PROP-2026-0006
title: Deterministic Actor-Launch Liveness Reconciliation
submitted_by: founder
submitted_at: 2026-09-20
proposal_type: product_requirement
authority_level: founder
status: submitted
requested_priority: P0
requested_wave: 2
---

# Deterministic Actor-Launch Liveness Reconciliation

## Intent

AlienIntent must deterministically detect when a BIU has entered a lifecycle state that requires an actor or effect, but the expected invocation/effect does not appear within a bounded grace period.

The system must recover from that condition without depending on a human or long-lived model coordinator noticing that progress has stopped.

## Motivating incident

During PY-06, the BIU transitioned to `VERIFY` after the producer successfully published its candidate.

The expected VERIFIER invocation was never launched because the triggering webhook delivery did not arrive.

The dispatcher and tunnel remained healthy, the candidate was published and retrievable, and no worker crashed.

The BIU remained in `VERIFY` with no active verifier invocation until the bootstrap coordinator was explicitly asked to inspect it approximately 28 minutes later.

An authorized operator transition regenerated the event and the verifier launched immediately.

This demonstrated a liveness gap:

> Durable lifecycle state required an actor, but no corresponding actor/effect existed and no deterministic mechanism detected the inconsistency.

## Durable principle

> **No nonterminal lifecycle state may depend indefinitely on a single transient event delivery.**

And:

> **When a lifecycle state requires an actor/effect, the expected actor/effect must appear within a bounded grace period or the system must classify and reconcile a liveness failure.**

## Polling distinction

This capability is not backlog/work-discovery polling.

### Prohibited work-discovery polling

Repeatedly querying external Work Management or the backlog to discover whether new actionable work exists.

### Allowed liveness reconciliation

Periodically checking whether already-known durable state that implies an expected actor/effect is consistent with actual invocation/effect state.

Example:

```text
BIU state = VERIFY
expected actor = VERIFIER
matching active/pending invocation = none
matching queued/pending effect = none
grace period exceeded
→ LIVENESS_GAP
```

## Required capability

AlienIntent must be able to define, for applicable lifecycle states:

- expected actor or effect;
- correlation identity;
- state-entry time or equivalent durable age;
- grace period;
- active/pending/completed invocation/effect evidence;
- reconciliation action;
- reconciliation outcome.

Initial examples include:

- `IMPLEMENT` → PRODUCER invocation expected;
- `VERIFY` → VERIFIER invocation expected;
- `ACCEPT` → required closure action expected, where applicable.

The exact lifecycle-to-actor mapping is a design concern.

## Liveness detection

For an active BIU whose current state requires an actor/effect:

1. determine the expected actor/effect;
2. determine whether a matching active invocation exists;
3. determine whether a matching pending claim/effect/outbox item exists;
4. determine whether a correlated completion already exists but projection is lagging;
5. if any valid matching evidence exists, do not recover;
6. if none exists and the grace period has not elapsed, wait;
7. if none exists and the grace period has elapsed, record `LIVENESS_GAP`;
8. reconcile through the narrowest idempotent authorized mechanism.

## Duplicate prevention

The liveness mechanism must not create duplicate worker/verifier invocations.

Before recovery it must check applicable durable evidence such as:

- active invocation;
- active reservation/claim;
- pending effect/outbox entry;
- recently completed correlated invocation;
- recorded delivery awaiting projection;
- other canonical effect identity.

Recovery must be idempotent or fenced by durable correlation/effect identity.

## Recovery

A liveness gap may be recovered by re-emitting/reconciling the expected effect through a canonical mechanism.

The implementation must not depend on lifecycle-status toggling as the permanent recovery design.

Bootstrap operator status transitions are evidence of the required outcome, not the canonical Python mechanism.

## Grace period

The grace period must be configurable.

Initial operational evidence from PY-06 supports a short bounded interval rather than indefinite waiting.

The bootstrap coordinator will initially use **5 minutes**.

The canonical Python implementation may later tune the default based on measured delivery latency and false-positive evidence.

## Evidence and observability

Each detected liveness gap should record:

- BIU/work identity;
- lifecycle state;
- expected actor/effect;
- correlation/effect identity if available;
- state-entry time;
- grace period;
- evidence checked;
- missing effect/invocation;
- recovery action;
- recovery result;
- duplicate-prevention evidence;
- timestamps/duration.

## Relationship to existing requirements

This proposal strengthens continuous execution and recovery semantics, especially:

- SF-REQ-001 Continuous factory execution;
- SF-REQ-008 restart/recovery;
- event-driven/no-polling architecture authority;
- durable effects/idempotency/reconciliation mechanisms.

Proposal Intake should determine whether this becomes:
- a new Product Requirement; or
- an amendment to existing continuous-execution/recovery requirements.

Do not duplicate existing authority if amendment is sufficient.

## Acceptance criteria

1. If a BIU enters `VERIFY` and no corresponding VERIFIER invocation/effect exists after the configured grace period, AlienIntent detects the inconsistency without human/model prompting.
2. The same detection works for other configured lifecycle states that require an actor/effect.
3. A pending or active correctly correlated invocation prevents recovery from creating a duplicate.
4. A pending durable effect/outbox entry prevents premature duplicate recovery.
5. A correlated completed invocation awaiting projection is distinguishable from a missing invocation.
6. A genuine missing invocation is reconciled automatically through an idempotent/fenced mechanism.
7. Liveness reconciliation does not scan the backlog for new READY work.
8. Recovery evidence is durable and reconstructible.
9. Grace period is configurable.
10. A meaningful mutation that disables the liveness check or duplicate-prevention guard causes verification to fail.

## Initial priority / wave

Founder direction:

- **Priority: P0**
- **Wave: 2**

Rationale: unattended continuous execution is not reliable while a dropped transient event can leave an active BIU permanently inert. This is foundational control-plane reliability for the canonical Python factory, but it does not retrofit the currently running Wave 1 BIUs.

## Non-goals

This proposal does not require:

- polling Work Management for new work;
- retrofitting PY-06 or other already-running Wave 1 BIUs;
- modifying Node/B-DISP product semantics;
- using a model to perform routine liveness detection;
- lifecycle-state toggling as the permanent recovery mechanism;
- broad health monitoring unrelated to expected lifecycle effects.

## Desired outcome

The Python AlienIntent control plane can autonomously detect and recover the simple but critical condition:

> **The BIU is in a state that requires an actor, but no actor was launched.**
