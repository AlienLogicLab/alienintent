# AlienIntent Architecture Authority — Founder-Resolved Decisions

**Date:** 2026-09-19  
**Status:** Authoritative founder-approved architecture direction  
**Owner:** Alien Logic Lab  
**Product:** AlienIntent

## Governing principles

AlienIntent must be designed deliberately from product intent, not inherited implementation accident.

Binding principles:
- DDD
- Hexagonal Architecture
- explicit Anti-Corruption Layers
- Python-specific software-engineering best practices
- Alien Logic Lab EOS inheritance/contribution
- convention over configuration
- solve for N architecturally; optimize normal use for N=1
- KISS
- event-driven / asynchronous integration
- polling prohibited unless explicitly approved
- material product/architecture/security/privacy/deployment decisions require Founder review before implementation
- routine implementation details inside approved constraints are delegated

> **AlienIntent must be built from explicit intent, not inherited accident.**

## 1. Deployment topology

One AlienIntent service may manage N project profiles. Default installation creates one.

Each profile isolates configuration, operational state, credentials/references, workspaces/worktrees, queues/reservations, and evidence namespaces.

FactoryChecks uses one profile. AlienIntent is not architecturally limited to one.

## 2. Hosting model

Self-hosted is canonical.

Alien Logic Lab is not committing to host a cloud service. The architecture must not prevent third parties or enterprises from hosting AlienIntent. No core capability may require an Alien Logic Lab-hosted service.

## 3. Transport

Transport is a Hexagonal port.

First-class adapters:
- direct webhook
- outbound relay

Polling is not a normal integration mechanism.

The domain/application core must not depend on GitHub webhook semantics, Cloudflare, relay implementation, or transport details.

An outbound relay deserves first-class support because it removes inbound-networking friction for self-hosted deployments.

## 4. PRODUCER and VERIFIER identities

PRODUCER and VERIFIER are AlienIntent domain roles.

External identities are adapter/deployment policy.

Default:
- internal logical role separation
- minimum necessary external identity infrastructure

Optional higher-assurance configurations may use separate GitHub users, Apps, credentials, providers, models, or execution environments.

Morty and JC are bootstrap identities, not product requirements.

## 5. Verifier independence

Default verifier independence requires:
- separate invocation
- isolated worktree
- independent context
- immutable candidate/evidence inputs
- separate provenance
- no access to producer private reasoning/session state
- no self-approval

Different provider/model/account/machine are optional assurance escalations, not default requirements.

## 6. Agent-native source-control methodology

AlienIntent is optimized for agentic engineering, not PR-centric human review.

Primary controls shift left:
- continuous checks during implementation
- deterministic validation on meaningful checkpoints/commits
- automated tests
- static analysis
- architecture fitness functions
- semantic/evaluation gates
- independent agent critique/review
- evidence-driven acceptance

PRs remain supported when repository policy, branch protection, human collaboration, or external workflow requires them.

> **Engineering trajectory and continuous verification are primary; a PR is one possible repository artifact.**

Merge/landing is a closure operation, not a lifecycle state.

## 7. Multi-repository work

AlienIntent must solve for work spanning N repositories.

A product-level Work Item may decompose into multiple bounded implementation artifacts associated with different repositories, with explicit dependencies/DAG ordering.

Do not pretend multi-repository work is one atomic Git transaction.

## 8. Canonical work model

AlienIntent owns repository-neutral work concepts.

Product intent may exist before any repository is known.

GitHub Project Draft Items, GitHub Issues, Jira Issues, Linear Issues, GitLab Issues, etc. are adapter representations.

Repository ownership is not required merely to express intent.

## 9. Lifecycle semantics and Ubiquitous Language

Current semantic lifecycle baseline:

CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE

Semantics are authoritative enough to design against. Exact labels are not cast in stone.

DDD/Ubiquitous Language work may improve names before the canonical Python model is finalized. Once approved, the Ubiquitous Language is authoritative across code, architecture, docs, prompts, control plane, integrations, and work packets.

