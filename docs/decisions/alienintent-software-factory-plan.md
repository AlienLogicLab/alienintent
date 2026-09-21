# AlienIntent Software Factory — Borrowing Plan and Product Requirements

**Date:** 2026-09-19  
**Status:** Founder-directed product/architecture plan — authoritative copy (clarified 2026-09-19; see Wave 1 clarification)  
**Owner:** Alien Logic Lab  
**Product:** AlienIntent

## Product proposition

AlienIntent is a software-factory control plane:

> **Authorized product requirements in → verified working software out.**

The intended human role is to define product intent, requirements, priorities, and genuinely consequential product/architecture decisions. AlienIntent should progressively automate everything downstream.

Given a populated backlog, configured priorities, sufficient execution authority, and no unresolved blockers, AlienIntent must continue working until the executable backlog is exhausted, external reality blocks progress, or a genuine human authority decision is required.

That behavior is a principal product acceptance criterion.

## Human role and long-term direction

Near term: **manage work, not agents**.

Long term: commoditize more of work management itself as requirements become structured, architecture becomes durable and machine-enforceable, planning becomes contract-driven, verification becomes mechanical, routing becomes evidence-based, and policy improves from evidence.

The human role should progressively move toward **ideation, product intent, and genuinely novel authority decisions**.

## Planning authority

### Founder / Product authority

Owns product intent, product priorities, product scope, business requirements, product tradeoffs, new architectural direction, authority exceptions, and unresolved decisions that materially change product semantics, trust, cost, privacy, deployment, or workflow.

AlienIntent must not invent product priorities.

Priority is input. When several READY BIUs are otherwise equal, the default scheduler takes the next eligible READY BIU.

### Architecture authority

Durable architecture records and EOS constrain planning.

The planner may not silently change DDD boundaries, Hexagonal Architecture, ACLs, lifecycle semantics, Ubiquitous Language, approved deployment/security policy, or acceptance criteria.

If planning reaches such a point, it emits a structured `HumanDecisionRequired` event.

### Director / planning intelligence

The Director may:
- interpret authorized requirements;
- identify ambiguity;
- decompose accepted requirements;
- form dependency DAGs;
- draft BIUs;
- select implementation sequencing from technical dependencies;
- identify required capabilities;
- identify verification obligations;
- propose provider/model routes;
- identify parallelizable work;
- recommend repair after failed verification;
- generate structured decision questions when authority is missing.

It may not:
- invent product priority;
- invent requirements;
- silently expand scope;
- choose an unresolved Founder decision;
- weaken architecture;
- reduce acceptance criteria to make implementation easier;
- turn a failed requirement into a different requirement.

### Deterministic kernel

The deterministic control plane owns canonical execution state, policy enforcement, lifecycle transitions, dependency enforcement, reservations, WIP, retries, cancellation, cost limits, capability grants, exact candidate identity, candidate custody, verification execution, evidence custody, result correlation, and closure eligibility.

> **Intelligence proposes; deterministic policy disposes.**

## BIU as compiled implementation contract

A mature BIU should contain:

- **Intent** — what is being built and why.
- **Satisfied requirements** — stable requirement IDs implemented by the BIU.
- **Fixed decisions** — technical/product/architecture decisions already made.
- **Boundaries** — what may and may not change.
- **Dependencies** — predecessor BIUs and external dependencies.
- **Required capabilities** — authority needed by the worker.
- **Budget** — time/token/cost limits.
- **Completion criteria** — observable deterministic scenarios defining implemented.
- **Verification obligations** — tests, architecture checks, static checks, API/browser/deployment checks.
- **Required evidence** — evidence needed before a verdict.
- **Non-goals** — explicitly excluded behavior.
- **Candidate custody requirements** — how the exact artifact is identified and made durably retrievable.
- **Release policy** — whether automatic release applies and any exceptional authorization required.

Agent-Ready determines whether a BIU can be executed without forcing the implementation agent to invent product or architecture decisions.

## Definition ≠ observation ≠ verdict

AlienIntent must permanently separate:

### Definition
What must be true: requirements, acceptance criteria, architecture rules, SLOs, compatibility requirements.

### Observation
Evidence about reality: exit codes, tests, changed files, exact SHA, workspace fingerprints, browser/API observations, deployment status, CI results.

An observation cannot declare PASS.

### Verdict
A policy decision derived from definitions plus trusted observations: requirement satisfied, verification failed, architecture violation, deployment healthy, ACCEPT / REJECT / BLOCKED.

> **Definition ≠ observation ≠ verdict.**

No worker self-report, completed task, or tool message may silently become a verdict.

## Factory yield

AlienIntent should treat engineering quality as a factory-yield problem.

Metrics should include:
- first-pass verification acceptance rate;
- average rework cycles per accepted BIU;
- requirement-coverage rate;
- architecture-violation rate;
- architecture violations caught before ACCEPT;
- drift detections;
- fake-DONE attempts prevented;
- verification failures by category;
- escaped defects discovered after acceptance;
- candidate-custody failures;
- retry rate;
- token/cost per accepted BIU;
- elapsed time per accepted BIU;
- provider/model performance by task class;
- context-policy effectiveness;
- intervention effectiveness;
- deployment verification success;
- backlog throughput;
- WIP utilization.

Long-term objective:

> **maximize accepted requirement-conformant software per unit of time/cost while minimizing rework, drift, fake completion, and escaped defects.**

