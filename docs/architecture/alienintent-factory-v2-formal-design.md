# AlienIntent Factory v2.0 — Formal Control-Plane Design

Date: 2026-09-29  
Status: **Canonical AlienIntent Factory v2 architecture. Architecture only: no v1 runtime change, cutover, migration, repository-visibility change, or retirement is authorized merely by this document.**

This document supersedes `AlienIntent_Factory_Director_Role_and_Buildout_2026-09-23.md` as a separate design authority and incorporates its enduring Factory Director/flywheel model. It also incorporates the Founder-approved private-canonical/public-publication repository architecture recorded on 2026-09-28. Historical decision records remain provenance, not competing design authorities.

## 1. Purpose

AlienIntent Factory v1 proved that autonomous software-factory execution is possible, but it also accumulated enough independent state interpretations, recovery paths, historical exceptions, mutable prose, sidecar files, and special-case control logic that the behavior of the control plane became difficult to predict.

v2.0 is a clean replacement design. It is **not a refactor of the v1 state machine**.

The objective is deliberately narrow:

> Given durable product intent, continuously convert the highest-priority eligible work into independently verified DONE outcomes using a control kernel whose behavior is deterministic, inspectable, replayable, and small enough to reason about completely.

v1 is retained as evidence, historical trajectory, and a source of requirements and failure classes. v1 implementation structure is not a compatibility target for the v2 control kernel.

## 2. Primary design rule

> **The control plane must be deterministic. Cognition may propose work, interpret ambiguous intent, design solutions, implement code, and perform qualitative review; cognition may not determine basic factory state, scheduling, ownership, transition legality, WIP, dependency satisfaction, or whether durable work has disappeared.**

If a factory-control decision can be expressed as data plus a deterministic rule, it belongs in the kernel and nowhere else.

## 3. v1 lessons promoted to v2 invariants

1. **One source of truth.** Current factory state must not be reconstructed from GitHub status, runtime claims, comments, hold files, inbox receipts, process lists, and prose simultaneously.
2. **Requirements are obligations until DONE.** Acknowledgement, classification, materialization, specification, planning, or dispatch is not completion.
3. **No hidden mutable state in work contracts.** Contracts contain stable intent and acceptance. Current status, claims, holds, dependency state, and runtime revision live only in canonical structured state.
4. **WIP constrains execution, not preparation.** Specification, planning, decomposition, readiness assessment, and queue replenishment may proceed while implementation WIP is full.
5. **READY is real inventory.** HOLD, CLARIFY, partially prepared, or merely assessed work does not count as READY supply.
6. **Founder decisions are not generic blockers.** A technical prerequisite, credential failure, missing fixture, failed verification, unavailable dependency, or runtime defect is never represented as a Founder decision.
7. **DONE cannot own WIP.** Ownership and lifecycle are one model, not two loosely reconciled models.
8. **Merged is not deployed.** Runtime revision is explicit state when deployment matters.
9. **Every failure class becomes a rule or test.** Recurring failures must not depend on future agents remembering past incidents.
10. **No special-case transition without a generalized invariant.** One-off fixes are rejected from the kernel unless the underlying rule is defined for all work items of the same class.
11. **Idempotency is mandatory.** Replaying commands, duplicate events, restart recovery, and repeated reconciliation must converge to the same state.
12. **External systems are projections.** GitHub Project, Issue comments, dashboards, notifications, and worker process state may reflect canonical state; they do not define it.

## 4. Architectural boundary

v2 has five control-plane components:

1. **Canonical Ledger** — durable append-only transition/event history plus transactional current-state projection.
2. **Transition Kernel** — the only code allowed to change canonical lifecycle/ownership state.
3. **Scheduler** — pure selection logic over canonical state; it proposes the next legal transition but does not mutate directly.
4. **Effect Executor** — performs external effects after a committed transition intent, with idempotency keys and readback.
5. **Adapters** — GitHub, workers, Agent Ready, notifications, deployment systems, and other external services. Adapters translate; they do not own factory truth.