External workflow states map to AlienIntent semantics.

## 10. Execution authorization

READY means prepared for execution.

AlienIntent supports an execution-release policy switch:
- automatic release ON (default)
- automatic release OFF

ON: a READY BIU satisfying release policy transitions to IMPLEMENT through an attributable policy release.
OFF: a human explicitly authorizes release.

This is policy, not a hard-coded human-approval requirement.

## 11. Assurance policy

Do not create a heavy LOW/NORMAL/HIGH bureaucracy unless evidence proves it useful.

AlienIntent needs a configurable assurance-policy mechanism that may strengthen:
- approval requirements
- verifier independence
- deterministic verification depth
- sandbox/isolation
- granted capabilities
- deployment authority
- evidence requirements

Default policy remains simple.

## 12. Sandboxing

Sandboxing is optional/configurable.

Purpose: limit blast radius when agents are granted powerful capabilities.

It is not intended to neuter agents.

Trusted deployments may run unsandboxed. When enabled, prefer Linux-native containers. Docker-compatible containers should also be supported. Higher-assurance backends may be adapters.

A container does not solve token waste; cost/trajectory controls address that.

## 13. BIU and capability authority

Until Ubiquitous Language work explicitly changes it, **BIU (Bounded Implementation Unit)** is the bounded execution artifact.

Each BIU receives the capabilities actually required to complete it.

Examples:
- code-change BIU: repository workspace, Git, language toolchain, tests, network if required
- deployment BIU: may additionally receive deployment credentials, cloud API access, DB migration authority, service-control authority

Capabilities should be explicit, attributable, and revocable where practical.
AlienIntent must be capable of granting dangerous/powerful capabilities when required.
Use sensible capability profiles/conventions plus explicit BIU-specific additions;
do not require needless per-operation permission bureaucracy.

## 14. Deployment authority

Agents must be able to change live environments when authorized.

Deployment capabilities may include:
- application deployment
- infrastructure changes
- DB migrations
- config rotation
- service restart
- feature-flag changes
- cloud resource changes

AlienIntent records:
- which BIU received authority
- which worker received it
- target environment
- granted capabilities
- actions taken
- verification performed afterward

## 15. Operational state versus durable learning evidence

Separate short-lived operational state from long-lived trajectory/evidence.

Operational state includes active invocation, reservations, retries, worktree ownership, event correlation, recovery state, and worker state.

Durable trajectory/evidence includes task characteristics, provider/model/version, context/policy version, execution trajectory, verification/review findings, repairs, quality outcomes, cost, latency, interventions, and downstream outcomes where available.

Durable evidence may be retained long-term because it feeds learning. Retention remains configurable.

## 16. State-store default

SQLite is the default for simple self-hosted/single-service operation.

PostgreSQL should be supported for multi-instance/hosted deployments.

Persistence must not collapse operational state, trajectory evidence, and learned policy into one undifferentiated store.

## 17. Domain event vocabulary

AlienIntent owns its internal event vocabulary.

External vendor events are translated through adapters/Anti-Corruption Layers.

Domain-event names follow the approved Ubiquitous Language.

## 18. Event delivery guarantees

Transport may duplicate, delay, retry, or reorder events.

AlienIntent should provide effectively once-only processing effects using:
- durable event identity
- deduplication
- idempotent handling
- exact invocation correlation
- replay support

Do not claim physically exactly-once network delivery.

## 19. Concurrency

Use bounded concurrency globally, per project, and per repository.

Default conservatively. One active mutating worker per repository is a reasonable starting convention unless safe parallelism is proven.

## 20. Cancellation

Cancellation is a first-class exceptional outcome.

On cancellation:
- terminate worker safely
- preserve evidence
- clean ephemeral resources
- record authority/reason
- make recovery/retry policy explicit

It need not be a normal happy-path lifecycle state unless domain modeling proves otherwise.

## 21. Async / no polling / retries