## Human escalation

AlienIntent should emit a structured `HumanDecisionRequired` event only when continuing requires authority it does not have.

Each escalation should include:
- project;
- Work Item / BIU;
- exact decision required;
- why work cannot continue;
- options;
- material tradeoffs;
- recommendation;
- affected requirements;
- affected architecture;
- cost of waiting if material;
- what becomes authorized by each choice.

The Control Plane maintains a **Decision Inbox**.

Notification is an adapter concern: local Control Panel, CLI, email, Slack, Telegram, or other event-based channels.

No polling.

A response becomes a durable authority record/event and automatically unblocks affected work.

## READY scheduling and solve-for-N

AlienIntent does not choose product priority.

Priority comes from the authoritative Work Management system.

Default scheduling:
1. highest-priority eligible READY BIU first;
2. FIFO / next READY among equal or unprioritized BIUs;
3. blocked dependencies skipped;
4. respect WIP/capacity;
5. refill slots automatically when capacity opens.

Default WIP: **one active mutating work stream per project/repository unless configured otherwise.**

Architecture solves for N; larger deployments may increase WIP and execute independent BIUs concurrently.

## Ideas to borrow

### OpenAI Symphony
Borrow:
- continuous consumption of configured project work;
- long-running service rather than manual scripts;
- manage work rather than supervise agents;
- isolated workspace per item;
- issue/work source behind an adapter;
- proof-of-work expectations.

Adapt: AlienIntent extends farther upstream into requirements, planning, BIUs, and readiness.

### Orkestra
Borrow:
- deterministic kernel owns state and lifecycle;
- Director outputs structured/schema-validated proposals;
- isolated worktrees;
- independent review;
- deterministic verification;
- capability discovery/probes;
- evidence-based routing;
- bounded retries;
- token budgets;
- SQLite local state;
- scripted/fake agents for zero-cost orchestration tests.

Adapt: AlienIntent's Director has less authority over Founder/product/architecture decisions.

### watt-mind/factory
Borrow:
- rolling dispatch;
- immediate slot refill;
- control-plane adapter abstraction;
- repository-agnostic operations;
- safe concurrency default of one;
- triage/unblock/sweep/audit concepts;
- queue health / doctor;
- offline/demo mode.

Avoid making PRs/CI the universal control model.

### Dwarves Kit
Borrow:
- closed loop rather than self-grading open loop;
- Shape → Build → Watch → Check → Learn;
- hard gates mechanical;
- bounded repair loops;
- append-only ledgers;
- learning proposes changes rather than silently mutating policy.

> **Propose, never dispose.**

### ZhangHanDong/agent-spec
Borrow aggressively:
- intent compiler;
- structured requirements as IR;
- requirements dependency graph;
- requirements → work units;
- requirements → test obligations;
- Task Contract structure: Intent, Decisions, Boundaries, Completion Criteria;
- explicit test selectors / requirement-to-test binding;
- contract linting before implementation;
- mechanical boundary enforcement;
- ambiguity questions;
- implementation agents do not choose fixed technical decisions.

Adapt: BIU becomes AlienIntent's compiled bounded contract.

### yimwoo/agent-spec
Borrow:
- task completion is not outcome verification;
- typed outcome definitions;
- timestamped observations with provenance;
- observations cannot submit verdicts;
- policy computes verdicts.

### IronLaw
Borrow aggressively:
1. reduce rework;
2. prevent drift;
3. catch fake DONE.

Evidence should include tool events, exit codes, file changes, exact candidate identity, workspace fingerprints, real builds, CI, and final user/deployment journey.

Extend with:
4. enforce approved architecture;
5. mechanically verify requirement satisfaction;
6. independent verdict generation;
7. measure factory yield.

### Forgeo
Borrow:
- persistent backlog-driven execution;
- next runnable task automatically;
- dependency handling;
- continue past independent blocked work;
- retries;
- explicit BLOCKED reason;
- human notification;
- simple `init`, `validate`, `status`, `once`, `run`, `stop`, `restart`;
- backlog-provider adapters;
- no-PR workflow as legitimate;
- optional Docker sandbox.

Adapt: AlienIntent remains event-driven; polling is not canonical.

### AIWorkHub
Borrow:
- dependency-aware task DAG;
- durable context authorities;
- source intelligence / bounded code queries;
- model portfolio;
- route by capability, readiness, cost, observed quality;
- provider-free replay/testing;
- evidence-based review;
- repository isolation;
- retry/token economics.

Consider source intelligence later; do not block the minimum factory on it.

### Supaku AgentFactory
Borrow for Control Plane UX:
- fleet overview;
- active/queued/completed work;
- available capacity;
- cost;
- stage board;
- session table/timeline;
- token use;
- event history;
- integration health.

### Foundry
Borrow:
- persistent control plane;
- headless worker abstraction;
- deterministic anti-planner execution kernel;
- persist after meaningful steps;
- crash/restart recovery;
- deterministic local checks before model calls;
- bounded retries;
- context-loss protection;
- audit log;
- setup wizard;
- provider-health diagnostics.

Adapt: AlienIntent has a planning/compiler layer upstream; its execution kernel still behaves as an anti-planner.

## Minimum factory architecture

