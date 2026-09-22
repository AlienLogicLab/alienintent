# AlienIntent Post-Wave-1 Closure and Wave-2 Design Program Plan

## Status

Founder-approved operating plan for the local AlienIntent Program Director.

This document defines the ordered program of work from completed Wave 1 through Wave 2 design and Founder approval.

> **Terminology note (2026-09-22).** The programme this plan governed is complete. It uses the historical bootstrap-assessor readiness vocabulary (`BLOCKED`, `NEEDS_CLARIFICATION`, `SPLIT_RECOMMENDED`) and the borrowed name "Gap Trap"; both were superseded by Founder decisions v0.1 — Agent Ready's dispositions are `READY / CLARIFY / SPLIT / HOLD`, and the product-native term is *deterministic failure-class promotion*. The plan is retained unchanged as a historical operating record.

It is a **program operations artifact**, not a Product Requirement, BIU contract, lifecycle state machine, or replacement for canonical architecture authority.

The Program Director must pair this plan with the Intelligent Routing role definition.

Recommended companion role artifact:

    alienintent-local-program-director-intelligent-routing.md

If installed in-repo, use the local canonical path chosen by the bootstrap coordinator.

---

# 1. Mission

Wave 1 produced both:

1. working Python AlienIntent capability; and
2. empirical evidence about the factory, methodology, control plane, verification, planning, decomposition, routing, and bootstrap mechanisms.

Wave 2 must be designed from both.

The governing principle is:

> **Before AlienIntent builds the next wave, it must prove that it learned how to build the first one better.**

The Program Director must therefore complete the closure, evidence, learning, process-hardening, and architecture-reconciliation work in this plan before Wave 2 execution begins.

---

# 2. Operating model

## Primary orchestration role

Local AlienIntent Program Director

Responsibilities:

- maintain durable program state;
- select next authorized task;
- route work to the cheapest capable actor;
- launch bounded Codex sessions;
- request Claude review where appropriate;
- reconcile review findings;
- stop at Founder decisions;
- preserve authority boundaries;
- prevent duplicated analysis and repeated repository archaeology.

## Current actor preference

Primary analysis / design / artifact authoring:

    Codex GPT-6 Astra

Historical/bootstrap review and adversarial cross-check:

    current Claude bootstrap coordinator

Fresh independent high-risk review:

    fresh Claude or fresh Codex context as appropriate

Deterministic tooling:

    preferred whenever facts can be established without model reasoning

The Program Director must follow the Intelligent Routing policy before every model call.

---

# 3. Program-state rules

The local Program Director must maintain a durable program state containing at least:

    current_phase
    completed_phases
    active_tasks
    blocked_tasks
    founder_decisions_required
    primary_artifacts
    review_artifacts
    resulting_commits
    phase_exit_status

Suggested task states:

    PLANNED
    READY
    RUNNING
    REVIEW
    REPAIR
    BLOCKED
    FOUNDER_DECISION_REQUIRED
    DONE
    SUPERSEDED

These are program states only.

They must never be confused with AlienIntent BIU lifecycle states.

---

# 4. Phase gates

A phase may not be skipped merely because later work appears obvious.

Each phase has:

- objective;
- required inputs;
- work;
- preferred routing;
- deliverables;
- exit gate.

If the exit gate is not met, the Program Director must not advance the dependent branch.

---

# PHASE 0 — Wave 1 Closure Manifest

## Objective

Establish one authoritative terminal reconstruction of Wave 1 that a fresh model can understand without conversational history.

## Current status

COMPLETED by fresh Codex GPT-6 Astra.

Terminal implementation SHA reported:

    10cc81620511af56befbb6140504d1991bb02846

Closure/evidence repository pass landed afterward.

Independent Claude review is required before Phase 0+1 are finally accepted.

## Inputs

- Git history;
- GitHub Issues;
- GitHub Project state;
- Agent-Ready assessments;
- execution trajectory evidence;
- Quality Evidence;
- Wave 1 decisions;
- PY-10 live-proof artifacts.

## Work