Cognitive agents live outside the kernel. They receive bounded assignments and return typed results.

## 5. Canonical persistence

### 5.1 Reference implementation

The initial v2 reference persistence is a **single SQLite database in WAL mode** on the factory host. PostgreSQL may be substituted later without changing domain semantics.

The database owns:

- immutable `events`;
- current `work_items` projection;
- dependencies;
- claims;
- decisions/blockers;
- effect intents and effect receipts;
- artifact/revision references;
- worker results;
- deployment/runtime revisions where relevant.

No YAML, Markdown, GitHub comment, Project field, process table, or model memory is canonical operational state.

### 5.2 Transaction rule

A legal state change is one database transaction:

1. validate command against current canonical state;
2. append immutable event;
3. update canonical projection;
4. create any required effect-intent rows;
5. commit.

External effects occur **after** commit. Effect completion is recorded separately using the effect's stable idempotency key.

### 5.3 Replay invariant

Replaying all committed events from genesis must reproduce the canonical projection exactly.

A projection mismatch is a fatal control-plane integrity fault; the factory stops mutation, notifies the operator, and remains read-only until repaired.

## 6. Domain model

### 6.1 WorkItem

Every durable obligation is a `WorkItem`.

Required fields:

- `id` — immutable factory identity;
- `kind` — `REQUIREMENT | BIU | MAINTENANCE | DECISION | MIGRATION`;
- `parent_id` — optional owning work item;
- `title`;
- `intent_ref` — immutable/source-controlled artifact or captured input reference;
- `priority` — explicit `P0..P5` or `UNPRIORITIZED`;
- `state`;
- `created_at`;
- `updated_at`;
- `version` — optimistic-concurrency integer;
- `authority_ref`;
- `acceptance_ref`;
- `runtime_target` when applicable.

Mutable operational facts are not stored in `intent_ref` documents.

### 6.2 Dependency

A dependency is a canonical edge:

`WorkItem A requires WorkItem B to satisfy predicate X.`

Initial v2 predicate set should remain intentionally small:

- `DONE`
- `ACCEPTED`
- `ARTIFACT_AVAILABLE`
- `DECISION_RESOLVED`

New dependency predicates require explicit architecture review.

### 6.3 Claim

A `Claim` is canonical execution ownership.

Fields:

- `work_item_id`;
- `phase` — `IMPLEMENT | VERIFY | ACCEPT`;
- `owner_id`;
- `invocation_id`;
- `generation`;
- `claimed_at`;
- `lease_until`;
- `status` — `ACTIVE | RELEASED | EXPIRED`.

There may be **at most one ACTIVE claim per WorkItem** and no more ACTIVE execution claims globally than the configured WIP limit.

### 6.4 Blocker

A blocker is structured, typed, and attributable:

- `DEPENDENCY`
- `DECISION_REQUIRED`
- `TECHNICAL`
- `CREDENTIAL`
- `EVIDENCE`
- `CAPACITY`
- `EXTERNAL_SERVICE`
- `VERIFICATION_FAILURE`
- `RETRY_EXHAUSTED`

A blocker contains `owner`, `reason_code`, `details_ref`, and `resolution_predicate`.

There is no generic `HOLD` state with overloaded meaning.

## 7. Lifecycle model

### 7.1 Primary lifecycle

The v2 semantic lifecycle remains recognizable but separates preparation from execution ownership:

`CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY → ACCEPT → DONE`

`REVIEW` is a verification activity or policy gate rather than a mandatory persisted lane unless later evidence proves a separate state is valuable.

### 7.2 Side conditions, not lifecycle states

The following are orthogonal conditions, not ad-hoc lifecycle substitutes:

- blocked;
- claimed;
- decision required;
- retry exhausted;
- external effect pending;
- deployment pending;
- runtime unhealthy.

This avoids exploding the state machine into combinations such as `IMPLEMENT_UNCLAIMED_FOUNDER_EXCEPTION_RECOVERABLE`.

### 7.3 Legal transition table

