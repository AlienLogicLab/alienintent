# AlienIntent / Agent Ready — Founder Architecture Decisions and Ubiquitous Language v0.1

## Status

Founder-approved architecture direction, pending canonicalization into the appropriate AlienIntent and Agent Ready decision/architecture artifacts.

This document makes durable the decisions reached after the Post-Wave-1 programme and corrects terminology that had drifted across product boundaries.

It is intentionally written for **N projects**, not for FactoryChecks or AlienIntent self-hosting specifically.

AlienIntent is currently building itself. Its next major project is expected to be FactoryChecks. Future projects may be greenfield, brownfield, maintenance-heavy, migration-heavy, feature-driven, research-heavy, or combinations of these.

No design here may assume AlienIntent is the only project, FactoryChecks is the only consumer, GitHub is the only work-management system, or one model/provider is permanently preferred.

---

# 1. Terminology correction: Agent Ready does not have BLOCKED

Agent Ready has exactly four semantic assessment dispositions:

- READY
- CLARIFY
- SPLIT
- HOLD

`BLOCKED` is not an Agent Ready disposition.

Where historical AlienIntent or Project state uses terms such as BLOCKED, TASKS, READY, IMPLEMENT, or similar, those are **AlienIntent / work-management lifecycle or planning states**, not Agent Ready dispositions.

The correct language for a work unit whose external prerequisite is not currently satisfied is:

> Agent Ready disposition: HOLD

If a Project item or AlienIntent plan separately records that work as blocked by a dependency, that is a different fact in a different bounded context.

**Invariant:** Never project AlienIntent or Work Management lifecycle vocabulary back into Agent Ready's assessment vocabulary.

Likewise: Agent Ready disposition is an assessment result, not a lifecycle state.

---

# 2. Agent Ready remains an independent product and bounded context

Agent Ready remains independently maintained and independently deployable.

Current intended product boundary:

- separate repository;
- installable independently of AlienIntent;
- local-first;
- public CLI;
- local MCP interface;
- one shared core assessment engine behind both interfaces;
- provider-neutral;
- no implementation authority;
- no work-management mutation authority;
- no AlienIntent dependency.

Agent Ready owns:

- readiness semantics;
- READY / CLARIFY / SPLIT / HOLD meaning;
- semantic cohesion analysis;
- decision-center analysis;
- owner-ambiguity analysis;
- prerequisite analysis;
- rework-locality analysis;
- readiness explanation;
- split recommendation boundaries;
- canonical assessment contract/schema;
- CLI behavior;
- MCP behavior;
- supported provider adapters;
- versioning and backward compatibility of the public assessment contract.

AlienIntent must consume Agent Ready only through Agent Ready's supported public contract.

No AlienIntent private import of Agent Ready internals. No duplicated readiness rubric inside AlienIntent. No copied Agent Ready decision logic.

---

# 3. Historical Agent Ready assessments are immutable evidence

An Agent Ready assessment is a historical fact:

> At time T, Agent Ready version V, using assessment contract/schema S, assessed input identity I, through provider/model provenance P, and returned disposition D with explanation E.

That record must not be rewritten merely because Agent Ready later changes its schema or improves its reasoning.

Required policy:

- preserve the raw original assessment;
- preserve schema/version identity;
- preserve Agent Ready version;
- preserve provider/model provenance where available;
- preserve input identity/fingerprint;
- preserve timestamp;
- preserve the original disposition and explanation;
- never silently recast an old disposition into a new one.

Schema evolution should use backward-compatible readers, versioned compatibility adapters, or read-time projection into a current internal representation.

Do not rewrite historical raw assessments.

If an assessment artifact is genuinely corrupt, correction must preserve the original and correction provenance.

---

# 4. Agent Ready feedback corpus and learning responsibility

Agent Ready should eventually maintain a versioned corpus linking assessments to real downstream outcomes.

Example feedback relationships:

- READY -> first-pass implementation success
- READY -> repeated repair
- READY -> later decomposition failure
- SPLIT -> split proved useful
- SPLIT -> split later proved unnecessary
- CLARIFY -> question materially changed implementation
- CLARIFY -> question proved unnecessary
- HOLD -> prerequisite genuinely prevented execution
- HOLD -> prerequisite was not actually required

This corpus exists to improve future readiness assessment.

## Gentleman’s agreement

The **consumer/user of Agent Ready is responsible for supplying outcome feedback** when downstream evidence becomes available.

Agent Ready cannot infer the truth of execution outcomes from projects it does not control.

Therefore:

> Agent Ready provides a feedback contract; consumers provide attributable assessment-outcome feedback.

For AlienIntent, feedback should be emitted as part of normal execution/evidence closure rather than as an ad hoc manual activity.

The exact workflow location must be designed, but the likely lifecycle is:

Agent Ready assessment -> AlienIntent execution / verification / acceptance -> durable outcome evidence -> assessment-outcome feedback adapter -> Agent Ready corpus intake.

Agent Ready must not autonomously mutate its readiness rules from individual feedback events.

Improvement remains governed:

evidence -> candidate lesson -> evaluation -> versioned rule/prompt/model change -> independent validation -> release.

---

# 5. Agent Ready owns split judgment; AlienIntent owns split/replan mutation

Two responsibilities must remain distinct.

## Agent Ready owns semantic judgment

Agent Ready decides whether a proposed work unit is cohesive, materially ambiguous, blocked by a prerequisite, or composed of independent decision centers.

When it detects independent decision centers, it returns `SPLIT` with recommended semantic boundaries.

Agent Ready does NOT rewrite AlienIntent plans, Project items, dependencies, requirements, or BIUs.

## AlienIntent owns authority-bearing mutation

AlienIntent's Requirements / Planning bounded context owns:

- requirement interpretation under existing authority;
- specification;
- design inputs;
- planning;
- requirement-to-BIU compilation;
- dependency construction;
- authoritative split/replan transaction;
- requirement/obligation conservation;
- lineage;
- reassessment invalidation;
- integration-parent semantics where required;
- updated plan materialization.

The boundary is:

> Agent Ready gives the judgment. AlienIntent performs the authority-bearing mutation.

---

# 6. Recommended bounded-context architecture

## Agent Ready bounded context

Core question:

> Is this proposed work unit sufficiently understood, cohesive, constrained, and verifiable to hand to an autonomous implementation agent?

Primary language:

- assessment
- work unit
- disposition
- readiness
- owner question
- engineering unknown
- prerequisite
- independent decision center
- rework locality
- READY
- CLARIFY
- SPLIT
- HOLD

Agent Ready does not own requirement authority, planning authority, lifecycle mutation, work allocation, execution, verification, acceptance, repository mutation, or Project mutation.

## AlienIntent Requirements / Planning bounded context

Core invariant:

> Authorized product intent must be converted into executable work without losing, inventing, weakening, or silently reallocating obligations.

Primary responsibilities:

- ingest requirements from multiple sources;
- normalize external source representation into AlienIntent's internal requirements model;
- preserve source identity/provenance;
- distinguish proposal, requirement, specification, design, and plan;
- compile authorized requirements into candidate BIUs;
- invoke Agent Ready through a port;
- respond to READY / CLARIFY / SPLIT / HOLD;
- perform split/replan transactions;
- conserve all obligations;
- create/update dependency DAG;
- produce candidate Wave plan;
- prepare work for release.

This bounded context should exist even if deployed in the same Python process as other AlienIntent contexts.

DDD bounded context does not imply network service or microservice.

---

# 7. Hexagonal integration with Agent Ready

AlienIntent depends on an abstract readiness port, not Agent Ready implementation details.

Conceptually:

AlienIntent Requirements / Planning -> ReadinessAssessmentPort -> CLI Adapter or MCP Adapter -> Agent Ready.

Possible domain-facing contract:

`assess(candidate_work_unit) -> ReadinessAssessment`