1. **Requirements Intake** — ports/adapters ingest authorized requirements and translate through ACLs.
2. **Intent / Requirements Compiler** — requirements IR, ambiguity questions, dependency graph, BIUs, test/architecture/evidence obligations.
3. **Scheduling / Factory Coordinator** — priority, dependencies, WIP, rolling refill, human-decision escalation.
4. **Deterministic Execution Kernel** — lifecycle, routing, context, capabilities, budgets, worktrees, candidate custody, retries, recovery.
5. **Verification / Acceptance** — requirements checks, architecture fitness, tests, independent review, evidence evaluation, bounded rework, closure eligibility.
6. **Evidence / Learning / Control** — Engineering Trajectory, Quality Evidence, yield, provider/context performance, failure taxonomy, community-learning proposals, Control Plane.


# Frontier creation-tool intake strategy

## Strategic conclusion

Frontier-model providers are rapidly moving upstream from "coding assistants" into **creation environments** where a human can express an idea conversationally and receive a functioning prototype, application, repository, worktree, artifact, or generated project.

AlienIntent should **not compete with those environments as the ideation UX**.

Instead, AlienIntent should treat them as interchangeable upstream creation surfaces:

```text
Human ideation
    ↓
frontier-provider creation environment
    ↓
prototype / repo / files / artifact / design / session evidence
    ↓
AlienIntent intake
    ↓
requirements + observations + provenance
    ↓
production architecture / BIUs
    ↓
software factory
    ↓
verified production software
```

This creates a strategically important role for AlienIntent:

> **Frontier creation tools become ideation/prototyping front ends; AlienIntent becomes the provider-neutral productionization factory downstream.**

The provider may change. The creation UI may change. The output format may change.

AlienIntent's durable value is taking an expression of product intent and converting it into governed, architecture-conformant, mechanically verified software.

## Current provider direction — September 2026

### Google AI Studio / Antigravity

Google AI Studio Build can generate full-stack web applications and native Android applications from natural-language prompts, exposes generated source, supports two-way GitHub synchronization, and supports ZIP export for external development.

Google has also converged its agent harness around Antigravity. The Antigravity agent is available programmatically through the Gemini Interactions API with sandboxed code execution and filesystem access.

Strategic implication:

- Git repositories are already a stable handoff surface.
- ZIP/project export is a second stable handoff surface.
- Provider APIs may eventually supply richer machine-readable provenance and interaction state.
- AlienIntent should not depend on undocumented AI Studio internals.

### OpenAI Codex / ChatGPT Work

Codex increasingly operates on projects, repositories, worktrees, skills, and long-running tasks. It can create and manipulate code directly in local/project workspaces rather than emitting only chat text.

Strategic implication:

- AlienIntent should ingest source-control state and task artifacts rather than require a special "Codex export."
- A branch/commit/worktree result can be treated as an externally created prototype/candidate source with provenance.
- Provider-specific task/session metadata is optional enrichment, not core authority.

### Anthropic Claude Artifacts / Claude Code

Claude Artifacts converts conversational intent into interactive apps and versioned code artifacts. Anthropic explicitly positions Artifacts as rapid prototyping and Claude Code as the path toward more production-grade implementation.

Strategic implication:

- Some provider creation environments will expose code only through copy/export rather than a stable source-control API.
- AlienIntent therefore needs file/archive intake in addition to Git intake.
- Artifact/share URLs can be accepted as provenance/reference when a stable retrieval API is available, but screen scraping must not be a canonical integration.

## Core strategy: provider-neutral Artifact Intake

AlienIntent should introduce a provider-neutral input boundary for externally created product artifacts.

"Artifact Intake" is a working architecture label, not yet a binding Ubiquitous Language term.

The intake boundary must support at least:

1. **Git source**
   - repository;
   - branch;
   - exact commit;
   - optional pull/merge request reference.

2. **Project archive**
   - ZIP/tar/project export;
   - immutable content hash;
   - preserved original bundle.

3. **Loose files**
   - source files;
   - design files;
   - requirements documents;
   - screenshots;
   - generated assets.

4. **Prototype/reference URL**
   - live preview;
   - shared artifact;
   - hosted prototype;
   - optional provider-native project URL.

5. **Structured provider API**
   - only where the provider exposes a stable supported API;
   - adapter-specific;
   - never required by the core domain.

6. **Optional session/intention evidence**
   - originating prompt;
   - follow-up prompts;
   - provider/model/version;
   - timestamps;
   - tool/session metadata where exportable.

## Three intake modes

Externally generated artifacts must not all have the same authority.

AlienIntent should distinguish three user-intent modes.

### 1. Intent / prototype input

Meaning:

> "This prototype expresses what I want."

AlienIntent extracts:

- observable product behavior;
- user journeys;
- apparent requirements;
- data concepts;
- interaction semantics;
- design constraints;
- assets;
- unresolved ambiguity.

The imported implementation is **evidence of intent**, not automatically approved architecture or production code.

This is the primary expected mode for Google AI Studio / Claude Artifacts / similar future tools.

### 2. Candidate implementation input

Meaning:

> "Treat this generated code as a starting implementation candidate."

AlienIntent may preserve and analyze the source, but it still must pass through:

- architecture conformance;
- requirement traceability;
- deterministic verification;
- security/quality checks;
- independent verdict;
- normal candidate custody and acceptance.

Externally generated code does not bypass the factory because it happens to run.

### 3. Reference input

Meaning:

> "Use this for inspiration/context only."

The artifact may inform planning/context but creates no requirement and grants no implementation authority.

## Authority rule