| From | To | Minimum deterministic preconditions |
|---|---|---|
| CAPTURE | SPECIFY | durable authority exists; priority is explicit or item is explicitly allowed to remain UNPRIORITIZED; no unresolved intake-identity conflict |
| SPECIFY | PLAN | specification and acceptance references complete; required product decisions resolved |
| PLAN | TASKS | approved decomposition exists; 100% obligation coverage; dependency graph valid |
| TASKS | READY | current contract passes lint/readiness; dependencies required for execution are satisfied; finite execution budget exists |
| READY | IMPLEMENT | highest-priority eligible selection; WIP available; no active claim; release policy passes |
| IMPLEMENT | VERIFY | producer returned retrievable immutable candidate + required mechanical evidence; IMPLEMENT claim released atomically with VERIFY claim eligibility |
| VERIFY | IMPLEMENT | verifier rejects with actionable findings and retry budget remains |
| VERIFY | ACCEPT | independent verification passes exact candidate and required evidence |
| ACCEPT | DONE | required landing/publication/deployment/closure effects completed and read back; no unresolved completion obligation |

No other normal transition is legal.

Rollback and repair paths are explicit commands with their own predicates; they do not masquerade as arbitrary backward Project edits.

## 8. Formal transition function

All lifecycle mutation routes through one function conceptually equivalent to:

```text
Result transition(Command c, FactoryState s)
```

The function is pure with respect to domain state. It returns either:

```text
Accepted {
    events[]
    new_state
    effect_intents[]
}
```

or:

```text
Rejected {
    reason_code
    observed_version
    violated_invariants[]
}
```

It must not perform network calls, launch models, inspect processes, read GitHub, or interpret prose.

## 9. Scheduler

The scheduler is intentionally boring.

### 9.1 Selection order

For executable work:

1. consider only canonical `READY` items;
2. remove items whose execution dependencies are unsatisfied;
3. remove items with unresolved blockers;
4. sort by explicit priority `P0` through `P5`;
5. within equal priority, use stable FIFO by `ready_at`, then immutable `id`;
6. admit until WIP is full.

No model chooses execution order.

### 9.2 Preparation order

Preparation is independent of execution WIP.

When the READY buffer is below target:

1. choose highest-priority non-DONE requirement/work item whose next preparation transition is legal;
2. advance deterministic steps directly;
3. create bounded cognitive assignment only when semantic work is required;
4. continue until READY buffer target is satisfied or every candidate has a typed blocker.

### 9.3 Scheduler pseudocode

```text
loop:
    reconcile_expired_claims()
    reconcile_effect_receipts()

    while ready_depth < ready_target:
        item = highest_priority_preparable_item()
        if item is None:
            break
        advance_preparation(item)

    while active_execution_claims < wip_limit:
        item = highest_priority_ready_item()
        if item is None:
            break
        claim_and_dispatch(item)

    if no deterministic or delegated progress is possible:
        sleep_until_event()
```

That should remain approximately the conceptual complexity of the production scheduler.

## 10. Requirement intake

### 10.1 Intake invariant

> A requirement accepted from the Founder or another authorized source remains a canonical obligation until its owning requirement reaches DONE or is explicitly superseded/cancelled by the same or greater authority.

### 10.2 Intake transaction

Authorized intake performs one deterministic transaction:

1. allocate immutable `WorkItem.id`;
2. store exact source payload or immutable reference;
3. record authority identity;
4. record supplied priority or `UNPRIORITIZED`;
5. enter `CAPTURE`;
6. append `RequirementCaptured` event.

Only after that transaction may an external inbox/message be acknowledged.

Therefore **there is no ACKNOWLEDGED-NOT-MATERIALIZED state in v2**.

### 10.3 Duplicate intake

Duplicate detection may propose a possible match, but it may not silently discard the new requirement.

Resolution must be one of:

- `NEW`;
- `DUPLICATE_OF(id)` with attributable authority;
- `SUPERSEDES(id)` with attributable authority;
- `CLARIFICATION_REQUIRED`.

