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
- automatic release ON
- automatic release OFF

ON: work satisfying release policy may transition to IMPLEMENT automatically.
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

AlienIntent inherits from Alien Logic Lab EOS.

AlienIntent records the EOS version/commit it conforms to.

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