Imported provider output is never automatically canonical product truth.

AlienIntent must preserve the distinction between:

- **authorized human intent**;
- **provider inference**;
- **observable prototype behavior**;
- **generated implementation detail**.

The intake process may draft requirements from imported artifacts, but only the configured authority mechanism can promote those drafts to governed requirements.

This is the same principle as:

> **definition ≠ observation ≠ verdict**

A prototype is principally an observation of one possible interpretation of intent.

It may also contain explicit definitions if the human deliberately submitted them as requirements.

AlienIntent must not silently collapse those categories.

## Executable intent

A functioning prototype can be more informative than a prose requirement because it expresses:

- interactions;
- visual behavior;
- navigation;
- data entry;
- workflow;
- timing;
- error paths;
- terminology.

AlienIntent should therefore support **behavior extraction** from a prototype as a requirements-assistance mechanism.

However:

> **Prototype behavior is not automatically a production requirement.**

The system should produce a structured gap report:

- behaviors observed;
- inferred requirements;
- ambiguities;
- contradictions;
- missing nonfunctional requirements;
- architecture conflicts;
- security/privacy assumptions;
- persistence assumptions;
- provider-specific dependencies;
- generated-code shortcuts;
- unresolved product decisions.

That gap report is then used by the Requirements Compiler.

## Provider-specific code must be treated as untrusted input

Creation environments often optimize for demonstration speed, not the target system's architecture or operational requirements.

AlienIntent must assume imported generated code may contain:

- provider-specific APIs;
- hidden runtime assumptions;
- embedded deployment bindings;
- weak persistence choices;
- generated secrets/configuration;
- prototype-only dependencies;
- architecture violations;
- unbounded external calls;
- incomplete error handling;
- missing tests;
- convenience authentication;
- accidental licensing/dependency implications.

Therefore ingestion must never mean "merge this into production."

It means:

> **capture → fingerprint → inspect → extract intent → reconcile → plan → verify.**

## Provenance requirements

Every imported artifact must retain provenance sufficient to reproduce what entered the factory:

- source type;
- provider when known;
- provider product/surface when known;
- import timestamp;
- source URL/repository where applicable;
- exact commit or immutable archive hash;
- originating user/authority;
- import mode;
- optional provider/model/version;
- optional prompt/session export;
- original artifact retained according to retention policy.

The normalized representation must point back to the immutable original.

## Stable integration surfaces first

AlienIntent must prefer durable handoff mechanisms over UI automation.

Integration priority:

1. Git repository / exact commit;
2. exported archive/files;
3. supported provider API;
4. provider-native share/project reference;
5. browser/UI extraction only as an explicit noncanonical exception.

Do not build core architecture around scraping Gemini Studio, Codex, Claude, or any provider UI.

Provider product surfaces will change faster than AlienIntent should.

## Anti-Corruption Layer requirement

Each provider-specific creation tool is an external bounded system.

Adapters/ACLs translate provider concepts into AlienIntent's generic intake model.

Examples:

```text
GoogleAIStudioAdapter
CodexProjectAdapter
ClaudeArtifactAdapter
GenericGitArtifactAdapter
GenericArchiveArtifactAdapter
```

These names are illustrative, not binding class names.

No provider-native concept belongs in AlienIntent's core domain model.

## Relationship to Requirements IR

Artifact Intake should feed the Requirements IR rather than bypass it.

Target flow:

```text
External creation artifact
        ↓
immutable intake snapshot + provenance
        ↓
observations / extracted behavior
        ↓
draft requirement candidates + ambiguity report
        ↓
authority/promotion
        ↓
governed Requirements IR
        ↓
Requirements → BIU compiler
        ↓
factory
```

This architecture also allows a future fully machine-mediated path when authority policy permits automatic promotion for sufficiently bounded classes of work.

## Relationship to externally generated code

When code is supplied:

```text
external code
    ↓
immutable source snapshot
    ↓
source intelligence / architecture analysis
    ↓
requirements comparison
    ↓
decision:
    ├── reuse portions
    ├── refactor/productionize
    └── discard implementation, preserve behavior/intent
```

The generated code is an input asset, not architectural authority.

## Priority

This capability is strategically important but must **not interrupt Wave 1**.

Implementation sequencing:

- Wave 1 remains unchanged: finish the continuous autonomous factory loop.
- Requirements IR and Requirements → BIU compilation remain the first part of Wave 2.
- **Artifact Intake follows the core Requirements IR and BIU compiler as Wave 2B.**
- A minimal generic Git/archive intake can be implemented before provider-specific adapters.
- Provider-specific adapters are added only when a stable supported handoff mechanism materially improves the generic path.

Reason:

Without Requirements IR, AlienIntent has nowhere clean to put the meaning extracted from a provider prototype.

Without the continuous factory, intake merely creates more work that still requires manual execution.

Therefore the correct order is:

```text
continuous factory
    ↓
Requirements IR / BIU compiler
    ↓
generic Artifact Intake
    ↓
provider-specific adapters
    ↓
advanced behavioral extraction / prototype verification
```

## New Product Requirements

### SF-REQ-041 — External creation artifact intake
**Priority:** P1 — Wave 2B

AlienIntent accepts externally created product artifacts through a provider-neutral intake boundary.

Minimum supported forms:
- Git repository/branch/commit;
- archive/project export;
- loose files;
- reference URL with explicit provenance.