Every outcome remains durable.

## 11. Priority semantics

AlienIntent does not invent product priority.

Rules:

- supplied P0–P5 is authoritative when source authority permits it;
- absent priority becomes `UNPRIORITIZED`, never guessed;
- `UNPRIORITIZED` requirements remain visible and generate a decision obligation if priority is required for progression;
- dependencies can make a high-priority item temporarily ineligible but cannot lower its priority;
- scheduling always chooses the highest-priority **eligible** item.

Wave/grouping metadata is not execution priority.

## 12. WIP and queue invariants

For configured execution WIP `N`:

1. `0 <= ACTIVE_EXECUTION_CLAIMS <= N` always.
2. Every ACTIVE claim references exactly one execution-state WorkItem.
3. Every execution-state WorkItem has either exactly one ACTIVE claim or a typed recovery/blocker condition visible to the scheduler.
4. READY depth does not include blocked or non-READY items.
5. Preparation continues while WIP is full.
6. Completion of one execution claim causes immediate deterministic refill from READY if an eligible item exists.
7. If READY is empty and preparable authorized backlog exists, preparation control is active; the system may not report healthy idle.

## 13. Worker protocol

Workers do not mutate canonical lifecycle directly.

A worker receives an immutable `Assignment` containing:

- WorkItem id/version;
- phase;
- intent/contract refs;
- exact baseline;
- allowed repositories/paths/effects;
- budget;
- acceptance/evidence obligations;
- invocation id/generation.

A worker returns exactly one typed terminal result:

- `IMPLEMENTED(candidate_ref, evidence_refs)`;
- `VERIFIED(candidate_ref, evidence_refs)`;
- `REJECTED(findings_ref)`;
- `BLOCKED(blocker_type, details_ref)`;
- `FAILED(failure_code, details_ref)`.

Free-form prose may accompany a result but never controls routing.

## 14. Verification

Verification is independent by identity and assignment.

The kernel enforces:

- candidate immutability;
- verifier distinct from producer identity;
- candidate retrievability;
- required mechanical regression receipts before expensive cognition;
- exact candidate identity in verdict;
- rejected findings cause a deterministic transition back to IMPLEMENT only if retry budget remains.

A verifier does not decide lifecycle policy.

## 15. Retry and failure semantics

Retry policy is data, not branching code.

Each phase has configured limits. On failure/rejection:

```text
if retries_used < retry_limit:
    transition according to policy
else:
    create RETRY_EXHAUSTED blocker
```

There are no special Issue-number exceptions in the kernel.

Changing retry policy is configuration/authority, not a code branch.

## 16. Decisions and human authority

A real unresolved Founder/product decision is represented by a `DECISION` WorkItem and a `DECISION_REQUIRED` blocker referencing it.

Resolving the decision appends a durable event and deterministically removes dependent decision blockers.

Technical blockers never become decision blockers merely to stop retries.

The Founder is interrupted only when the required authority genuinely belongs to the Founder.

## 17. Effects and idempotency

Every external mutation has a stable `effect_id` derived from canonical intent, not wall-clock randomness.

Examples:

- GitHub Project projection update;
- branch publication;
- merge/landing;
- deployment;
- service restart;
- notification.

Effect states:

`PENDING → APPLIED → READ_BACK`

or

`PENDING → FAILED`

Reissuing an already APPLIED/READ_BACK effect is a no-op.

Unknown effect outcome is explicit and blocks unsafe duplication until reconciled.

## 18. External projections

GitHub is a human-visible projection and collaboration surface.

Projection rules:

- canonical ledger → GitHub Issue/Project fields/comments;
- projection failure does not rewrite canonical truth;
- projection lag is visible as `projection_status`;
- external edits that are not authorized commands do not silently mutate canonical state;
- adapters may translate authorized external commands into kernel Commands.

The same rule applies to dashboards, notifications, local files, and future integrations.

## 19. Runtime revision and deployment