Reconstruct the actually executed BIU population:

    PY-01
    PY-02
    PY-03
    PY-04
    PY-05
    PY-06
    PY-07
    PY-08
    PY-09
    PY-09B
    PY-10

For each BIU:

    Issue
    requirements
    dependencies
    final lifecycle
    accepted candidate SHA
    merge SHA
    Agent-Ready history/final disposition
    verifier rejection count
    DONE timestamp
    Issue closure
    evidence references

## Preferred routing

Primary:
    fresh Codex GPT-6 Astra

Review:
    current Claude bootstrap coordinator

Deterministic:
    Git ancestry, Issue state, counts, SHA checks

## Deliverable

    docs/evidence/wave1-closure-manifest.md

or current canonical equivalent.

## Exit gate

A fresh independent model can answer:

- what Wave 1 contained;
- what completed;
- what was accepted;
- which artifacts prove it;
- what remains UNKNOWN;

without conversation history.

---

# PHASE 1 — Final Evidence Reconciliation

## Objective

Create a trustworthy terminal evidence boundary before any learning analysis.

## Current status

COMPLETED by fresh Codex GPT-6 Astra.

Independent Claude review remains the gate before Phase 2.

## Inputs

- Execution Trajectory v1;
- Quality Evidence v1;
- PY-01 through PY-10 evidence;
- PY-09B evidence;
- repair-cycle data;
- factory incident evidence.

## Required work

Finalize/supersede terminal evidence for:

    PY-09
    PY-09B
    PY-10

Reconcile:

- candidate identities;
- merge ancestry;
- verifier rejection counts;
- finding counts;
- execution cycles;
- invocation attempts;
- provider interruptions;
- Agent-Ready assessment history;
- Issue closure;
- test counts;
- PY-10 live-proof branch counts;
- UNKNOWN telemetry.

Preserve:

> UNKNOWN is not zero.

Preserve:

> invocation attempt is not execution cycle.

Preserve:

> provider failure is not verifier rejection.

Preserve:

> observation is not verdict.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    Claude bootstrap coordinator

Deterministic:
    evidence consistency scripts, Git, structured JSON comparison

## Expected deliverables

At minimum:

    docs/evidence/wave1-evidence-reconciliation.md
    docs/evidence/wave1-repair-cycles.json
    docs/evidence/wave1-yield-snapshot.md
    docs/evidence/quality/wave1-cross-biu-comparison.md
    terminal PY-09 evidence
    PY-09B trajectory + Quality Evidence
    PY-10 trajectory + Quality Evidence

## Exit gate

Independent review disposition:

    PASS

or:

    PASS_WITH_QUALIFICATIONS

with no evidence defect serious enough to distort Learning Consolidation.

If:

    REPAIR_REQUIRED

repair evidence before Phase 2.

---

# PHASE 1R — Independent Closure/Evidence Review

## Objective

Independently verify Phase 0 + Phase 1 before allowing interpretation.

## Current status

NEXT REQUIRED GATE.

## Primary reviewer

Current Claude bootstrap coordinator.

Reason:

- it witnessed much of Wave 1;
- it can identify omitted incidents;
- it is not the author of the Codex evidence pass.

Its memory is a locator only.

Durable evidence wins on disagreement.

## Required checks

At minimum:

- 11-BIU population;
- terminal SHA;
- Issue/DONE state;
- rejection totals;
- first-pass acceptance population;
- PY-09 provider/failover history;
- PY-09B split/proven-red/permission history;
- PY-10 Agent-Ready history and capstone proof;
- correction provenance;
- UNKNOWN discipline;
- consistency checker quality;
- Claude PRODUCER authorization ambiguity;
- cold-start sufficiency of closure manifest.

## Deliverable

Review report with exactly one disposition:

    PASS
    PASS_WITH_QUALIFICATIONS
    REPAIR_REQUIRED

## Exit gate

PASS or PASS_WITH_QUALIFICATIONS.

Do not start Phase 2 before this.

---

# PHASE 2 — Wave 1 Learning Consolidation

## Objective

Convert scattered incidents and decisions into one deduplicated learning ledger.

Do not immediately create new requirements.