`ReadinessAssessment` is AlienIntent's internal representation of the public Agent Ready result, preserving raw provenance.

No domain layer should know Agent Ready filesystem location, subprocess syntax, MCP transport details, provider CLI details, or Agent Ready package internals. Those belong in adapters.

---

# 8. Split/replan flow

## Initial compilation

external/internal requirements -> normalized requirements -> specification -> design / plan -> candidate BIU -> Agent Ready.

Outcomes:

- READY -> candidate may proceed to work materialization / later release gates.
- CLARIFY -> resolve only material owner question(s), then reassess.
- HOLD -> satisfy prerequisite, then reassess.
- SPLIT -> semantic split boundaries returned -> AlienIntent replans -> conservation check -> new candidate BIUs -> reassess each candidate.

## Replanning existing work

If later evidence shows a previously accepted decomposition was inadequate:

execution/review evidence -> new Agent Ready assessment or explicit replanning trigger -> SPLIT -> AlienIntent freezes original obligation set -> creates split transaction -> maps 100% of obligations to resulting work/integration parent -> rewrites dependency relationships -> invalidates stale readiness assessments -> reassesses resulting candidate units.

No obligation may disappear because work was split.

---

# 9. Design for N: requirements must come from multiple external systems

AlienIntent must never assume GitHub Issues are the canonical universal source of requirements.

The factory must support multiple requirement/work-management sources through ports/adapters.

Likely sources include:

- GitHub Issues / Projects
- Jira
- Linear
- Azure DevOps
- GitLab
- local files
- structured documents
- product-management systems
- future enterprise systems
- AlienIntent-native proposal intake
- external artifact/prototype intake

The AlienIntent Requirements / Planning domain must operate on an internal canonical requirements representation.

External-system vocabulary must not leak into the core domain.

Examples:

- Jira Epic is not automatically an AlienIntent Requirement.
- GitHub Issue is not automatically a BIU.
- Linear Project is not automatically a Wave.

Adapters translate source concepts plus provenance into the internal model.

AlienIntent should preserve external source, external identity, external version/revision, source link, ingestion timestamp, authority status, and synchronization/projection semantics.

Work-management projection is similarly adapter-based.

**Design target:** Replace Jira with GitHub, or GitHub with another provider, without rewriting the Requirements / Planning domain.

---

# 10. Public-use constraint

AlienIntent is a product, not a FactoryChecks-specific automation.

Therefore:

- no FactoryChecks-specific assumptions in the core domain;
- no AlienIntent-self-hosting assumptions in the core domain;
- no single-provider requirement-source assumptions;
- no single AI-provider assumptions;
- no single repository-layout assumptions beyond explicitly configured interfaces;
- no hidden dependency on one user's local environment;
- project-specific conventions belong in configuration/adapters/policy.

AlienIntent self-building is one project instance. FactoryChecks is another project instance. Future projects must be first-class.

---

# 11. Explicit cognizant allocator

AlienIntent requires an explicit Allocation capability.

The allocator is not a passive queue popper.

It makes attributable work-assignment decisions using relevant constraints.

Inputs may include:

- BIU requirements
- required capabilities
- risk class
- provider/model capability evidence
- current provider readiness
- local/remote availability
- current WIP/capacity
- concurrency limits
- execution budget
- remaining budget
- security/privacy constraints
- repository/project constraints
- historical quality/yield evidence
- routing policy
- retry/failover policy

Output is an attributable allocation decision including selected worker/provider/model, why selected, limits, authority basis, and fallback/escalation conditions.

## Local-model-first default

The default system-init posture should be:

> Use an adequate local model for allocation cognition where one is available and passes configured capability checks.

Frontier/paid models are optional escalation providers.

System initialization should configure local allocator model/provider, capability/readiness check, escalation provider(s), quality/risk threshold for escalation, and budget policy.

Deterministic policy should settle trivial allocation cases without a model.

A local model should handle ordinary allocation cognition where demonstrated adequate.

