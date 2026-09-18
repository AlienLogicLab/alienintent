# AlienIntent — Recommended Defaults for the 40 Founder Architecture Decisions

**Date:** 2026-09-18  
**Status:** Founder review draft  
**Purpose:** Readable, non-table version of the 40 architecture decisions and recommended defaults for AlienIntent.

---

## Governing defaults

Unless a decision materially changes the product, security model, trust boundary, installation burden, deployment model, cost model, privacy model, or user workflow:

- **Default to established best practices.**
- **Convention over configuration.**
- **Solve for N architecturally; optimize the normal experience for N=1.**
- **Use Hexagonal Architecture: variable external concerns belong behind ports/adapters.**
- **Keep the core domain vendor-neutral.**
- **Escalate complexity only when risk or user choice justifies it.**
- **DDD, Hexagonal Architecture, explicit Anti-Corruption Layers, Python best practices, and EOS inheritance/contribution are binding constraints.**

---

# 1. Deployment topology

## Recommendation

A single AlienIntent service should be capable of managing **N project profiles**, while the default installation creates exactly **one**.

Each project/profile should have isolated:

- configuration;
- operational state;
- credentials;
- queues;
- workspaces/worktrees;
- evidence.

FactoryChecks uses one project profile. The product is not artificially limited to one.

## Why

This solves for N without making N=1 painful.

It avoids the architectural dead end of requiring one OS process per project while preserving a trivial default operating model.

---

# 2. Hosted versus self-hosted

## Recommendation

**Self-hosted is canonical.**

Hosted operation is allowed by the architecture, but AlienIntent must not depend on an Alien Logic Lab cloud service.

## Why

This matches the product intent:

- Alien Logic Lab is not committing to operate a hosted SaaS version.
- Someone else should be able to host it.
- No core capability should depend on Alien Logic Lab infrastructure, licensing servers, hosted relay ownership, or account systems.

---

# 3. Event transport

## Recommendation

Define an `EventIngressPort`.

First-class adapters:

- direct webhook;
- outbound relay.

Additional adapters may include:

- polling;
- message brokers;
- other event sources.

## Why

Transport is an infrastructure concern, not a domain concern.

A webhook, relay, polling loop, or event bus must not shape the AlienIntent domain model.

For normal use:

- if public HTTPS is already available, direct webhook is simplest;
- if inbound networking is undesirable, outbound relay should be first-class.

The relay itself should be deployable independently and not require Alien Logic Lab hosting.

---

# 4. External identities for PRODUCER and VERIFIER

## Recommendation

Make this deployment policy.

Default:

- one GitHub App identity;
- internal logical separation between PRODUCER and VERIFIER.

Allow stronger configurations such as:

- separate GitHub users;
- separate Apps;
- separate credentials.

## Why

PRODUCER and VERIFIER are domain roles.

They do not inherently require different GitHub human accounts.

Users who want stronger identity isolation should be able to configure it.

---

# 5. Verifier independence

## Recommendation

A verifier is independent when it has:

- a separate invocation;
- an isolated worktree;
- an independent context;
- immutable candidate/evidence inputs;
- no access to the producer's private reasoning/session;
- separate provenance.

By default, the verifier may use:

- the same provider;
- the same model;
- the same GitHub App;
- the same machine.

Higher-risk policies may require different providers, models, credentials, or execution environments.

## Why

The objective is to avoid self-review contamination and preserve independent judgment.

Forcing different providers, machines, or GitHub identities for every task adds cost and ceremony without proportionate value.

Stronger separation is useful mainly to reduce **correlated failure**, so it belongs in risk policy.

---

# 6. Source-control workflow

## Recommendation

Default to:

- branch per execution unit;
- PR-based landing;
- respect repository branch protection and merge policies;
- direct-to-default disabled unless explicitly allowed.

`ACCEPT` authorizes closure.

Merge/landing is performed during closure and is **not** a lifecycle state.

## Why

This matches familiar engineering practice, preserves auditability, and avoids inventing a proprietary source-control workflow.

---

# 7. Multi-repository work

## Recommendation

A parent `WorkItem` may own multiple repository-specific `ExecutionUnit`s connected by an explicit dependency DAG.

Each Execution Unit can be verified independently.

Parent closure depends on the declared children satisfying policy.

## Why

Real product work often spans:

- frontend;
- backend;
- infrastructure;
- data;
- documentation.

Pretending a multi-repo change is one atomic Git transaction is unrealistic.

---

# 8. Canonical work-item model

## Recommendation

AlienIntent owns a repository-neutral `WorkItem`.

External objects are adapter references:

- GitHub Project Draft Issue;
- GitHub Issue;
- Jira Issue;
- Linear Issue;
- GitLab Issue.

A Work Item may exist before a technical repository is known.

## Why

Product intent should not depend on source-code ownership.

This keeps GitHub/Jira concepts out of the core domain.

---

# 9. Lifecycle semantics

## Recommendation

Use canonical AlienIntent lifecycle semantics:

`CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE`

External systems map their own workflow states onto these semantics.

## Why

Convention over configuration.

Users should be able to map Jira's "QA" or GitHub's "In Review" to AlienIntent semantics without redefining what VERIFY or REVIEW means internally.

---

# 10. Execution authorization

## Recommendation

Preserve the distinction:

- `READY` = sufficiently prepared for execution;
- transition/release to `IMPLEMENT` = authorization to execute.

Default:

- human authorization for NORMAL and HIGH-risk work;
- optional policy-based automatic release for explicitly approved LOW-risk work.

## Why

Readiness and authority are different concerns.

Combining them weakens governance and makes execution policy harder to reason about.

---

# 11. Risk / assurance classes

## Recommendation

Start with three classes:

- LOW
- NORMAL
- HIGH

Risk controls:

- approval requirements;
- model/provider selection;
- verifier independence;
- sandbox strength;
- tool capabilities;
- deployment authority;
- required evidence.

## Why

Three classes provide useful control without constructing a large compliance taxonomy.

More can be added later if real users require them.

---

# 12. Execution sandbox

## Recommendation

Production default:

- disposable container.

Other supported modes:

- trusted host execution for development;
- VM / ephemeral cloud runner as higher-assurance adapters.

## Why

A disposable Git worktree isolates repository state.

It does **not** isolate arbitrary model-generated commands from the host.

Containers provide a good default balance of simplicity, portability, and isolation.

---

# 13. Tool permission model

## Recommendation

Use capability-based grants with **deny by default**.

Potential capabilities include:

- shell;
- filesystem;
- network;
- package installation;
- Git;
- work-management APIs;
- cloud control planes;
- database access;
- production credentials.

## Why

A worker should receive only the authority required for the current execution unit.

This is standard least-privilege design.

---

# 14. Operational state store

## Recommendation

Default:

- SQLite for self-hosted/single-service installations.

Optional:

- PostgreSQL for multi-instance or hosted deployments.

Preserve durable event/audit records transactionally.

## Why

SQLite makes installation dramatically simpler and is sufficient for many self-hosted installations.

PostgreSQL should be available when concurrency, hosted operation, or scale requires it.

---

# 15. Canonical internal event model

## Recommendation

Use typed, versioned AlienIntent domain events.

Examples:

- WorkCaptured;
- WorkReady;
- WorkReleased;
- ExecutionStarted;
- VerificationCompleted;
- WorkAccepted;
- ClosureCompleted;
- WorkDone;
- WorkCancelled.

Vendor events are translated through ACLs.

## Why

The core event vocabulary must belong to AlienIntent, not GitHub or Jira.

---

# 16. Event delivery semantics

## Recommendation

Assume **at-least-once delivery**.

Require:

- idempotent handlers;
- event deduplication;
- exact invocation correlation;
- tolerance for event reordering where practical;
- replay support.

Do not promise exactly-once delivery.

## Why

This is the realistic distributed-systems model and aligns with behavior already learned from B-DISP.

---

# 17. Concurrency model

## Recommendation

Use bounded concurrency:

- global limit;
- per-project limit;
- per-repository limit.

Default:

- one active mutating execution per repository.

Allow configurable safe parallelism later.

## Why

Conservative defaults prevent workers from colliding.

Larger users can increase throughput when they understand their repository structure.

---

# 18. Cancellation

## Recommendation

Cancellation is a first-class terminal disposition, but not part of the normal happy-path lifecycle.

On cancellation:

- terminate worker safely;
- preserve evidence;
- clean ephemeral resources;
- record who/what cancelled and why.

## Why