## Inputs

- accepted Phase 0+1 evidence boundary;
- all Wave 1 trajectory/Quality Evidence;
- factory incident records;
- SWF-18 through SWF-34;
- proposal history;
- Agent-Ready history;
- PY-10 proof.

## Primary task

For every material lesson, capture:

    learning_id
    failure_class
    originating_BIUs
    recurrence_count
    first_occurrence
    last_occurrence
    evidence_refs
    existing_owner
    enforcement_level
    mechanizable
    proven_red
    later_consumption
    effectiveness_evidence
    recommended_disposition

## Mandatory disposition buckets

Every lesson ends in exactly one:

    ALREADY_GRADUATED
    STRENGTHEN_EXISTING_OWNER
    GAP_TRAP_PROMOTION
    NEW_CAPABILITY_GAP
    BOOTSTRAP_ONLY

## Important clusters to test

Do not assume they are separate requirements.

### Proof quality

- tests that cannot fail;
- unexecuted code paths;
- proof harness built too late;
- regressions of previously proven behavior.

### Identity

- candidate identity;
- baseline identity;
- effect identity;
- attention identity;
- terminal result identity;
- BIU identifier grammar;
- execution cycle vs invocation.

### Recovery

- missing actor vs completed blocked effect;
- liveness suppression;
- provider capacity;
- partial-work continuity;
- provider failover;
- duplicate-safe recovery.

### Specification correctness

- valid check against wrong specification;
- copied bootstrap permission assumptions;
- impossible acceptance criteria.

### Decomposition

- SPLIT_RECOMMENDED;
- unowned capability;
- split lineage;
- dependency rewrite;
- requirement conservation.

### Observability

- provider-adapter log differences;
- normalized progress signals;
- buffered vs streaming output.

### Coordinator performance

Assess structural risk from coordinator-authored:

- contracts;
- infrastructure;
- release artifacts;
- recovery logic.

Do not reduce conclusions to "be more careful."

## Preferred routing

Primary:
    fresh Codex GPT-6 Astra

Why:
    must derive lessons from durable evidence without lived conversational bias

Review:
    Claude bootstrap coordinator, targeted/adversarial

Risk:
    MEDIUM/HIGH depending on lesson

## Deliverable

    Wave 1 Learning Ledger

Use existing evidence conventions or a clearly scoped evidence/analysis artifact.

## Exit gate

Every material Wave 1 lesson has:

- evidence;
- one canonical owner or explicit ownership gap;
- one recommended disposition.

No duplicate requirement proliferation.

---

# PHASE 3 — Gap Trap Graduation Audit

## Objective

Identify recurring known failure classes that should stop consuming REVIEW/model cognition.

## Canonical principle

> VERIFY proves what AlienIntent already knows how to check.
> REVIEW discovers what AlienIntent does not yet know how to check.

> REVIEW explores; VERIFY accumulates.

## Inputs

Learning Ledger entries marked:

    GAP_TRAP_PROMOTION

and possibly:

    STRENGTHEN_EXISTING_OWNER

## For each candidate determine

    failure_class
    cheapest_enforcement_layer
    deterministic_rule
    violation_fixture
    proven_red_method
    advisory_or_blocking
    canonical_owner
    expected_cognitive_work_removed
    effectiveness_metric

Possible enforcement destinations:

    static check
    unit/integration test
    mutation check
    architecture fitness
    schema validator
    admission gate
    state-machine invariant
    runtime assertion
    evidence consistency check
    config preflight

## High-priority classes already suspected

Evidence must confirm:

- non-discriminating tests;
- correct-but-unexecuted paths;
- proof harness missing before repair;
- baseline/result identity;
- BIU identifier parser assumptions;
- config validation before service restart;
- effect verification after command intent;
- attention/effect stable identity.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    Claude for high-impact promotions only

Deterministic:
    mutation/proven-red fixtures

## Deliverable

Gap Trap Promotion Backlog.

## Exit gate

Recurring known mechanically expressible defects no longer exist solely as prose reminders.

Each has a disposition and owner.

---

# PHASE 4 — Agent-Ready Outcome Completeness Audit