Frontier cognition should be reserved for cases that exceed local capability or configured confidence/risk policy.

---

# 12. Deterministic worker test boundary

The prior phrase "fake-agent" / "fake-worker" is misleading.

The purpose is not to simulate frontier-model intelligence.

The purpose is to exercise AlienIntent's real orchestration deterministically.

Recommended working name:

> **Deterministic Test Worker**

Alternative names to evaluate later:

- Test Worker
- Deterministic Worker Simulator
- Execution Test Worker
- Worker Protocol Simulator

Avoid names that imply imitation of LLM intelligence.

## Definition

A Deterministic Test Worker is:

> A deterministic implementation of the same worker-facing port/protocol used by production workers, capable of producing scripted valid and invalid worker behaviors so AlienIntent's real control plane, lifecycle, recovery, identity, evidence, and fault handling can be tested without paid model inference.

Architecture:

WorkerPort -> Real Worker Adapter -> Codex/Claude

or:

WorkerPort -> Test Worker Adapter -> deterministic scenarios.

AlienIntent core must not special-case lifecycle semantics for the test worker.

No shortcut such as `if test_mode: mark_done()`.

The Test Worker must exercise the same observable contract.

It should support scenarios such as valid result, malformed result, missing result, delayed result, duplicate result, wrong correlation identity, capacity failure, provider failure, crash before output, progress then crash, restart/resume, repair cycle, verification rejection, human-decision request, split recommendation where appropriate, and successful end-to-end outcome.

---

# 13. Architecture-edge authority

Implementation workers do not invent architecture policy.

If implementation discovers a material architecture question that existing authority does not answer:

stop affected work -> surface ArchitectureDecisionRequired -> Founder decides architectural policy.

Engineering research may inform the decision. Implementation may not silently choose it.

Founder retains architectural-policy authority unless explicitly delegated later.

---

# 14. Persistent deterministic monitoring

Persistent monitoring must live outside model-session lifetime.

Examples include liveness observation, lifecycle event observation, queue/attention observation, process/service health, durable anomaly detection, and event ingestion/reconciliation under already-authorized deterministic rules.

Models may interpret anomalies and make judgments.

Models must not have to remain alive merely to keep monitoring active.

**Invariant:** Cognition may be episodic. Deterministic monitoring must be durable.

---

# 15. Microservices clarification

A bounded context and a microservice solve different problems.

## Bounded context

A DDD bounded context answers:

> Where is this model/language internally consistent, and who owns these invariants?

It is a semantic/design boundary.

## Microservice

A microservice adds a deployment/distribution boundary:

- independent process/runtime;
- network/API failure modes;
- deployment/version compatibility;
- observability;
- retries/timeouts;
- distributed transactions or eventual consistency;
- service discovery/configuration;
- operational ownership.

A microservice can be useful when those deployment properties are actually valuable.

It can be harmful when the distribution cost is greater than the independence gained.

Therefore:

> Do not create a microservice merely because a bounded context exists.

Likewise:

> Do not avoid a microservice when independent scaling, deployment, security isolation, ownership, or failure containment clearly justify one.

For current AlienIntent core architecture, prefer a modular monolith with explicit bounded contexts and Hexagonal ports until evidence demonstrates a reason to distribute a context.

Agent Ready is already independently deployable for product-boundary reasons, but that does not imply every AlienIntent bounded context should become a service.

---

# 16. First-pass Ubiquitous Language — Agent Ready

This is v0.1 and should be refined against current code/specification before canonical adoption.

## Assessment
A durable result of applying Agent Ready readiness semantics to one identified proposed Work Unit under one identified assessment/version/provider context.

## Work Unit
A proposed unit of autonomous software-development work supplied to Agent Ready for assessment. Agent Ready does not require the work unit to be an AlienIntent BIU.

## Readiness
The degree to which a Work Unit is sufficiently understood, cohesive, constrained, prerequisite-satisfied, and verifiable for autonomous implementation.