When a WorkItem's DONE predicate includes runtime behavior, canonical state records:

- landed revision;
- deployed revision;
- target environment/profile;
- deployment effect id;
- readback evidence.

`landed_revision != deployed_revision` means deployment is incomplete. DONE is refused when deployment is part of acceptance and readback is absent.

## 20. Cognition boundary

### Cognition is appropriate for

- interpreting new ambiguous requirements;
- specification;
- architecture/design;
- decomposition proposals;
- code implementation;
- novel debugging;
- qualitative review;
- producing structured findings.

### Cognition is forbidden from deciding

- canonical current state;
- transition legality;
- priority ordering;
- dependency satisfaction;
- WIP accounting;
- claim ownership;
- retry counts;
- whether a requirement still exists;
- whether an external effect already occurred;
- whether a runtime revision is deployed;
- whether DONE prerequisites are mechanically satisfied.

If cognition returns a result the kernel cannot map to a typed command/result, nothing changes.

## 21. Observability

The minimum operator view is derived entirely from canonical state:

- active claims / WIP limit;
- READY queue in execution order;
- preparation queue in priority order;
- blocked items grouped by blocker type and owner;
- oldest unresolved requirement;
- pending effects;
- failed projections;
- current runtime revision(s);
- throughput and cycle counts.

No dashboard calculates independent truth.

## 22. Formal safety properties

The v2 implementation must prove with executable tests at minimum:

### S1 — State uniqueness
A WorkItem has exactly one canonical lifecycle state.

### S2 — Transition legality
No state transition occurs outside the transition table.

### S3 — WIP safety
ACTIVE execution claims never exceed configured WIP.

### S4 — Claim coherence
DONE/READY/preparation-state items cannot retain ACTIVE execution claims.

### S5 — Requirement conservation
Every accepted requirement is reachable from canonical state until DONE or explicitly superseded/cancelled with authority.

### S6 — Dependency safety
No item enters READY/IMPLEMENT when its required execution predicates are unsatisfied.

### S7 — Priority safety
When capacity opens, no lower-priority eligible READY item is selected ahead of a higher-priority eligible READY item.

### S8 — Idempotency
Repeating the same command/event/effect receipt cannot produce a second semantic transition/effect.

### S9 — Replay equivalence
Replaying the event ledger reproduces the current projection exactly.

### S10 — Ownership safety
At most one active owner exists for a WorkItem phase/generation.

### S11 — Verification independence
A producer cannot satisfy its own independent verification obligation.

### S12 — No silent idle
If legal deterministic or delegated progress exists, the scheduler cannot enter healthy idle.

## 23. Liveness properties

Safety prevents bad transitions; liveness prevents factory starvation.

### L1 — Ready refill
If preparable authorized backlog exists and READY depth is below target, preparation is eventually scheduled.

### L2 — Execution refill
If WIP capacity exists and an eligible READY item exists, it is eventually claimed.

### L3 — Result routing
Every terminal worker result causes a deterministic next state or a typed blocker.

### L4 — Requirement progress
Every non-DONE requirement is either advancing, queued by priority, or visibly blocked by a typed owner/resolution predicate.

### L5 — Restart recovery
After process restart, canonical state and effect receipts are sufficient to resume without model reconstruction or historical-prose interpretation.

## 24. What v2 explicitly deletes from the kernel

The v2 core must not contain equivalents of:

- issue-number-specific branches;
- generic Founder-hold JSON as a universal suppression mechanism;
- parsing arbitrary Issue prose to infer current state;
- current-state facts copied into Markdown work units;
- worker claims reconstructed from unrelated process heuristics;
- status edits used as magic retry/re-arm signals;
- special recovery semantics keyed to prior result prose;
- multiple independent implementations of lifecycle eligibility;
- model reasoning to decide whether READY/WIP/dependencies are satisfied;
- manual “poke the lane” behavior required for normal progress.

## 25. Factory Director operating model

The Factory Director is the persistent **coordination cognition** around the deterministic kernel. It is not the lifecycle engine, not the scheduler, not the source of product authority, and not the domain brain for every bounded context.