## Objective

Ensure every supported Agent-Ready terminal disposition and execution failure has a well-defined next process.

## Inputs

Actual Agent-Ready implementation/schema/CLI.

Do not infer supported outcomes only from Wave 1 observations.

## Observed examples

    READY
    BLOCKED
    NEEDS_CLARIFICATION
    SPLIT_RECOMMENDED

Also distinguish:

    provider/tool failure
    timeout
    malformed result
    missing terminal result

These are not readiness dispositions unless actual schema says otherwise.

## For every supported disposition define

    semantic_meaning
    authority_owner
    lifecycle_effect
    next_action
    required_artifact
    attention_behavior
    stale_assessment_rule
    reassessment_trigger
    DAG_effect
    Founder_decision_required
    implementation_allowed

## Required invariant

> Every Agent-Ready disposition has exactly one defined authority path.
> No non-READY outcome may be silently coerced into READY.

Also preserve:

> resolved prerequisites do not retroactively rewrite an old BLOCKED verdict; reassessment is required.

## Preferred routing

Primary:
    Codex GPT-6 Astra reading actual implementation

Review:
    Claude against Wave 1 incidents

## Deliverable

Agent-Ready Outcome Handling Matrix + gap analysis.

## Exit gate

No supported outcome requires coordinator improvisation.

---

# PHASE 5 — BIU Split / Replan Process Design

## Objective

Turn SPLIT_RECOMMENDED from a signal into a safe canonical decomposition operation.

## Reference incident

PY-10 -> PY-09B.

## Required semantics

### Authority

Who may authorize split/replan?

### Lineage

Original BIU -> resulting BIUs.

### Requirement conservation

Every original:

    requirement
    acceptance criterion
    verification obligation
    evidence obligation

must map to:

    child/replacement A
    child/replacement B
    retained integration parent

Nothing silently disappears.

### Scope conservation

Split redistributes authorized work.
It does not silently alter product intent.

### Dependency rewriting

Downstream dependencies must update deterministically.

### Identity allocation

No ad hoc regex assumptions.

### Lifecycle semantics

Define status of original BIU:

    parent
    superseded
    retained integration unit
    other canonical form

### Agent-Ready invalidation

Decomposition changes invalidate stale assessments.

### Project projection

Issues/dependencies/order/status remain coherent.

### Evidence

Preserve originating assessment and split authority.

### Closure

Define when original intent is fully satisfied.

## Strong invariant

> Splitting may change decomposition, but it must conserve authorized intent and proof obligations.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Independent design review:
    Claude

Risk:
    HIGH

## Deliverable

Canonical split/replan design.

Prefer amendment to existing planning/BIU authority where possible.

Likely owner candidates to audit:

    SF-REQ-013
    SF-REQ-015

Do not presume a new requirement.

## Exit gate

A future SPLIT_RECOMMENDED can be processed without improvised coordinator procedure.

---

# PHASE 6 — Bootstrap Retirement / Transition Audit

## Objective

Retire temporary controls safely and avoid accidental permanent bootstrap architecture.

Do not retire by date.

Retire by replacement.

## Audit at minimum

    SWF-21 release authority
    SWF-29 liveness reconciliation
    SWF-27 observer
    attention queue
    Windows notification
    session-bound attention waiter
    coordinator checkpoint
    PRODUCER-on-Claude temporary profile change
    Node/bootstrap execution authority
    any other explicitly temporary mechanism

## For each record

    mechanism
    purpose
    demonstrated_failure_prevented
    authority
    stated_expiry_condition
    replacement_requirement
    replacement_implemented
    bootstrap_still_operating
    recommended_disposition
    evidence

Allowed preliminary dispositions:

    RETIRE_CANDIDATE
    KEEP_UNTIL_REPLACED
    REVERT_TEMPORARY_CHANGE
    NEEDS_DECISION

## Special guidance

SWF-21:
    Wave 1 release purpose likely complete.
    Do not automatically reuse for Wave 2.

SWF-29:
    do not remove before SF-REQ-056 or equivalent replacement is actually operational.