## Disposition
Exactly one terminal semantic assessment outcome: READY, CLARIFY, SPLIT, HOLD.

## READY
The Work Unit is sufficiently coherent and constrained to hand to an autonomous implementation agent. READY is not execution authorization.

## CLARIFY
A material owner-intent or authority question must be resolved before the work can be responsibly implemented. CLARIFY is not used for ordinary engineering research the worker can perform itself.

## SPLIT
The Work Unit contains materially independent decision centers or outcomes that should be separated before autonomous implementation. SPLIT is not triggered merely because work is large.

## HOLD
A required external prerequisite is absent or unavailable. HOLD is not unresolved owner intent; that is CLARIFY.

## Owner Question
A question whose answer requires product/business/architecture/authority ownership rather than ordinary engineering investigation.

## Engineering Unknown
A question a competent implementation agent can answer through bounded technical research without changing owner intent or authority.

## Prerequisite
An external condition, artifact, environment, dependency, permission, decision, or capability that must exist before implementation can responsibly begin.

## Independent Decision Center
A part of a Work Unit that can be implemented, accepted/rejected, or reasoned about independently enough that combining it materially increases rework or decision coupling.

## Rework Locality
How well likely implementation/verification changes remain confined to the proposed Work Unit rather than causing broad unrelated churn.

## Split Boundary
A semantic boundary recommended by Agent Ready between independent decision centers. It is advice, not project mutation.

## Assessment Contract
The versioned public structure in which Agent Ready returns assessment results.

## Assessment Feedback
Attributable downstream outcome evidence supplied by an Agent Ready consumer and linked to the assessment that preceded it.

## Feedback Corpus
A versioned set of Assessment Feedback used to evaluate and improve readiness semantics.

---

# 17. First-pass Ubiquitous Language — AlienIntent

This is v0.1 and should be reconciled against Architecture Authority, existing SF-REQs, lifecycle vocabulary and current Python code before canonical adoption.

## Project
One independently governed software/product system operated by an AlienIntent installation. Examples: AlienIntent itself; FactoryChecks; a future unrelated project. A Project has its own sources, repositories, work-management configuration, policies, authority and evidence.

## Proposal
A candidate change in product intent submitted for evaluation. A Proposal is not yet an authorized Requirement.

## Requirement Source
An external or internal system from which requirement/proposal information is obtained.

## Source Record
The provider-specific external record observed through a Requirement Source. AlienIntent preserves provenance but does not make provider vocabulary part of the core domain.

## Requirement
An authorized statement of product capability, behavior, constraint or outcome that AlienIntent must preserve through specification, design, planning and execution.

## Requirement Provenance
The durable relationship between a Requirement and the source records, proposals, decisions and authority from which it was derived.

## Specification
A clarified, sufficiently explicit description of required intent, scope, constraints, acceptance and non-goals suitable for design.

## Design Contract
The explicit architecture/invariant/interface/failure/recovery contract governing implementation of one specified capability or coherent design area.

## Design Verification
Independent challenge of a Design Contract before implementation planning. Design Verification seeks missing owners, impossible premises, inconsistent boundaries, unproven platform assumptions and hidden architectural decisions.

## Plan
An authorized technical decomposition and dependency strategy for implementing verified design.

## Wave
A Founder-authorized set of Requirements/Design/Plan scope approved for autonomous factory execution under a defined authority and budget envelope. A Wave is not merely a label or milestone.

## Bounded Implementation Unit (BIU)
A bounded executable work contract derived from authorized Plan scope. A BIU contains enough intent, constraints, acceptance, proof and authority for implementation without inventing product/design policy.

## BIU Compiler
The Requirements / Planning capability that materializes authorized planning intent into candidate BIUs while preserving traceability and obligations.

## Replan
An authority-bearing change to technical decomposition after the current Plan/BIU structure is found inadequate.

## Split Transaction
A specific Replan operation that replaces or restructures one work unit into multiple units while preserving every authorized obligation, dependency and required integration proof.