Provider-native concepts remain outside the core domain.

### SF-REQ-042 — Immutable intake snapshot and provenance
**Priority:** P1 — Wave 2B

Every imported artifact is fingerprinted and preserved as an immutable input snapshot with provenance sufficient to identify exactly what entered the factory.

### SF-REQ-043 — Intake authority modes
**Priority:** P1 — Wave 2B

AlienIntent distinguishes at least:
- intent/prototype input;
- candidate implementation input;
- reference-only input.

The selected mode controls what authority may be derived from the artifact.

### SF-REQ-044 — Prototype-to-requirements extraction
**Priority:** P1 — Wave 2B

AlienIntent can derive structured requirement candidates, observed behaviors, workflows, terminology, ambiguity, and missing nonfunctional requirements from an imported prototype or generated project.

Derived requirements are drafts until promoted by configured authority.

### SF-REQ-045 — External generated-code productionization
**Priority:** P2

When imported artifacts include code, AlienIntent can evaluate that code against governed requirements and target architecture and determine whether to reuse, repair/refactor, or discard it while preserving useful intent/behavior.

Externally generated code never bypasses normal verification and acceptance.

### SF-REQ-046 — Creation-tool adapters
**Priority:** P2

AlienIntent supports provider-specific adapters for stable supported export/API surfaces while retaining generic Git/archive/file intake as the compatibility baseline.

Initial research targets:
- Google AI Studio / Antigravity;
- OpenAI Codex / ChatGPT Work;
- Anthropic Claude Artifacts / Claude Code.

### SF-REQ-047 — Prototype behavioral verification
**Priority:** P2

Where a prototype is executable, AlienIntent may capture user-visible behavior and use it as an observation source for requirement drafting and later conformance comparison.

Observed prototype behavior is never automatically promoted to a requirement.

## Wave 2B — Frontier creation-tool intake

Requirements:

- SF-REQ-041
- SF-REQ-042
- SF-REQ-043
- SF-REQ-044

Outcome:

> A user can ideate/prototype in a frontier-model creation environment, hand the resulting artifact to AlienIntent through a stable generic handoff, and have AlienIntent convert it into governed requirement candidates without treating provider-generated code or inferred behavior as authoritative.

Provider-specific productionization work follows under SF-REQ-045 through SF-REQ-047.

## Strategic product consequence

AlienIntent should not need to win the "best vibe-coding studio" market.

If Google, OpenAI, Anthropic, or another frontier provider creates a better ideation tool, that should make AlienIntent more useful, not less.

The durable position is:

> **Create anywhere. Productionize through AlienIntent.**

This makes provider innovation an upstream supply of better intent/prototype artifacts rather than a direct threat to the software factory.


## Implementation priority

### Priority 0 — Factory control loop
Goal: continuously consume prioritized READY BIUs and execute through DONE without human per-BIU relay.

### Priority 1 — Requirements → BIU compiler
Goal: product requirements, not hand-written BIUs, become the normal input.

### Priority 2 — Verification / yield
Goal: mechanically prove requirements and architecture rather than trust agent claims.

### Priority 3 — Provider economics / context efficiency
Goal: lower cost while preserving accepted quality.

### Priority 4 — Learning loop
Goal: evidence improves proposals/policy without self-corrupting autonomous mutation.

### Priority 5 — Installation / operator experience
Goal: make the factory easy to install, inspect, control, and diagnose.

# Product Requirements Backlog

These are Product Requirements, not implementation BIUs.

## SF-REQ-001 — Continuous factory execution
**Priority:** P0

Given a populated backlog with eligible READY BIUs, AlienIntent continuously executes work until the eligible backlog is exhausted, blocked, or requires human authority. No human per-BIU trigger.

## SF-REQ-002 — READY scheduling
**Priority:** P0

Select next eligible READY BIU by external priority, then FIFO among equals/unprioritized, subject to dependencies and WIP. AlienIntent never invents product priority.

**Amendment (2026-09-21, [SWF-21 release admission](2026-09-20-wave1-release-coordinator.md)) — admission preconditions.** Eligibility selects *which* BIU is next; admission decides whether it may enter IMPLEMENT at all. Before any READY/TASKS → IMPLEMENT release, and **before any worker is launched**, all of the following must hold, mechanically where possible:

1. implementation is **explicitly authorized** by a durable release record;
2. that record identifies the **exact baseline** revision;
3. the baseline **resolves to a real repository revision**;
4. the baseline is **compatible with — reachable from — the intended release point** as policy requires;
5. **stale Issue wording stating that implementation is unauthorized cannot coexist with an authorized release** without an explicit superseding record;
6. no worker is launched until these checks pass.

A failed check is a refusal to transition, not a warning. This does not replace Agent-Ready or the dependency/WIP conditions; it is the record-completeness gate in front of them.

**Dependency satisfaction is a lifecycle question ([SWF-31](2026-09-20-wave1-closure-policy.md)).** The bootstrap evaluates it through GitHub's native blocked-by links, which read Issue state — a **projection** the control plane writes to, not lifecycle authority. Project `DONE` is the authoritative state. Canonical Python must evaluate dependency satisfaction against lifecycle state it owns, never against a secondary projection that can lag or be edited externally.

## SF-REQ-003 — Solve for N
**Priority:** P0

Support configurable concurrent work streams. Default one active mutating stream; independent work may run concurrently when policy allows.