Session-bound waiter:
    may retire with resident coordinator if no longer needed.

Persistent observer/attention:
    evaluate replacement separately.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    Claude bootstrap coordinator

Risk:
    HIGH where removing a known protection

## Deliverable

Bootstrap Retirement Matrix + recommended transition plan.

## Exit gate

No temporary mechanism quietly becomes permanent.

No known protection disappears before replacement is operational.

---

# PHASE 7 — Final Wave 1 Retrospective + Architecture Reconciliation

## Objective

Produce the authoritative evidence-backed conclusion of Wave 1 and reconcile approved lessons into architecture/requirements before Wave 2 planning.

## Inputs

- accepted closure/evidence boundary;
- Learning Ledger;
- Gap Trap audit;
- Agent-Ready outcome audit;
- split/replan design;
- bootstrap retirement audit.

## Final retrospective must include

### Yield

    BIU count
    first-pass acceptance
    verifier rejections
    repair cycles
    regressions
    Founder exceptions
    provider interruptions
    control-plane incidents
    elapsed time
    UNKNOWN telemetry

### Learning

    propagated lessons
    mechanized lessons
    proven-red controls
    recurring ungraduated failures

### Methodology

    verification-first sequencing
    split/decomposition
    Agent-Ready outcome handling
    Design Verification
    REVIEW -> Gap Trap -> VERIFY

### Architecture

    identity
    recovery
    provider capacity
    observability
    transport
    Work Management projection
    lifecycle
    control plane

## PY-09B / PY-10 evidence

Record as FACT if confirmed:

    both first-pass accepted

Record as INFERENCE/HYPOTHESIS:

    verification-first + bounded scope may have contributed

Do not claim causality without adequate evidence.

## Reconciliation rule

For every proposed change:

    existing owner first
    amendment preferred
    new Product Requirement only if genuinely uncovered
    Priority/Wave never invented

## Preferred routing

Primary author:
    Codex GPT-6 Astra

Independent review:
    Claude

Risk:
    HIGH

## Deliverables

    final Wave 1 retrospective
    architecture reconciliation
    approved amendment/proposal recommendations
    explicit unresolved Founder decisions

## Exit gate

Canonical architecture and requirement set reflect Wave 1 evidence rather than pre-Wave assumptions.

Only then proceed to Wave 2 design.

---

# PHASE 8 — Wave 2 Requirement Inventory + SPECIFY

## Objective

Determine the actual post-Wave-1 Wave 2 candidate set and fully specify each requirement before design.

## Inputs

- reconciled canonical requirements;
- CAPTURE backlog;
- Wave assignments;
- Learning Ledger outputs;
- approved post-Wave-1 amendments;
- bootstrap replacement needs.

Likely candidates to evaluate, not assume:

    SF-REQ-051 Design Contract / Design Verification
    SF-REQ-053 persistent control plane / bounded coordinator episodes
    SF-REQ-056 liveness reconciliation
    SF-REQ-039 fake-agent/offline factory proof
    SWF-32 execution cycle capability
    Agent-Ready process hardening
    split/replan capability
    other approved Wave 2 work

## For each requirement specify

    intent
    value
    scope
    non-goals
    dependencies
    acceptance criteria
    authority gaps
    security constraints
    operational constraints
    observability/evidence
    failure modes

## Important lifecycle goal

Wave 2 must begin making the previously underused upstream lanes operational:

    CAPTURE
      -> SPECIFY
      -> DESIGN
      -> PLAN
      -> TASKS
      -> READY

Do not mechanically preserve lanes without operational semantics.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    targeted Claude where requirements depend on Wave 1 historical behavior

## Deliverable

Specified Wave 2 candidate requirements.

## Exit gate

Every selected candidate is sufficiently specified for Design Contract work.

No unresolved product intent hidden in design.

---

# PHASE 9 — Wave 2 Design Contracts

## Objective

Define the intended architecture before BIU decomposition.

## For each design contract include

    bounded_context
    domain_owner
    ubiquitous_language
    ports
    adapters
    state
    transitions
    identities
    persistence
    concurrency
    failure_modes
    recovery
    evidence
    observability
    security
    operator_surface
    non_goals
    architecture_fitness
    deterministic_enforcement_opportunities