## Obligation
A required piece of intent, acceptance, verification, evidence, dependency or integration responsibility that must not disappear during compilation/replanning.

## Obligation Conservation
The invariant that every authorized Obligation remains attributable after compilation, split or replan.

## Integration Parent
A retained work/integration unit that owns cross-child integration proof after a split when no child alone can satisfy the original integrated obligation.

## Readiness Assessment
AlienIntent's immutable recorded use of an Agent Ready Assessment plus provenance and current interpretation. AlienIntent does not own readiness semantics.

## Allocation
The act of binding authorized work to an eligible execution resource/provider/model under policy, capability, capacity and budget constraints.

## Allocator
The cognizant AlienIntent capability that makes attributable Allocation decisions.

## Execution Packet
The exact bounded runtime authority/resources/limits/context assigned to one work execution attempt or cycle.

## Provider
A system capable of supplying model/agent execution.

## Worker
A concrete execution actor operating under an Execution Packet.

## Worker Capability
A declared/verified capability relevant to allocation.

## Deterministic Test Worker
A deterministic WorkerPort implementation used to exercise the real AlienIntent execution protocol and control plane without model inference.

## Invocation
One attempt to start/use a Worker. An Invocation is not an Execution Cycle.

## Execution Cycle
A semantic implementation/verification/rework cycle governed by AlienIntent lifecycle rules. Provider retry/failover within the same phase does not automatically create a new Execution Cycle.

## Candidate
A concrete implementation artifact/result proposed for verification/acceptance.

## Candidate Custody
The guarantee that an exact Candidate is durably identifiable, retrievable and attributable throughout verification/acceptance.

## Observation
A factual recorded occurrence. An Observation is not a Verdict.

## Verdict
An authoritative conclusion about work/result status produced by the designated authority/process. Provider process exit or textual success is not automatically a Verdict.

## Evidence
Durable information supporting an Observation, Verdict, Requirement satisfaction claim, recovery action or learning conclusion.

## Quality Evidence
Derived evidence about quality/yield/failure/rework created from durable observations while preserving the distinction between fact and interpretation.

## REVIEW
The lifecycle activity that discovers failure classes AlienIntent does not yet know how to mechanize. REVIEW explores.

## VERIFY
The lifecycle activity that proves known requirements/invariants AlienIntent already knows how to check. VERIFY accumulates.

## Gap Trap
The learning mechanism that converts recurring suitable REVIEW discoveries into deterministic VERIFY/enforcement capability.

## Failure Class
A generalized category of defect or unsafe behavior discovered from one or more concrete findings.

## Proven Red
Evidence that a deterministic control fails when a meaningful representative violation is introduced. Where practical, representative real-data shape should complement synthetic mutation.

## Attention Item
A durable indication that something requires model/operator judgment. It is not itself a Founder Decision.

## Founder Decision
A durable human authority decision required because existing authority does not resolve a material product, architecture, policy, risk or budget question.

## Architecture Decision Required
A Founder Decision specifically concerning architecture policy that implementation agents are not authorized to invent.

## Decision Inbox
The operator-facing surface for unresolved Founder Decisions with enough context to decide without reconstructing agent history.

## Work Management Provider
The external system used to represent/project product/work state and relationships. Examples: GitHub; Jira; other adapters. Its provider-specific model is not the AlienIntent domain model.

## Projection
A representation of AlienIntent-owned or source-owned domain state in an external Work Management Provider. A Projection is not automatically authority.

## Release
The explicit authority-bearing transition that allows an eligible READY work item to enter implementation under a defined baseline and execution envelope.

## Monitoring
Durable deterministic observation/reconciliation infrastructure independent of model-session lifetime.

## Coordinator
A bounded cognitive/control role that evaluates durable state and makes/requests authorized coordination decisions. A Coordinator episode need not be permanent.

## Learning Proposal
A cited recommendation to change policy, routing, context, verification or design based on evidence. A Learning Proposal is not active policy until approved under promotion authority.