Polling is prohibited as an architectural integration mechanism unless explicitly approved as an exception.

Prefer asynchronous/event-driven operation over blocking synchronous designs.

Transient failures use bounded retries, exponential backoff, jitter, and finite limits.

## 22. Cost governance

AlienIntent must put hard boundaries around token/model spend.

Support:
- per-BIU budget
- project/deployment budget
- retry budget
- measured cost
- hard-stop controls
- cost attribution

Learning should measure useful outcome per cost, not token consumption alone.

## 23. Provider routing

Provider/model choice is vendor-neutral.

> **Use the cheapest provider/model demonstrated capable of satisfying the required quality bar. Prefer local models when they satisfy the bar.**

Provider adapters advertise capabilities.

## 24. Context Engineering

Already decided.

AlienIntent manages:
- instructions
- knowledge
- memory
- examples
- tools
- guardrails

Requirements:
- static vs dynamic context
- provenance
- versioning
- progressive disclosure / skills
- task-specific assembly
- context budgets
- evidence linking context policy to outcome

## 25. Memory model

Already decided.

Do not create a generic memory bucket.

Separate:
- operational state
- task context
- durable engineering knowledge
- organizational knowledge
- engineering trajectory
- Quality Evidence
- learned policy

## 26. Evidence retention

Local-first by default.

Requirements:
- configurable retention
- secret redaction
- immutable accepted evidence where appropriate
- rich capture
- selective retrieval
- no dependence on private chain-of-thought

## 27. Private reasoning

Do not require/store private chain-of-thought.

Preserve observable engineering evidence:
- authorized inputs
- context versions
- tool actions
- commands/results
- artifact changes
- tests
- verification
- review findings
- decisions
- cost/time
- outcomes

## 28. Privacy and community learning

Self-hosted deployments remain private/local by default.

Nothing leaves the deployment except through explicitly configured adapters/providers.

AlienIntent must also support optional community-learning contribution.

Community contribution shares generalized/anonymized engineering learning, not proprietary source or sensitive execution content.

Potential shared learning:
- provider/model performance by task class
- failure taxonomy
- verification effectiveness
- intervention effectiveness
- routing evidence
- cost/quality relationships
- capability observations

Participation is explicit/configurable.

## 29. Adapter contracts

Ports/adapters are versioned and capability-aware.

The core must not accumulate vendor-specific conditional logic.

## 30. Extensibility

Design ports so third-party adapters are possible.

Do not build a giant generalized plugin framework before real implementations validate the abstraction.

At least two implementations should exercise an extension point before treating its API as stable.

## 31. Configuration

Use a typed configuration schema and convention-heavy defaults.

`alienintent init` generates normal configuration.

Advanced users may edit it.

Secrets are referenced, not embedded.

Internal provider/project IDs should be discovered automatically where possible.

## 32. Secrets

Use a `SecretProvider` port.

Simple self-hosted default may use protected local files.

Support adapters for environment references, OS keyrings, Vault, cloud secret managers, Kubernetes Secrets, and enterprise secret systems.

## 33. Packaging / installation

Canonical implementation is Python.

Provide a first-class CLI.

Installer/bootstrap must automate or eliminate manual setup pain.

Containers are optional/configurable, not mandatory.

Service/control-surface packaging must account for the first-class AlienIntent Control Plane.

## 34. Upgrade and compatibility

Use best practices:
- semantic versions
- explicit migrations
- preflight validation
- checkpoints/backups
- safe behavior during active work
- rollback where practical
- versioned external/persisted contracts

Before 1.0, controlled breaking changes are acceptable with migration support.

## 35. Observability

AlienIntent provides:
- structured logs
- health/readiness
- execution timelines
- metrics
- traces where useful
- model/provider usage
- token/cost/latency
- lifecycle history
- diagnostics

This also feeds Engineering Trajectory and Quality Evidence.

## 36. Operator Control Plane

AlienIntent requires a first-class operator control plane.

Originating principle:

> **A state machine needs an event generator so the operator can deliberately generate valid events to test, diagnose, recover, and drive it without directly hacking state.**

Capabilities include:
- status
- explain
- emit/generate legitimate domain events
- replay
- resume
- reconcile
- cancel/abort
- doctor/diagnostics
- logs
- version/install diagnostics
- inspect active BIUs
- inspect workers/invocations
- inspect queued/pending events
- inspect state-machine state
- inspect evidence
- inspect provider/model routing
- inspect token/cost usage
- inspect capabilities/credentials granted
- inspect transport health
- inspect adapter health
- test event paths
- test state transitions
- synthetic-event generation
- configuration/policy management where appropriate

Critical rule:

> **Operator-generated events should flow through the same domain/event interfaces as normal events wherever possible. The control plane must not become a direct state-mutating backdoor.**

CLI and web interfaces are presentation adapters over the control-plane application services.

## 37. Human control surfaces

External work-management systems remain important human surfaces for backlog/workflow.

They do not replace the AlienIntent operator control plane.

At minimum CLI access is required.

Prior control-panel/web work should be recovered and incorporated rather than reinvented.

## 38. Installer/bootstrap UX

`alienintent init` is first-class product functionality.

It should:
- discover IDs/config where possible
- automate GitHub App setup where possible
- guide repository authorization
- configure work-management adapter
- configure transport/relay
- configure providers
- map lifecycle semantics
- validate secrets
- configure service/control plane
- run health checks
- support resume
- support rollback
- support diagnostics
- support noninteractive automation

## 39. Architecture fitness

DDD/Hexagonal boundaries must be mechanically enforced where practical.

Examples:
- no vendor SDK imports in domain
- dependency-direction tests
- port conformance tests
- adapter isolation
- no GitHub/Jira/Codex types in domain interfaces
- architecture checks in CI

## 40. EOS inheritance/contribution

AlienIntent is intended to inherit from Alien Logic Lab EOS after EOS
normalization establishes one internally consistent approved version.

AlienIntent records one internally consistent, approved EOS version/commit before
claiming conformance. Mixed per-document maturity states are not a conformance
baseline; maturity inconsistencies must be reconciled in EOS itself first.

Generalizable improvements return to EOS through explicit proposals/PRs or another deliberate governance mechanism.

## 41. Python repository structure

Use a `src/` layout organized by approved bounded contexts.

Keep domain/application/ports/adapters/composition architecturally separated.

Exact package names wait for DDD/Ubiquitous Language/bounded-context modeling.

No agent may invent repository structure merely because implementation starts.

## 42. Node → Python coexistence

Node remains the bootstrap implementation.

Node and Python should coexist in the same repository during migration unless evidence forces a different decision.

Node is frozen except for critical bootstrap fixes.

Python is implemented against shared behavioral/conformance contracts.

Node remains operational authority until Python reaches sovereignty.

## 43. Python Sovereignty

Python Sovereignty is reached when:

> **The Python AlienIntent implementation can operate AlienIntent development end-to-end without invoking Node and passes the full behavioral conformance, live self-hosting, recovery, control-plane, evidence, and learning suite.**

Only then may Node be retired.

## 44. Remaining pre-Python design work

Before substantial canonical Python implementation:

1. Product Intent
2. Ubiquitous Language v1
3. bounded-context model
4. Hexagonal Architecture specification
5. core ports
6. Anti-Corruption Layer rules
7. Python engineering standard
8. BIU/domain execution model
9. capability/authority model
10. assurance-policy model
11. event model
12. persistence model separating operational state and long-lived evidence
13. Control Plane application model
14. adapter contracts
15. Node/Python conformance strategy
16. EOS inheritance/contribution mechanism
17. architecture fitness rules
18. installer/bootstrap design

## 45. Founder escalation rule

Agents may decide routine implementation details only inside approved constraints.

Founder review is required before implementation when a decision materially changes:
- product semantics
- architecture
- security/trust boundary
- user workflow
- deployment topology
- installation burden
- persistent data/lifetime
- compatibility
- integration contracts
- operational authority
- cost policy
- privacy/data sharing
- community-learning behavior