## SF-REQ-004 — Rolling slot refill
**Priority:** P0

When capacity opens, automatically select/release the next eligible READY BIU.

## SF-REQ-005 — Work Management abstraction
**Priority:** P0

Read upstream work, priority, and dependencies through a Work Management port. GitHub Projects is the first adapter; the core does not depend on GitHub concepts.

## SF-REQ-006 — Human decision escalation
**Priority:** P0

When authority is missing, emit a structured HumanDecisionRequired event and block only affected work. Independent work continues.

## SF-REQ-007 — Candidate custody invariant
**Priority:** P0

Never enter VERIFY until the exact candidate is durably identifiable and retrievable by a fresh independent verifier. Enforce in the control plane, not worker instructions.

**Amendment (2026-09-20, [SWF-30](2026-09-20-candidate-worktree-retention.md)) — local working copy as operational cache.** Custody is satisfied by the durable published identity, not by the local working copy that produced it. A local candidate worktree is therefore **not itself required evidence** once all of: (1) the exact candidate identity is known; (2) the candidate commit/artifact is durably published; (3) that identity is independently retrievable; (4) read-back confirms the published identity/content; (5) no active invocation uses the worktree; (6) no uncommitted unique content exists; (7) no explicit BIU or evidence policy requires local retention. When all seven hold, the worktree is operational cache and may be removed as routine cleanup.

"Durably published" means the candidate remains reachable through a remote reference or other repository object whose **retention is at least as strong as the applicable evidence-retention obligation**; a transient remote branch about to be deleted does not qualify merely because the commit currently exists on the remote. Failing any condition means retention. This amendment does not weaken conditions 1–4 — it consumes that proof — and it never authorizes deleting the only durable copy of anything, nor any evidence object, trajectory or accepted result. Architecture Authority §26 evidence retention is cross-referenced and unchanged.

## SF-REQ-008 — Crash-safe execution
**Priority:** P0

Preserve canonical execution state across crashes/restarts and prevent duplicate effects using the approved inbox/effect-intent/outbox, version, fencing, idempotency, and reconciliation model.

## SF-REQ-009 — Deterministic execution kernel
**Priority:** P0

Lifecycle, policy, reservations, WIP, retries, capabilities, budgets, candidate identity, and verdict admissibility are deterministic. No LLM owns canonical execution state.

**Amendment (2026-09-21, [SWF-32](2026-09-21-biu-execution-cycle-counter.md)) — BIU execution cycle counter.** The kernel maintains a durable per-BIU **execution cycle number** after release, deterministic and reconstructible like the candidate identity it sits beside. The first authoritative transition into `IMPLEMENT` establishes cycle 1; every later authoritative transition into `IMPLEMENT` from another lifecycle state — including authorized `ACCEPT → IMPLEMENT` rework — increments by exactly one; `VERIFY` inherits the cycle and never increments it; `ACCEPT`/`DONE` retain it as history. Retry, restart, provider failover or a replacement worker within the same phase does not increment, a verifier restart within `VERIFY` does not increment, liveness recovery or replay of the same state does not increment, and duplicate delivery of one transition must not increment twice. Restart, replay and reconciliation preserve or deterministically reconstruct the same value.

**Cycle count is not invocation count.** A cycle is a lifecycle fact; an invocation attempt is a worker fact; neither is derivable from the other. Worker invocations remain separately identifiable, and trajectory must represent BIU → cycle → invocation attempts. The cycle is projected to the configured Work Management provider for operator visibility (FD-01 direction only — a projected field is never execution authority), and is **evidence, not a verdict**: SF-REQ-024, SF-REQ-029, SF-REQ-034, SF-REQ-049 and SF-REQ-052 consume it; none of them owns it.

**Not retrofitted.** This adds no obligation to the Node bootstrap or to any released BIU, and carries **no Priority or Wave assignment** — the implementation obligation is unscheduled until the Founder assigns one.

## SF-REQ-010 — BIU contract model
**Priority:** P0

BIUs have machine-readable Intent, requirement links, fixed decisions, boundaries, dependencies, capabilities, budget, completion criteria, verification obligations, evidence obligations, non-goals, candidate custody, and release policy.

## SF-REQ-011 — Requirements IR
**Priority:** P1

Represent authorized requirements independently of GitHub/Jira/document formats, with stable IDs, provenance, status, dependencies, and traceability to BIUs.

## SF-REQ-012 — Requirements ambiguity detection
**Priority:** P1

Detect missing authority or ambiguity before implementation and emit structured questions rather than allowing implementation agents to improvise.

## SF-REQ-013 — Requirements → BIU compilation
**Priority:** P1

Lower governed requirements into bounded BIUs with explicit requirement-satisfaction links and dependency DAGs.

## SF-REQ-014 — Mechanical test obligations before implementation
**Priority:** P1

Where mechanically testable, derive verification/test obligations before implementation. Implementation code cannot be the sole source of its own acceptance tests.

## SF-REQ-015 — BIU lint/readiness
**Priority:** P1

Check BIUs for unresolved decisions, incomplete boundaries, missing acceptance/verification obligations, architecture constraints, and dependency problems. Agent-Ready remains execution-readiness authority.

## SF-REQ-016 — Definition / Observation / Verdict separation
**Priority:** P1

Store definitions, observations, and verdicts separately. Observations cannot declare verdicts; worker claims cannot become PASS without policy/evidence evaluation.