---

# 18. User interaction direction

The previously outlined user workflow is accepted as the starting model:

introduce proposal -> CAPTURE -> clarify / deduplicate / establish authority -> SPECIFY -> DESIGN -> independent Design Verification -> PLAN -> candidate BIUs -> Agent Ready assessment -> Wave approval packet -> Founder authorizes Wave -> AlienIntent executes autonomously -> Founder interrupted only for real authority decisions -> Wave closure / learning.

Do not over-design the final UX now.

After the autonomous factory is operational, survey strong existing developer/product/workflow tools and adopt the best interaction patterns.

Design now must preserve future UX flexibility.

---

# 19. New-project initialization direction

Usability polish is not the current priority.

However, architecture must preserve a future project initialization boundary.

Conceptual future command:

`alienintent init`

Project initialization will eventually configure:

- Project identity
- Requirement Source adapters
- Work Management Provider adapter
- repositories/source-control adapters
- lifecycle mapping
- authority policy
- Agent Ready interface
- providers/models
- local allocator model
- frontier escalation providers
- execution budget
- concurrency/WIP policy
- worker capability policy
- sandbox/worktree policy
- evidence storage
- monitoring host
- Decision Inbox / notification
- security/privacy policy

Validation:

`alienintent doctor`

must prove configured capability before autonomous execution.

Do not prioritize polished onboarding ahead of factory completion. Do preserve these extension points now.

---

# 20. Decisions now considered settled in principle

1. Agent Ready remains an independent repository/product/bounded context.
2. Agent Ready owns readiness semantics, assessment contract, CLI and MCP.
3. Historical Agent Ready assessments are immutable; schema evolution must remain backward-compatible or use versioned adapters/read-time projection.
4. Consumers are responsible for supplying outcome feedback to the Agent Ready feedback corpus.
5. Agent Ready owns split judgment; AlienIntent owns authority-bearing split/replan mutation.
6. AlienIntent Requirements / Planning is a distinct bounded context, initially within a modular Python deployment unless evidence supports distribution.
7. Agent Ready integration uses a Hexagonal port with CLI/MCP adapters.
8. AlienIntent Requirements / Planning must be source-provider-neutral and support N requirement sources such as GitHub, Jira and others through adapters.
9. AlienIntent is designed for N projects; AlienIntent-self-building and FactoryChecks are instances, not special cases.
10. AlienIntent has an explicit cognizant Allocator capability.
11. Allocation should default to an adequate local model when configured/demonstrated capable, with optional paid/frontier escalation established during project/system initialization.
12. SF-REQ-039 intent is a deterministic worker-protocol/control-plane test capability, not simulation of frontier intelligence.
13. Working name: Deterministic Test Worker, subject to later naming refinement.
14. The Deterministic Test Worker must use the same WorkerPort/protocol and real control plane as production workers.
15. Implementation workers do not invent architecture policy; unresolved architecture policy returns to Founder authority.
16. Persistent deterministic monitoring lives outside model sessions.
17. The current user-interaction workflow is accepted as an initial product workflow, with later UX refinement informed by external-product research.
18. New-project initialization is a future usability/productization concern, but present architecture must preserve configuration/adaptation boundaries required for it.

---

# 21. Follow-up canonicalization work

Before these decisions are considered fully canonical, reconcile them into:

## AlienIntent
- Architecture Authority
- relevant SF-REQs
- Phase 14 Founder decision records
- Requirements / Planning design contract
- Allocation design
- SF-REQ-039 naming/scope
- Work Management / Requirement Source port definitions
- system-init/doctor future boundary
- Ubiquitous Language artifact

## Agent Ready
- repository architecture/product docs
- assessment contract policy
- immutable-history/version-compatibility policy
- assessment feedback contract
- feedback corpus roadmap
- Ubiquitous Language artifact

Do not duplicate the same authority text in multiple places unnecessarily. Choose one canonical owner per invariant and cross-reference it elsewhere.
