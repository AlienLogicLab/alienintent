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

## Bootstrap evidence — the activation boundary (2026-09-21)

Monitoring survived the coordinator episode (previous section). Attention did not.

**Observed failure.** PY-06 reached DONE. The observer recorded it correctly and on time —
`OUTCOME_RECORDED / DONE_TO_DONE`, issue 54, `2026-09-20T15:59:06Z`, with the note *"closure complete
— next BIU release is coordinator work"*. It carried `requires_model_judgment: false`, because the
classifier treated DONE as a healthy outcome rather than as the one transition that **requires** a
coordinator to act. Nothing notified anyone and nothing activated. The factory sat idle until the
Founder manually told the coordinator that PY-06 was DONE, roughly 45 minutes later; only then were
closure verified, `main` reconciled, PY-07 re-assessed and released.

**The same gap immediately produced a worse instance.** At `16:56:38Z` PY-07's producer raised
`FOUNDER_EXCEPTION` — observed, flagged `requires_model_judgment: true`, and seen by no one. The
SWF-29 liveness watch then did its job at `17:04:41Z`, re-emitted the status, a second producer
started and refused identically at `17:06:09Z`. Deterministic recovery was working perfectly against
a condition only judgment could resolve, so it would have kept relaunching workers indefinitely. No
mechanism escalated, because no mechanism could.

> **Persistent observation and bounded coordinator cognition require an activation boundary. An
> observation requiring model judgment must become a durable attention item capable of activating, or
> at minimum notifying for activation of, a bounded coordinator episode.**

A corollary the second incident makes explicit:

> **Deterministic recovery must yield to attention. A recovery mechanism that cannot resolve a
> condition must stop repeating and raise it, rather than re-attempting on a timer.**

### Coordinator tenure during Wave 1 bootstrap (Founder decision, 2026-09-21)

> During Wave 1 bootstrap, coordinator tenure may span multiple BIUs for continuity, provided
> monitoring, authority, and recoverability remain externalized and durable. This does not change the
> canonical target of bounded, policy-controlled coordinator episodes.

This is an explicit, scoped departure from rule 2's one-BIU default, permitted by rule 5 (tenure is
policy) and bounded by rules 3, 8 and 9: it holds only while everything needed for correct
continuation stays outside the session. It is not evidence that long tenure is the target model.

### Applied

- **Durable attention queue** — `~/.local/state/alienintent/coordinator-attention.jsonl`, append-only,
  with a CLI (`attention.py list|show|ack`). A coordinator with no prior conversation can ask what
  needs judgment, see the BIU, event, timestamp, required authority and handled state, and acknowledge
  items with an attributable note. Attention outlives both the daemon and the episode.
- **Classification** — DONE (next release is coordinator work), `FOUNDER_EXCEPTION`, unrecovered
  `LIVENESS_GAP`, repeated verifier rejections on one BIU, and anything already flagged
  `requires_model_judgment`. Healthy IMPLEMENT/VERIFY/ACCEPT churn and a single rejection do not
  notify. Identity is the dispatcher's own outcome, not the moment of observation, so a daemon restart
  cannot re-alarm.
- **Notification, not activation** — a Windows toast through the WSL host, the only channel verified
  to work here. It is best-effort and loud on failure: the durable item is written first, and the
  attempt and its result are recorded beside it, so a dead channel can never look like a delivered one.

### Automatic model activation: available, deliberately not wired

Programmatic activation **is** technically supported in this environment — the dispatcher already
launches `claude -p` workers, so a daemon could start a coordinator episode the same way. It is not
wired, for two reasons that are decisions rather than limitations:

1. an unattended episode started by a daemon would perform authority-bearing acts (releases, Issue
   edits, commits) with no human present — the autonomy question is the Founder's, not the
   coordinator's, and rule 10 forbids a temporary control from becoming architecture by default;
2. under the tenure decision above, a coordinator episode is resident through Wave 1, so notification
   suffices; nothing currently needs waking.

The attention queue is the activation boundary either way: whatever eventually consumes it — a
notification, a Founder, or a policy-controlled episode launcher — reads durable observation identity,
never conversational state.

### The wake-up bridge, restored (2026-09-21)

The activation gap above had a concrete, recoverable cause. Before PY-06 the coordinator *was* woken —
not by design, but as a side effect: watchers ran as **Claude-tracked background tasks**, and the
harness delivers a completion event into the session when such a task exits. `watch_biu.sh` polled
durable state and called `exit 0` the moment it saw a reject, an authority block or a terminal state;
that exit was the wake-up. The same mechanism is visible in ordinary use — every background
Agent-Ready run in this episode announced itself the same way. The known failure mode confirms the
mechanism from the other side: a watcher launched with `&` inside a foreground command detached,
became untracked, and notifications stopped.

Moving monitoring to `systemd --user` was correct and is not reversed — but a systemd process is
invisible to the harness, so **detection survived and the callback died**. The cost is measured:
PY-06's DONE waited 45 minutes for a manual prompt, PY-07's `FOUNDER_EXCEPTION` was never seen at all,
and PY-08 sat in TASKS for 1h45m after its predecessor finished.

> While the Wave 1 bootstrap coordinator episode is resident, a session-bound attention waiter bridges
> durable attention events into the Claude harness. Persistent monitoring remains externalized and
> independent of coordinator lifetime.

The bridge is deliberately the smallest thing that restores the callback: one session-owned process
that waits on the durable queue and exits when something needs judgment. It takes no decision, mutates
no state and launches nothing — the exit *is* the signal. Detection stays in the systemd services,
which were not modified. Duplicate wake-ups are prevented by durable item identity rather than
timestamps, and acknowledgement plus re-arm closes the loop.

This does **not** wire unattended `claude -p` activation, which remains available and unauthorized for
the reasons above. It restores waking an episode that is already resident — which is exactly what the
Wave 1 tenure decision makes sufficient.

### Relationship to the Decision Inbox

These are two different queues and must not be merged. The **Decision Inbox** (SF-REQ-035, built by
PY-07) is a *product* capability: durable, attributable authority decisions that re-admit blocked work
through normal guards. This attention queue is *bootstrap operational tooling* that makes a coordinator
aware that something needs judgment at all — including that a `HumanDecisionRequired` exists. When the
Decision Inbox and SF-REQ-053 activation land, the durable attention items become inputs to them and
this file-based queue expires with the rest of the bootstrap. **No new Product Requirement is created:**
SF-REQ-053 owns the activation boundary and SF-REQ-035 owns human decisions.

## Scope and non-goals

No change to the current Wave 1 coordinator, worker or verifier behaviour, and no change to Node/B-DISP bootstrap behaviour. No coordinator-lifecycle experiment is started. No visible lifecycle state is created — existing authority does not require one. No fixed context-size or time thresholds are selected. No implementation, and no BIU is created from this record.