## SF-REQ-017 — Requirement-evidence traceability
**Priority:** P2

Every requirement claimed satisfied has traceable evidence. Missing evidence yields UNVERIFIED/BLOCKED/REJECT, not DONE.

## SF-REQ-018 — Architecture conformance
**Priority:** P2

Mechanically enforce approved architecture where possible. Architecture violations block acceptance; fitness checks require negative controls proving they can fail.

## SF-REQ-019 — Drift detection
**Priority:** P2

Detect material divergence between implementation trajectory and authorized BIU intent/boundaries; trigger correction or escalation.

## SF-REQ-020 — Fake-DONE prevention
**Priority:** P2

Never accept natural-language claims like "tests passed" or "done" as delivery facts. Completion must be evidence-backed.

## SF-REQ-021 — Independent verification
**Priority:** P2

Review candidates in an independent invocation/workspace/context; no self-approval. Stronger model/provider separation remains configurable.

## SF-REQ-022 — Bounded repair loops
**Priority:** P2

Verification rejection returns to implementation with findings. Repair loops have bounded retries/budgets; exhaustion escalates instead of consuming indefinitely.

## SF-REQ-023 — Product/outcome verification
**Priority:** P2

Task completion is distinct from product/release/deployment outcome verification. Support typed command, API compatibility, browser journey, deployment, SLO, and release outcomes.

## SF-REQ-024 — Factory yield metrics
**Priority:** P2

Measure first-pass acceptance, rework, drift, fake-DONE prevention, architecture catches, requirement coverage, escaped defects, cost, latency, and provider/model performance.

## SF-REQ-025 — Provider capability discovery
**Priority:** P3

Provider adapters expose capabilities and authenticated readiness; routing cannot assume provider equivalence.

## SF-REQ-026 — Cheapest-capable routing
**Priority:** P3

Select the cheapest provider/model demonstrated capable of meeting the quality bar; prefer capable local models.

## SF-REQ-027 — Source intelligence
**Priority:** P3

Support provider-neutral structural source intelligence for bounded relevant code context. Optimization, not minimum-factory prerequisite.

## SF-REQ-028 — Execution economics
**Priority:** P3

Record token/cost/time per attempt and accepted BIU, including retries. Cheap failed runs are not economic success.

## SF-REQ-029 — Engineering Trajectory
**Priority:** P4

Record observable engineering trajectory independent of Git commits: actions, artifacts, checks, findings, repairs, policy/context versions, cost, outcomes. No private chain-of-thought required.

Trajectory observations may carry versioned, evidence-backed failure classifications where supported: behavioral defect, evidence/proof defect, custody/identity defect, tooling/publication defect, process-instruction adherence, genuine authority required, false/escalated authority request, and provider-capacity interruption. Classification describes observed evidence and does not itself declare a verdict.

## SF-REQ-030 — Quality Evidence
**Priority:** P4

Derive durable Quality Evidence from trajectories; raw observation and learned hypothesis remain distinct.

Derived evidence identifies its source trajectory/schema version and explicit evidence inputs. Where facts permit, aggregate metrics reconcile against those sources, including verifier cycles, RETURN_TO_IMPLEMENT, classified rejections, authority decisions, attributable human-blocked duration, candidate/merge identity, final verdict/landed/DONE and timestamp relationships. UNKNOWN or partial telemetry is never silently converted to zero. Contradictory derived evidence fails deterministic consistency verification.

The deterministic consistency verification must itself carry discriminating negative-control / proven-red evidence where practical: altering a derived count, substituting zero for UNKNOWN telemetry without evidence, or introducing an impossible timestamp relation must cause the applicable check to fail. A consistency check that cannot fail is not evidence (SWF-24). Folded from PROP-2026-0004 by Founder decision of 2026-09-20; SF-REQ-030 is the canonical owner of Execution Evidence Derivation and Consistency Verification.

## SF-REQ-054 — retired: folded into SF-REQ-030

**Status:** retired 2026-09-20 by Founder decision. Not an active requirement; the ID is not reused.