### 25.1 Mission

> **Continuously coordinate authorized work so the factory maintains a healthy supply of correctly prioritized executable work and processes it through completion with minimal avoidable coordination latency.**

The Director optimizes flow subject to deterministic policy: authority, priority, dependencies, WIP, readiness, verification, budgets, security/privacy, custody, and durable plan obligations.

The Director is successful when the factory does not idle merely because preparation, delegation, or coordination that was already authorized failed to happen.

### 25.2 Two connected flows

The Director coordinates two flows that remain conceptually distinct.

**Demand / definition flow**

```text
Proposal / Feature / Defect / Discovery
                |
              CAPTURE
                |
             SPECIFY
                |
               PLAN
                |
              TASKS
                |
          readiness work
                |
              READY
```

**Execution flow**

```text
READY -> IMPLEMENT -> VERIFY -> ACCEPT -> DONE
```

Review, assurance, deployment, publication, and other gates may participate as typed policies/effects without multiplying the core lifecycle unnecessarily.

WIP applies to execution. It does **not** prohibit the Director from continuing specification, planning, decomposition, readiness work, dependency resolution, or queue replenishment for later work.

### 25.3 Director control loop

The cognitive Director operates over typed kernel queries and commands:

```text
OBSERVE
  canonical state, queues, blockers, effects, runtime health
      |
      v
INTERPRET
  determine which uncertainty actually needs cognition
      |
      v
DELEGATE / PROPOSE
  requirements, design, planning, readiness, implementation,
  verification, recovery, or operator attention
      |
      v
COMMAND
  submit typed intent to the deterministic kernel
      |
      v
VERIFY RESULT
  consume canonical state/effect readback, never prose inference
      |
      +----> repeat
```

The Director never changes canonical state by editing projections or by narrating a desired outcome. It asks the kernel to perform a typed command; the kernel accepts or rejects it mechanically.

### 25.4 Queues

v2 exposes four operator-visible logical queues derived from canonical state:

- **Intake** — durable requirements/proposals not yet sufficiently specified.
- **Definition** — specification, design, planning, decomposition, and readiness work.
- **Admission** — READY work waiting for execution capacity or an explicit release policy.
- **Execution** — claimed IMPLEMENT/VERIFY/ACCEPT work.

Blocked work is not a fifth lifecycle. It is a typed condition attached to the owning WorkItem with an explicit owner and resolution predicate.

### 25.5 Delegation boundary

The Director delegates substantive work to authoritative capabilities rather than emulating every capability itself with ad hoc prompting. Examples include requirements/specification, architecture/design, planning/decomposition, Agent Ready, allocation, producer implementation, independent verification, review, publication assembly, and deployment.

Each delegated capability returns typed artifacts/results. Free-form prose may explain a result but cannot itself mutate lifecycle state.

### 25.6 No-idle rule

Healthy idle exists only when **no legal deterministic transition, no eligible execution, and no authorized cognitive preparation/delegation can advance the factory**.

If READY is below target while authorized preparable backlog exists, the Director must keep preparation active. If execution capacity is available and eligible READY work exists, the deterministic scheduler must fill it. If neither can progress, the blocking predicate must be visible and attributable.

### 25.7 Factory health

Factory health is measured from canonical state, not model impressions. Minimum flow indicators include:

- READY depth and target;
- executable WIP / limit;
- oldest unresolved requirement;
- blocked items by type/owner;
- time in state;
- preparation throughput;
- implementation/verification cycle counts;
- retry exhaustion;
- pending/unknown external effects;
- projection drift;
- runtime/deployed revision drift;
- requirements with no legal next action.

The Director may explain these metrics cognitively, but it does not calculate alternate truth.

## 26. Repository authority and deterministic public publication

AlienIntent v2 separates **engineering authority** from **publication**.

### 26.1 Private canonical engineering repository

The canonical engineering repository is private by default. It is the durable product-development authority and may contain:

- source and tests;
- requirements, architecture, design and ADRs;
- Ubiquitous Language and contracts;
- work units and internal evidence;
- internal Issues/Project state references;
- Factory Director internals;
- migration/cutover plans;
- durable private runbooks;
- provider/model evaluations and other internal engineering material.

Committing an artifact to the canonical repository does **not** publish it.

### 26.2 Public repository is a publication target

A public repository, when configured, is a separate product/distribution surface generated from an explicitly approved canonical private revision.

Typical public content may include:

- intentionally released source and appropriate tests;
- README, LICENSE, CONTRIBUTING and SECURITY;
- build/package metadata required by users;
- installation and stable API/extension documentation;
- deliberately curated public architecture/security/contributor guidance;
- intentional releases and public tags.

The public repository is never canonical engineering authority merely because it is visible to users.

### 26.3 Publication classification

Every canonical artifact resolves to exactly one publication classification:

- `INTERNAL` — default;
- `PUBLIC_SOURCE` — explicitly approved open-source product content;
- `PUBLIC_DOCUMENTATION` — explicitly approved external documentation.

Unknown or missing classification means `INTERNAL`.

There is no denylist-based publication mode.

### 26.4 Publication pipeline

Publication is a deterministic, allowlist-based, fail-closed factory operation:

```text
private canonical revision
        |
publication assembler
        |
explicit allowlist/classification resolution
        |
reject unknown/unclassified public candidates
        |
secret scan
        |
private-reference / internal-path scan
        |
public build + tests
        |
public API/compatibility checks
        |
immutable publication candidate
        |
explicit publication authority
        |
public repository / release
```

The Factory Director may coordinate publication, but it may not infer privacy from conversation context, model memory, filename patterns, or prior publication. Classification and publication authority are deterministic data.

### 26.5 Public/private issue separation

Internal Issues and the internal Project are factory-control infrastructure and remain private with the canonical engineering authority.

A public repository may expose a separate public Issue/Discussion surface. External input follows:

```text
external report / proposal / question
            |
        public intake
            |
     internal evaluation
            |
 possible RequirementCandidate
            |
 canonical private Requirements context
```

A public Issue never directly becomes a canonical requirement, BIU, priority decision, worker assignment, or execution authority.

### 26.6 Branch and history separation

Private canonical history may retain detailed engineering truth and worker/candidate branches required for custody.

Public publication must not automatically expose worker branches, internal failure history, private planning, model/provider strategy, or security-sensitive operations. Public history may compose or squash accepted private changes into externally meaningful commits.

The preferred public repository genesis is a **fresh curated publication snapshot**, not a rewrite of the full internal Git object graph.

### 26.7 Operations-document rule

Transient operational narrative is not a permanent architecture mechanism. When an operational incident reveals a durable rule, promote that rule into one or more of:

- requirement;
- architecture/design/ADR;
- deterministic policy;
- executable invariant/regression test;
- durable private runbook.

Then the transient operational record may expire or remain only in private continuity/history.

### 26.8 Installer/product invariant

A new AlienIntent installation assumes:

> **canonical engineering repository = private unless explicitly configured otherwise**

If a user wants a public repository, it is configured as a separate publication target. Setup must never assume `canonical repo == public repo`, `commit == publication`, `public Issues == internal work management`, or `GitHub visibility == engineering authority`.

### 26.9 Publication safety properties

The v2 conformance suite must prove:

- unknown classification cannot publish;
- only allowlisted artifacts enter a publication candidate;
- internal requirements/design/evidence/work units/worker branches cannot leak by default;
- secrets/private references fail publication;
- a public publication is reconstructable from canonical revision + publication policy;
- repeating publication assembly is deterministic;
- public intake cannot bypass internal requirement authority;
- publication and normal engineering commits are distinct effects with distinct authority.

## 27. v1 compatibility policy

v2 must preserve **intent and evidence**, not v1 implementation quirks.

During migration:

- v1 stays operational;
- v2 runs in shadow mode against mirrored inputs/events;
- v2 does not mutate v1 state;
- historical v1 outcomes are converted into replay fixtures;
- divergences are classified as v2 defect, v1 defect, or intentional semantic change;
- no v1 special case is copied merely to make replay match a known-bad outcome.

## 28. v2 build sequence

### Phase V2-0 — Formal model

Deliver:

- state enum;
- transition table;
- typed commands/results/events;
- invariant suite;
- reference scheduler function.

No GitHub, workers, models, or services.

### Phase V2-1 — Canonical ledger

Deliver:

- SQLite schema;
- transactional event append + projection update;
- replay;
- optimistic concurrency;
- corruption/replay tests.

### Phase V2-2 — Deterministic scheduler

Deliver:

- priority/FIFO;
- dependencies;
- READY target;
- WIP;
- claim lifecycle;
- blocker ownership;
- exhaustive model-based/property tests.

### Phase V2-3 — Requirement intake

Deliver:

- authorized capture;
- immutable provenance;
- duplicate/supersession handling;
- requirement-conservation tests;
- priority handling.

### Phase V2-4 — Worker protocol

Deliver:

- Assignment schema;
- typed terminal results;
- producer/verifier independence;
- retry/exhaustion;
- no model-driven routing.

### Phase V2-5 — Effect executor

Deliver:

- effect intents;
- idempotency;
- readback;
- unknown-effect recovery;
- deployment revision tracking.

### Phase V2-6 — GitHub projection

Deliver:

- one-way canonical projection;
- authorized command ingress;
- drift detection;
- projection repair.

### Phase V2-7 — Shadow factory

Run v2 alongside v1 on real incoming work without authority to mutate production execution.

Acceptance requires sustained agreement on correct behavior and explicit explanation of every divergence.

### Phase V2-8 — Controlled cutover

Only after live proof:

1. freeze new v1 intake;
2. reconcile all open obligations into v2 canonical state;
3. prove counts/identities/priorities/dependencies;
4. enable v2 as sole writer;
5. retain v1 read-only rollback evidence;
6. retire v1 control components only after a defined stability window.

## 29. v2 acceptance bar

v2 is not production-ready because unit tests pass.

Before cutover it must demonstrate:

- deterministic replay from empty database to exact expected state;
- property-based state-machine testing across large generated transition sequences;
- fault injection at every transaction/effect boundary;
- duplicate event/effect immunity;
- process-kill/restart recovery;
- priority/dependency/WIP correctness;
- requirement conservation from inbox through DONE;
- rejection/rework cycles;
- external projection outage/recovery;
- worker credential outage/recovery;
- deployment revision mismatch detection;
- sustained shadow operation without Founder maintenance intervention.

## 30. Complexity budget

The v2 kernel has an explicit complexity budget.

- One lifecycle transition module.
- One scheduler module.
- One canonical persistence interface.
- One claim implementation.
- One blocker taxonomy.
- One effect state machine.
- No duplicated transition predicates across adapters.

A proposed kernel feature must answer:

1. Which invariant requires it?
2. Why can it not live outside the kernel?
3. What state-space increase does it introduce?
4. What property/negative-control test proves it?

If those answers are weak, the feature does not enter the kernel.

## 31. Definition of “expensive watch” behavior

The factory behaves correctly when an operator can predict its next action from canonical state without reading source code, model transcripts, or historical comments.

Given the same canonical state and same command/event, v2 must produce the same result.

For every non-DONE WorkItem, the system must be able to answer mechanically:

- What is it?
- What priority is it?
- What state is it in?
- Who owns it, if anyone?
- What is it waiting for?
- What exact predicate clears that wait?
- What legal transition comes next?
- Why is it not happening now?

If the answer requires reconstructing a conversation, interpreting prose, or asking a model what probably happened, v2 has failed its design objective.

## 32. Governing principle

> **AlienIntent v2 should be difficult to make clever and easy to prove correct.**

The intelligence belongs in creating and improving software. The factory mechanism itself should be boring, deterministic machinery.