## Required discipline

Do not let implementation agents make material design decisions.

Design must be explicit enough that implementation becomes local execution rather than architecture invention.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Risk:
    HIGH

## Deliverable

Wave 2 Design Contracts.

## Exit gate

Each selected requirement has a complete candidate design ready for independent Design Verification.

---

# PHASE 10 — Wave 2 Design Verification

## Objective

Independently challenge design before planning/decomposition.

## Primary reviewer

Prefer fresh Claude independent context for major design verification.

Use current bootstrap Claude only where historical Wave 1 interpretation materially matters.

## Required checks

    ownership completeness
    requirement coverage
    capability ownership
    no scope holes
    architecture consistency
    platform feasibility
    impossible acceptance criteria
    security assumptions
    failure/recovery semantics
    deterministic enforcement
    proofability
    local iteration surface
    decomposition readiness
    Gap Trap opportunities
    bootstrap assumptions accidentally copied into canonical design

## Reference failure classes

Explicitly test against Wave 1 failures such as:

- unowned live transport;
- wrong permission specification;
- impossible Project isolation;
- hidden identifier grammar;
- tests that cannot fail;
- unexecuted "correct" structures;
- late proof harness;
- missing result identity;
- recovery ambiguity.

## Deliverable

Design Verification findings and disposition.

Suggested:

    VERIFIED
    REPAIR_REQUIRED
    OWNER_DECISION_REQUIRED

Use actual canonical vocabulary if defined.

## Exit gate

No material design finding remains unresolved.

Only verified designs proceed to PLAN.

---

# PHASE 11 — Wave 2 PLAN / Dependency DAG

## Objective

Turn verified designs into technical sequencing.

## Work

    identify implementation dependencies
    identify shared substrate
    identify parallel work
    identify required proof fixtures
    identify migrations
    identify bootstrap replacement sequence
    avoid circular dependencies
    define integration/capstone work

## Important lesson

A capstone must integrate previously proven capabilities.

It must not secretly become first owner of infrastructure required to perform its own proof.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    targeted Claude for high-risk DAG assumptions

## Deliverable

Verified Wave 2 dependency DAG and technical plan.

## Exit gate

Every planned capability has one owner and dependency path.

---

# PHASE 12 — Wave 2 BIU Decomposition

## Objective

Compile the verified Wave 2 plan into bounded execution units.

## Every BIU must contain

    intent
    requirement links
    fixed decisions
    scope
    non-goals
    dependencies
    acceptance criteria
    verification obligations
    evidence obligations
    architecture constraints
    capabilities
    budget
    candidate custody
    release policy
    stop condition
    escalation condition

## Apply learned decomposition rules

- bounded rework locality;
- proof harness established early;
- no unowned substrate;
- no impossible acceptance criteria;
- requirement conservation;
- shared capabilities separated where appropriate;
- capstones integrate rather than invent dependencies.

## Preferred routing

Primary:
    Codex GPT-6 Astra

Review:
    high-risk decomposition review as needed

## Deliverable

Candidate Wave 2 BIU set + DAG mapping.

## Exit gate

Every BIU is ready to undergo Agent-Ready assessment.

---

# PHASE 13 — Agent-Ready Assessment

## Objective

Assess every Wave 2 BIU using the audited outcome-handling process.

## Rules

- fresh current assessment;
- exact baseline;
- explicit provider/model provenance;
- terminal result validated structurally;
- every non-READY outcome follows the canonical handling matrix;
- no disposition coerced to READY;
- SPLIT_RECOMMENDED invokes the defined split/replan process;
- NEEDS_CLARIFICATION creates explicit clarification authority;
- BLOCKED remains blocked until inputs change;
- assessment execution failure is not a disposition.

## Preferred routing

Use cheapest-capable Agent-Ready provider subject to current policy and evidence.

Do not silently vary the readiness bar.

## Deliverable

Agent-Ready assessment set with resolution history.

## Exit gate