Execution Evidence Derivation and Consistency Verification is owned canonically by **SF-REQ-030** above, which was amended to carry this capability including the discriminating negative-control obligation. Origin [PROP-2026-0004](../proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md) is preserved unchanged as provenance; [Issue #65](https://github.com/AlienLogicLab/alienintent/issues/65) is closed as duplicate/superseded.

## SF-REQ-055 — Proposal Intake as a Product Capability
**Priority:** P1
**Wave:** 3
**Authority:** ratified as product authority by Founder decision of 2026-09-20.

AlienIntent accepts proposals as immutable, noncanonical provenance until admitted through applicable authority; validates, classifies, deduplicates, resolves authority, canonicalizes into the appropriate artifact and durably maps proposal to canonical work. `proposal_id` provides idempotency, duplicate delivery creates no duplicate canonical work, and canonical artifacts own current state. Intake is provider-neutral; repository-backed `docs/proposals/` is an adapter. Intake cannot invent priority, Wave, product/architecture authority or create a BIU by receipt.

Canonical Product Requirement: [Issue #66](https://github.com/AlienLogicLab/alienintent/issues/66), CAPTURE. Origin: PROP-2026-0005.

## SF-REQ-031 — Evidence-derived routing learning
**Priority:** P4

Improve routing recommendations from observed task/provider/model outcomes while remaining task/model/version aware.

## SF-REQ-032 — Learning proposals, not autonomous policy mutation
**Priority:** P4

Learning produces cited policy/routing/context proposals; no proposal becomes active without configured promotion authority.

## SF-REQ-033 — Community learning
**Priority:** P4

Opt-in contribution of generalized/anonymized quality/provider evidence without requiring proprietary code, secrets, or sensitive project content.

## SF-REQ-034 — Operator Control Plane
**Priority:** P0 minimum / P5 polish

Provide status, explain, emit legitimate events, replay, resume, reconcile, cancel, doctor, and inspection of BIUs, workers, events, evidence, cost, capabilities, transport, and adapters. Operator events use normal domain/event paths.

## SF-REQ-035 — Decision Inbox
**Priority:** P0

HumanDecisionRequired events appear in one operator surface with enough context to decide without reconstructing agent history; decisions are durable and automatically unblock work.

## SF-REQ-036 — Factory dashboard
**Priority:** P5

Show active/queued/completed work, WIP/capacity, workers, provider/model, BIU, stage, elapsed time, cost, event timeline, blocked decisions, integration health.

## SF-REQ-037 — Installer
**Priority:** P0 minimum / P5 polish

`alienintent init` configures a normal self-hosted installation with convention-heavy defaults and discovers what can be discovered.

## SF-REQ-038 — Doctor / validation
**Priority:** P0

Validate installation, work-management access, provider readiness, source-control access, transport health, lifecycle mapping, persistence, and execution capability before autonomous work begins.

## SF-REQ-039 — Fake-agent/offline factory proof
**Priority:** P1

Support deterministic scripted/fake workers that exercise the real factory lifecycle without provider credentials or token spend.

## SF-REQ-040 — Provider-free replay
**Priority:** P2/P4

Replay recorded events/evidence for recovery, debugging, and deterministic policy testing without recalling model providers where outputs are already captured.

# Initial implementation waves

## Wave 1 — Make the factory run continuously
Requirements: SF-REQ-001 through SF-REQ-010, SF-REQ-034, SF-REQ-035, SF-REQ-038.

Outcome: a prioritized READY backlog runs continuously through the existing execution machinery, refills capacity, preserves state, and stops only on real authority blockers.

Clarification (Founder decision, 2026-09-19): "existing execution machinery" means the current Node bootstrap may execute the BIUs that build Wave 1. It does not mean implementing Wave 1 factory capabilities in Node. Wave 1 is implemented in the canonical Python AlienIntent architecture; Node changes remain limited to critical bootstrap repairs under Architecture Authority §42. See [the Wave 1 Founder decisions](2026-09-19-software-factory-wave1-founder-decisions.md).

## Wave 2 — Requirements become the normal input
Requirements: SF-REQ-011 through SF-REQ-016, SF-REQ-039.

Outcome: authorized requirements compile into Agent-Ready BIUs with deterministic completion/test obligations.

## Wave 2B — Frontier creation-tool intake
Requirements: SF-REQ-041 through SF-REQ-044.

Outcome: prototypes and generated projects from frontier-provider creation environments can become governed requirement candidates through provider-neutral intake without bypassing AlienIntent authority.

## Wave 3 — Raise factory yield
Requirements: SF-REQ-017 through SF-REQ-024, SF-REQ-040, plus SF-REQ-045 through SF-REQ-047 where applicable.

Outcome: requirement satisfaction, architecture adherence, drift, fake-DONE, rework, and product outcomes become evidence-backed and measurable.

## Wave 4 — Reduce cost
Requirements: SF-REQ-025 through SF-REQ-028.

Outcome: provider/model/context choices optimize cost while preserving accepted quality.

## Wave 5 — Learn
Requirements: SF-REQ-029 through SF-REQ-033.

Outcome: real execution evidence produces quality/routing/context proposals without uncontrolled policy mutation.

## Wave 6 — Productize installation and operations
Requirements: SF-REQ-036, SF-REQ-037, advanced Control Plane UX.

Outcome: a new user installs and operates the factory without reproducing bootstrap pain.

# Source projects / design references

Idea sources, not dependencies:

- OpenAI Symphony — https://github.com/openai/symphony
- Orkestra — https://github.com/andyyaro/orkestra
- watt-mind/factory — https://github.com/watt-mind/factory
- dwarves-kit — https://github.com/dwarvesf/dwarves-kit
- ZhangHanDong/agent-spec — https://github.com/ZhangHanDong/agent-spec
- yimwoo/agent-spec — https://github.com/yimwoo/agent-spec
- IronLaw — https://github.com/Porphyrioon/ironlaw
- Forgeo — https://github.com/lucaGazzola/forgeo
- AIWorkHub — https://github.com/shrec/AIWorkHub
- Supaku AgentFactory — https://github.com/LiteTrackerApp/agentfactory
- Foundry — https://github.com/ai-supervisor-foundry/foundry

Additional current creation-tool research:
- Google AI Studio Build — https://ai.google.dev/gemini-api/docs/aistudio-build-mode
- Google Antigravity Agent — https://ai.google.dev/gemini-api/docs/antigravity-agent
- OpenAI Codex app — https://openai.com/index/introducing-the-codex-app/
- Anthropic Claude Artifacts — https://support.anthropic.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them

Borrow ideas. Do not copy architecture blindly. Every borrowed idea must be reconciled against AlienIntent DDD, Hexagonal Architecture, EOS, Founder decisions, and evidence.