When Founder review is required, present:
1. decision
2. why it matters now
3. options
4. material tradeoffs
5. recommendation
6. consequences
7. what becomes authorized
8. what remains undecided

Do not silently choose because one implementation is convenient.

## Amendment — 2026-09-22: Founder architecture decisions (canonicalized)

Source: **Founder Architecture Decisions and Ubiquitous Language v0.1**
(`../decisions/alienintent-agent-ready-founder-decisions-and-ubiquitous-language-v0.1.md`),
Founder-approved; canonicalized here by the resident bootstrap coordinator. Each item names its
single canonical owner. Where the owner is another artifact, this section cross-references and
does not restate.

**Governing-principle refinement.** *Elegance includes the absence of unnecessary complexity.
Prefer the simplest architecture that preserves the required invariants and extension
boundaries.* Current architectural bias: **modular monolith + explicit DDD bounded contexts +
Hexagonal ports/adapters + distribution only when evidence justifies it** (independent scaling,
security isolation, failure containment, genuinely independent release lifecycle, operational
ownership, host/runtime constraints). This is not a prohibition on services; a bounded context
never implies a deployment boundary. Owner: this section (extends the KISS principle above).

**A1. Agent Ready product boundary.** Agent Ready remains an independent product, repository and
bounded context. It owns readiness semantics, the dispositions `READY / CLARIFY / SPLIT / HOLD`,
assessment logic, the versioned public assessment contract/schema, its CLI, its local MCP
interface, provider adapters and backward compatibility of its public interface. AlienIntent
consumes it **only** through supported public interfaces behind a Hexagonal port
(`ReadinessAssessment`, CLI or MCP adapters); it never imports Agent Ready private
implementation, copies its rubric, duplicates its decision logic or mutates its internals.
*Agent Ready remains a separate system* (canonical-architecture non-responsibility, retained).
Owner of the **integration**: SF-REQ-015 (amended). Owner of Agent Ready itself: the Agent Ready
product — no AlienIntent requirement claims it.

**A2. Requirements / Planning bounded context.** AlienIntent has an explicit Requirements /
Planning bounded context owning the invariant *authorized product intent is converted into
executable work without losing, inventing, weakening or silently reallocating obligations*:
requirement intake/normalization, provenance, specification, design inputs, planning,
requirement-to-BIU compilation, dependency DAG construction, Agent Ready invocation through a
port, processing of the four dispositions, the split/replan transaction, obligation conservation
and Wave-plan materialization. It exists even when deployed in the same process as other
contexts. FD-01's external-provider ownership of product authority, priority and business context
is unchanged; see the FD-01 refinement of 2026-09-22 and the FD-02 refinement in
`pre-python-gate/founder-decisions.md`. §41 and §44(3) apply: no package restructuring by this
amendment. Owners: this section (context map); SF-REQ-011/012/013/015 (capabilities).

**A3. Solve for N Projects and N Requirement Sources (binding).** §8 is refined: requirement
information enters through a `RequirementSource` port distinct from the `WorkManagement` port;
the core operates on a provider-neutral internal requirements model; external identity, revision,
link, ingestion time and authority status are retained as provenance; external vocabulary never
becomes the domain model. Neither AlienIntent self-hosting, nor any single external product, nor
GitHub, nor one model provider may be assumed by the core; project-specific conventions live in
configuration, adapters and policy. Owner: SF-REQ-011 (amended) for the port and provenance;
SF-REQ-005 for Work Management; this section for the principle.

**A4. Cognizant Allocator.** §23 is refined: AlienIntent has an explicit Allocation capability
producing attributable allocation decisions (selected worker/provider/model, why, limits,
authority basis, fallback/escalation), distinct from scheduling (SF-REQ-002). Default posture:
deterministic policy settles trivial cases; an adequate **local model** performs ordinary
allocation cognition where configured and demonstrated capable; frontier/paid models are optional
escalation, configured at initialization. Owner: SF-REQ-026 (amended); initialization SF-REQ-037.