All intended Wave 2 release candidates are READY or explicitly excluded/blocked.

---

# PHASE 14 — Founder Approval

## Objective

Present the final evidence-backed Wave 2 program for Founder authority.

## Founder packet

Must contain:

    selected requirements
    design contracts
    design-verification results
    dependency DAG
    BIU set
    Agent-Ready status
    unresolved risks
    bootstrap transition plan
    expected deterministic controls
    Gap Trap promotions
    explicit priority/Wave decisions requiring Founder authority

## Program Director role

Recommend.

Do not decide Founder authority.

## Exit gate

Explicit Founder approval of final Wave 2 plan.

---

# PHASE 15 — Wave 2 Execution

Begins only after Phase 14.

At that point the execution factory operates under the new approved design and process.

This plan does not itself authorize Wave 2 release.

---

# 5. Cross-phase principles

## Principle A — Existing owner first

Before creating new authority:

    search existing requirement
    search existing decision
    search architecture authority
    search proposal history

Prefer amendment where one invariant already has an owner.

---

## Principle B — Observation != verdict

Always preserve:

    factual observation
    interpreted finding
    authority decision
    lifecycle verdict

as separate concepts.

---

## Principle C — Deterministic before cognitive

Never spend model tokens on facts deterministic tooling can establish reliably.

---

## Principle D — Cheapest capable routing

Do not optimize for cheapest call.

Optimize for lowest expected total cost to accepted quality.

---

## Principle E — Independent review is risk-based

LOW risk:
    deterministic checks may be sufficient.

MEDIUM:
    targeted second-model review.

HIGH:
    independent review mandatory where approved.

---

## Principle F — Proven red

A mechanically testable rule is not trusted merely because its check passes.

A meaningful violation must cause failure.

---

## Principle G — No false precision

UNKNOWN stays UNKNOWN.

Do not manufacture zeros.

---

## Principle H — Wave 1 historical integrity

Do not rewrite Wave 1 evidence to make later interpretation cleaner.

Corrections preserve provenance and supersession.

---

## Principle I — Temporary means temporary

Every bootstrap mechanism must have:

    purpose
    replacement
    expiry condition

But no protection is removed before replacement is operational.

---

## Principle J — Learning must reduce future cognition

A recurring mechanically expressible failure repeatedly rediscovered by models is evidence of incomplete learning graduation.

---

# 6. Current program position

As of local Program Director bootstrap:

    Wave 1 implementation: COMPLETE
    11 BIUs: DONE
    PY-10 capstone: DONE

    Phase 0: primary Codex pass COMPLETE
    Phase 1: primary Codex pass COMPLETE

    Required next gate:
        Phase 1R independent Claude closure/evidence review

    Phase 2:
        NOT STARTED

    Wave 2:
        NOT DESIGNED
        NOT AUTHORIZED FOR EXECUTION

The Program Director must not redo Phase 0/1 merely because it starts in a fresh session.

---

# 7. Immediate next action

The first real orchestration task is:

    task_id: POSTW1-REVIEW-001
    phase: 1R
    title: Independent Wave 1 Closure/Evidence Review
    actor: current Claude bootstrap coordinator
    risk: HIGH
    input:
        landed Phase 0/1 Codex evidence artifacts
    required disposition:
        PASS
        PASS_WITH_QUALIFICATIONS
        REPAIR_REQUIRED

Only PASS or PASS_WITH_QUALIFICATIONS unlocks Phase 2.

---

# 8. Definition of program completion

This post-Wave-1 program is complete when:

1. Wave 1 evidence is independently trusted;
2. lessons are consolidated and deduplicated;
3. mechanizable recurring failures have Gap Trap dispositions;
4. Agent-Ready outcomes have defined processes;
5. split/replan is designed;
6. bootstrap controls have safe transition decisions;
7. final Wave 1 retrospective is reconciled into architecture;
8. Wave 2 requirements are specified;
9. Wave 2 designs are independently verified;
10. Wave 2 DAG and BIUs are bounded;
11. Agent-Ready is complete;
12. Founder approves the Wave 2 plan.

Only then may Wave 2 execution begin.