Exceptional outcomes should be real and auditable without bloating the normal lifecycle.

---

# 19. Timeout and retry policy

## Recommendation

Classify failures as:

- transient;
- permanent;
- policy.

For transient failures:

- bounded exponential backoff;
- jitter;
- retry cap.

Never retry forever.

Switching provider/model requires policy authorization.

## Why

This is standard resilient-system behavior and prevents runaway loops.

---

# 20. Cost governance

## Recommendation

Support:

- per-work-item budget;
- installation-level budget/cap;
- measured provider cost;
- retry budget;
- hard-stop before exceeding configured limits.

Installer should generate sensible defaults.

## Why

Autonomous execution without spend boundaries is an operational risk.

Cost belongs in execution policy.

---

# 21. Provider contract

## Recommendation

Use a capability-based Provider Port.

Providers advertise capabilities such as:

- code modification;
- tool execution;
- structured output;
- streaming;
- persistent sessions;
- context limits;
- cost reporting;
- model identity/version;
- capability probing.

## Why

Do not force every provider into a lowest-common-denominator API.

AlienIntent needs capability-aware routing.

---

# 22. Context engineering

## Recommendation

Make context assembly an explicit application capability.

Support the six context classes:

- instructions;
- knowledge;
- memory;
- examples;
- tools;
- guardrails.

Separate:

- static context;
- dynamic context.

Track provenance, versioning, and token/size budgets.

## Why

Context is too important to be scattered across adapter code or prompts assembled ad hoc.

---

# 23. Memory model

## Recommendation

Do not create a generic "memory" bucket.

Separate:

- operational state;
- task context;
- durable engineering knowledge;
- organizational knowledge;
- evidence;
- learned policy.

## Why

Long-lived agent systems otherwise turn "memory" into an unmaintainable junk drawer.

---

# 24. Evidence retention

## Recommendation

Default to:

- local-first;
- configurable retention;
- secret redaction;
- immutable accepted evidence records;
- rich capture with selective retrieval.

## Why

AlienIntent needs evidence for auditability and learning without forcing users to surrender proprietary source/history.

---

# 25. Private reasoning

## Recommendation

Do not require or store private model chain-of-thought.

Preserve observable:

- inputs;
- tool actions;
- command outputs;
- artifacts;
- diffs;
- verification;
- review findings;
- decisions;
- cost/time.

## Why

This is sufficient engineering provenance and avoids depending on hidden reasoning.

---

# 26. Privacy and data residency

## Recommendation

Nothing leaves the deployment except through explicitly configured adapters/providers.

Relay should be:

- content-blind where practical;
- zero-retention by default.

## Why

Self-hosted should actually mean self-hosted.

External providers remain explicit trust boundaries.

---

# 27. Adapter API and versioning

## Recommendation

Use versioned ports/adapters with:

- capability discovery;
- compatibility rules;
- explicit versioning.

## Why

This avoids vendor-specific branching in core code and gives adapters a stable evolution path.

---

# 28. Extension / plugin model

## Recommendation

Design ports so third-party adapters are possible.

Do **not** build a large generic plugin framework in v1.

Stabilize extension APIs only after at least two real implementations exercise the abstraction.

## Why

This preserves extensibility without premature abstraction.

---

# 29. Configuration model

## Recommendation

Use:

- typed schema;
- convention-heavy defaults;
- `alienintent init` generation;
- environment overrides;
- human-editable advanced configuration;
- secrets referenced, never embedded.

## Why

Convention over configuration.

Users should rarely need to know internal IDs.

---

# 30. Secrets architecture

## Recommendation

Define a `SecretProvider` port.

Default:

- protected local files for simple self-hosted server deployment.

Optional adapters:

- OS keyring;
- environment references;
- Vault;
- cloud secret managers;
- Kubernetes Secrets.

## Why

Keeps initial deployment simple while avoiding permanent coupling to local files.

---

# 31. Packaging and service lifecycle

## Recommendation

Official distribution:

- Python CLI;
- OCI container.

CLI handles:

- init;
- admin;
- diagnostics.

Container is the recommended long-running service.

Also provide a systemd helper for users who do not want containers.

## Why

This supports developer, server, and enterprise use without coupling the application core to Docker/systemd/Kubernetes.

---

# 32. Upgrade model

## Recommendation

Use:

- semantic versions;
- explicit schema migrations;
- preflight validation;
- backup/checkpoint;
- drain or refuse unsafe upgrade during active execution;
- rollback where practical.

## Why

Operational state is valuable and must not be casually corrupted during upgrade.

---

# 33. Backward compatibility

## Recommendation

Version all persisted/external contracts from day one.

Before 1.0:

- breaking changes allowed with migration tooling.

After 1.0:

- normal semantic-version guarantees.

## Why

Avoid both premature compatibility paralysis and uncontrolled schema drift.

---

# 34. Observability

## Recommendation

Provide:

- structured logs;
- OpenTelemetry-compatible traces;
- metrics;
- health/readiness endpoints;
- execution timeline;
- diagnostics;
- provider/model usage;
- cost/latency.

Exporters remain adapters.

## Why

This follows standard operational practice and directly supports trajectory/evidence analysis.

---

# 35. Human control surface

## Recommendation

MVP:

- external work-management system;
- AlienIntent CLI;
- API underneath.

Do not build a dedicated web UI until evidence shows it is needed.

## Why

GitHub/Jira/Linear already provide mature human workflow surfaces.

Do not rebuild them without a demonstrated gap.

---

# 36. Installer / bootstrap UX

## Recommendation

Treat `alienintent init` as first-class product functionality.

It should:

- discover IDs instead of asking for them;
- automate GitHub App creation where possible;
- guide repository authorization;
- configure work-management adapter;
- configure transport/relay;
- configure providers;
- map lifecycle semantics;
- validate secrets;
- install the service;
- run health checks;
- support resume;
- support rollback;
- support diagnostics;
- support noninteractive automation.

## Why

The manual bootstrap work already performed is direct evidence of what the installer must automate or eliminate.

---

# 37. Architecture fitness enforcement

## Recommendation

Mechanically enforce DDD/Hexagonal boundaries in CI.

Examples:

- forbidden vendor imports in domain;
- dependency-direction tests;
- port conformance tests;
- adapter isolation;
- no GitHub/Jira/Codex types in domain interfaces.

## Why

Architecture that exists only in prose will drift.

Machines should reject violations.

---

# 38. EOS inheritance and contribution

## Recommendation

Each Alien Logic Lab project adopts a versioned EOS baseline.

AlienIntent records the EOS version/commit it conforms to.

Generalizable AlienIntent improvements return to EOS through explicit proposals/PRs.

## Why

This makes EOS inheritance/contribution concrete and auditable without hidden synchronization.

---

# 39. Python repository structure

## Recommendation

Use a `src/` layout organized by approved bounded contexts.

Keep:

- domain;
- application;
- ports;
- adapters;
- composition

architecturally separated.

Do not finalize package names until domain modeling is approved.

## Why

Package structure should follow the domain and Hexagonal Architecture, not a framework or vendor SDK.

---

# 40. Node → Python coexistence / Python Sovereignty

## Recommendation

Keep Node and Python in the **same repository during migration**.

Node becomes:

- bootstrap implementation;
- frozen except for critical fixes.

Python is built alongside it against shared behavioral contracts.

Node continues to own live operation until Python demonstrates parity.

### Python Sovereignty milestone

Python Sovereignty is reached when:

> **The Python AlienIntent implementation can operate AlienIntent development end-to-end without invoking the Node implementation and passes the complete behavioral conformance, live self-hosting, recovery, and evidence suite.**

Only then is Node retired.

## Why

One repository preserves provenance, keeps behavioral comparison practical, and avoids maintaining two separate products.

---

# Summary principles

The recommendations above are driven by four defaults:

> **Convention over configuration.**

> **Solve for N architecturally; optimize the default experience for N=1.**

> **Use ports/adapters wherever something can reasonably vary outside the core domain.**

> **Escalate configuration, isolation, and assurance only when risk or user choice warrants it.**

---

# Decisions most worth challenging before implementation

The recommendations most likely to materially shape AlienIntent are:

- #6 — PR-based source-control workflow
- #11 — three risk classes
- #12 — disposable containers as production execution default
- #14 — SQLite default / PostgreSQL scale-out
- #31 — CLI + OCI container packaging
- #35 — no dedicated web UI for MVP
- #40 — Node and Python coexist in the same repository

These should be reviewed explicitly before implementation authority is granted.