**A5. Architecture-edge authority.** §45 is refined: when implementation encounters a material
architecture question existing authority does not answer, the affected branch stops and an
**Architecture Decision Required** is surfaced with evidence, options and a recommendation, as a
kind of `HumanDecisionRequired` through the Decision Inbox (SF-REQ-035). Engineering research is
allowed; silent architecture invention is not. No second decision mechanism is created.

**A6. Persistent deterministic monitoring.** Already canonical: SWF-27 §Bootstrap evidence
(*persistent monitoring is operational infrastructure and must not determine coordinator tenure*)
and SF-REQ-053/056. Restated only as the UL invariant *cognition may be episodic; deterministic
monitoring must be durable.* Owner: SWF-27 / SF-REQ-053. Not duplicated here.

**A7. Historical readiness assessments are immutable.** Consistent with §15 and §26. Owner of
retention/provenance: SF-REQ-029 (amended) within the Evidence and Learning module. Owner of
readiness semantics: Agent Ready (A1). Not the same owner.

**A8. Assessment feedback.** Agent Ready provides the feedback contract; consumers supply
attributable structured outcome evidence. AlienIntent derives it from durable execution evidence.
Owner: SF-REQ-030 (amended). The maturity point is **deliberately unsettled** — a Wave 2
design-learning objective.

**A9. Deterministic Test Worker.** SF-REQ-039 renamed and reframed in place; identity retained.

**A10. Project initialization.** §31 and §38 stand; the extension points `alienintent init` must
preserve are enumerated in SF-REQ-037 (amended). Polish is not prioritized ahead of factory
completion.

**A11. Ubiquitous Language artifact.** §9 and §44(2) are satisfied in first canonical form by
`alienintent-ubiquitous-language-v0.1.md`, which records terminology collisions rather than
normalizing them and explicitly does not canonicalize "Gap Trap".

## Amendment — 2026-09-22 (b): Reuse Before Build

Source: Founder follow-up of 2026-09-22 after the Wave 1 authoritative-capability-substitution
finding (`../evidence/2026-09-22-wave1-authoritative-capability-substitution.md`). Canonical
owner of the principle: this section, as a governing principle beside KISS and "solve for N".
Design-time enforcement: SWF-25 Design Verification (amended). Runtime classification:
SF-REQ-029 (amended). Configured-capability validation: SF-REQ-038 (amended).

> **Reuse Before Build.** Before implementing, emulating or prompting around a capability,
> determine whether an authoritative implementation already exists in the configured project /
> Alien Logic Lab / tool ecosystem. If one exists, consume it through its supported interface
> unless explicit authority records why it is unsuitable.

> **A compatible output shape is not evidence that the authoritative capability produced the
> result.** Producer identity is provenance to be recorded and checked, never inferred from
> field names, vocabulary or a passing schema.

**Failure class named:** *Authoritative Capability Substitution* — a workflow implements,
emulates or prompts around behaviour already owned by an available authoritative capability
instead of consuming that capability through its supported interface. Wave 1's readiness
assessments (PY-01…PY-10, PY-09B) are the recorded instance: the Agent Ready product, CLI and
MCP existed and had been used natively during the pre-Python gate, yet the Wave 1 coordinator ran
raw Codex/Claude prompts shaped to the Agent Ready contract.

**What follows for design and operation:**
- A Design Contract or work packet that names a specific external capability ("run Agent-Ready")
  names the *product*, not a shape; a substitute requires explicit recorded authority.
- Capability availability is **project configuration**, not host-local configuration
  (§31, §38, SF-REQ-037/038): a capability configured only in one operator's or one host's
  settings is not "available" to the factory.
- Where a contract names an external capability, enforcement fails closed on producer identity
  (SF-REQ-038 doctor; evidence checker `tools/evidence/check_assessment_producer.py`).

