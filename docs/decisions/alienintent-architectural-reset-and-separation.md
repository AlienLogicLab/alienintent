# AlienIntent Architectural Reset, FactoryChecks Separation, and Integration Model

**Date:** 2026-09-18  
**Status:** Durable architectural record  
**Owner:** Alien Logic Lab  
**Product:** AlienIntent  
**Previous working name:** B-DISP

---

# 1. Purpose of this record

This document makes durable the decisions and reasoning established while separating AlienIntent from FactoryChecks and redefining AlienIntent as an independent Alien Logic Lab product.

It exists specifically to prevent future agents from:

- treating accidental implementation choices as permanent architecture;
- forgetting why certain workflow states exist or do not exist;
- conflating GitHub terminology with AlienIntent concepts;
- coupling AlienIntent to GitHub Projects, GitHub Issues, Node.js, or FactoryChecks;
- reusing FactoryChecks-specific infrastructure as if it were the AlienIntent product;
- silently inventing architecture without explicit product intent and approval.

The core rule is:

> **AlienIntent must be designed with intent. Existing implementation history is evidence and behavioral reference, not architectural authority.**

---

# 2. Product identity

The permanent public product name is:

> **AlienIntent**

Parent organization:

> **Alien Logic Lab**

AlienIntent was previously developed under the working name **B-DISP**.

B-DISP originated inside FactoryChecks as execution/orchestration infrastructure. The extracted code demonstrated useful behavior, but the extraction itself does **not** define the permanent AlienIntent product architecture.

AlienIntent is now an independent Alien Logic Lab product.

---

# 3. Architectural reset

The current implementation inherited from B-DISP is Node.js-based.

That is an **implementation fact**, not an approved product architecture decision.

The product owner did **not** choose Node.js as AlienIntent's canonical language or platform.

Therefore:

> **The existing Node.js implementation is a behavioral prototype/reference implementation. It is not the architectural authority for AlienIntent.**

AlienIntent must not become:

> “a JavaScript artifact that escaped FactoryChecks.”

It must become:

> **a deliberately designed independent product whose implementation follows approved product intent, architecture, constraints, and engineering standards.**

The required order is:

```text
Product Intent
    ↓
Domain Model
    ↓
Architecture
    ↓
Constraints
    ↓
Technology Selection
    ↓
Implementation
```

Not:

```text
Existing code happens to use technology X
    ↓
therefore technology X becomes architecture
```

---

# 4. Canonical implementation direction

The intended canonical implementation language is **Python**, subject to explicit architectural design and migration planning.

The reasons are product-specific, not language-fashion arguments.

AlienIntent is primarily:

- an orchestration/control-plane system;
- an agent execution coordinator;
- a lifecycle-policy engine;
- a verification/evidence system;
- an integration system;
- a future model-routing and engineering-quality learning system.

Python aligns strongly with:

- AI/model tooling;
- agent providers;
- evaluation tooling;
- embeddings and local models;
- observability and experimentation;
- filesystem/process control;
- subprocess orchestration;
- APIs;
- databases;
- policy engines;
- future quality-analysis work.

The current Node implementation must remain available as the **behavioral oracle** until Python reaches demonstrated parity.

The migration must be behavior-preserving, not a rewrite-by-memory.

---

# 5. Binding architectural constraints

AlienIntent must strictly conform to:

1. **Domain-Driven Design (DDD)**
2. **Hexagonal Architecture**
3. **Explicit Anti-Corruption Layers (ACLs) at external boundaries**
4. **Python language-specific software engineering best practices**
5. **Alien Logic Lab EOS inheritance and contribution rules**
6. **Architectural fitness rules that mechanically enforce critical dependency boundaries**

These are mandatory design constraints.

---

# 6. DDD mandate

AlienIntent must model the AlienIntent domain in AlienIntent language.

The domain model must not be defined by GitHub, Jira, Codex, Claude, FastAPI, PostgreSQL, or other external technologies.

Candidate domain concepts include:

- Product Intent
- Work Item
- Execution Unit
- Lifecycle State
- Lifecycle Transition
- Readiness Evidence
- Execution Authorization
- Invocation
- Worker
- Provider
- Verification
- Review
- Acceptance
- Closure
- Engineering Trajectory
- Quality Evidence
- Policy
- Provider Capability
- Cost
- Outcome

These are hypotheses to be refined through domain modeling.

DDD does **not** mean mechanically creating entities, repositories, aggregates, and value objects everywhere.

DDD means:

- model the actual domain;
- establish a ubiquitous language;
- identify real bounded contexts;
- protect semantic boundaries;
- preserve product meaning independently of external system terminology;
- use tactical DDD patterns only where justified by domain complexity.

---

# 7. Bounded contexts

AlienIntent must not become one undifferentiated domain model.

Likely bounded-context candidates include:

- Work Definition
- Execution
- Verification
- Evidence
- Policy / Learning
- Integration

These are **bounded-context hypotheses**, not final declarations.

They must be validated through domain modeling.

---

# 8. Hexagonal architecture mandate

AlienIntent Core must depend on AlienIntent concepts and ports.

External systems must exist behind adapters.

Conceptually:

```text
                         AlienIntent Core
                               |
                              Ports
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
   Work Management       Source Control       Agent Provider
        Port                  Port                  Port
          |                    |                    |
     +----+----+          +----+----+          +----+----+
     |         |          |         |          |         |
   GitHub     Jira      GitHub    GitLab      Codex    Claude
  Projects
```

GitHub must not become AlienIntent's ontology.

Jira must not become AlienIntent's ontology.

Codex must not become AlienIntent's ontology.

Git must not become AlienIntent's ontology.

They are integrations.

---

# 9. Anti-Corruption Layer mandate

External objects must not leak directly into the domain.

Bad:

```python
def process_project_v2_item(item: GitHubProjectV2Item):
    ...
```

inside the domain/application core.

Correct conceptual flow:

```text
GitHub webhook
      ↓
GitHub adapter
      ↓
GitHub anti-corruption layer
      ↓
AlienIntent domain event
      ↓
AlienIntent use case
```

Likewise:

```text
Jira API payload
      ↓
Jira adapter
      ↓
Jira anti-corruption layer
      ↓
AlienIntent WorkItem / lifecycle concept
```

External terminology dies at the boundary.

---

# 10. Core versus adapters

AlienIntent should ultimately support interchangeable implementations such as:

```text
work_management/
    github_projects
    jira
    linear
    gitlab_issues
    azure_devops

source_control/
    github
    gitlab
    bitbucket
    azure_repos

agent_providers/
    codex
    claude
    future providers
```

AlienIntent must be able to support a configuration such as:

```text
work_management = jira
source_control = github
```

without requiring Jira to be mirrored into GitHub Projects.

That is a core architectural requirement for a genuinely independent product.

---

# 11. Python engineering standards

Python must be used deliberately and idiomatically.

At minimum:

- modern supported Python, initially target 3.12+ unless evidence dictates otherwise;
- `pyproject.toml` as canonical project configuration;
- complete type annotations across public domain/application interfaces;
- static type checking with a deliberate choice of `mypy` or `pyright`;
- `ruff` for linting and formatting enforcement;
- `pytest` for testing;
- property-based tests where state-machine or invariant-heavy behavior benefits;
- deterministic tests;
- explicit dependency injection through composition;
- no hidden service locator;
- no uncontrolled global mutable state;
- explicit exception taxonomy;
- structured logging;
- async only where concurrency or I/O justifies it;
- external libraries must not leak external types into the domain;
- framework magic must not define the architecture;
- packages such as FastAPI, Pydantic, SQLAlchemy, GitHub SDKs, etc. are tools, not architectural foundations.

Architecture boundaries must be mechanically tested where practical.

Example dependency intent:

```text
domain/
    may depend on:
        Python standard library
        domain-owned abstractions

    must not depend on:
        github
        jira
        fastapi
        sqlalchemy
        codex
        anthropic
        vendor SDKs

application/
    may depend on:
        domain
        ports

adapters/
    may depend on:
        application
        ports
        external SDKs

composition/
    wires implementations together
```

---

# 12. EOS relationship

AlienIntent is an Alien Logic Lab project.

It must both **inherit from** and **contribute to** Alien Logic Lab EOS.

Conceptual relationship:

```text
                    AlienLogicLab
                         |
                        EOS
                  organizational system
                         |
              +----------+----------+
              |                     |
              v                     v
         AlienIntent          other ALL projects
              |
              | reusable discoveries
              v
             EOS
```

## EOS → AlienIntent

AlienIntent must inherit applicable:

- engineering principles;
- project conventions;
- architecture governance;
- decision-record conventions;
- development methodology;
- evidence standards;
- quality expectations;
- agent operating rules;
- reusable tooling;
- organizational learning.

## AlienIntent → EOS

AlienIntent must contribute reusable discoveries such as:

- improved DDD/Hexagonal patterns;
- agent-engineering methodology;
- architecture fitness functions;
- verification patterns;
- trajectory/evidence practices;
- autonomous-development lessons;
- generalized Python engineering standards;
- reusable integration patterns;
- lifecycle-management practices.

AlienIntent is both an EOS consumer and an EOS proving ground.

---

# 13. Existing Node implementation: what is retained

The Node implementation is retained as a behavioral reference until Python parity is demonstrated.

Behaviors that have earned preservation include, subject to explicit verification:

- exact invocation correlation;
- stale-result rejection;
- isolated disposable worktrees;
- fail-closed admission;
- worker identity separation;
- deterministic verification;
- result authentication;
- recovery semantics;
- signed webhook handling;
- explicit execution authorization;
- lifecycle transitions;
- closure semantics;
- durable operational evidence.

The JavaScript module hierarchy itself has no architectural authority.

The correct migration model is:

```text
Existing Node implementation
        |
        v
observable behavior
tests
failure semantics
state transitions
security rules
        |
        v
behavioral/conformance specification
        |
        v
new Python AlienIntent implementation
```

The migration must ultimately support a conformance suite that verifies equivalent observable behavior.

---

# 14. Migration sequence

Do not begin a blind rewrite.

Preferred sequence:

```text
Phase 1
Freeze current behavior as executable contracts.

Phase 2
Create AlienIntent Product Intent and Ubiquitous Language.

Phase 3
Create bounded-context and Hexagonal architecture specifications.

Phase 4
Define ports and language-neutral behavioral contracts.

Phase 5
Define Python engineering standard and architectural fitness rules.

Phase 6
Implement Python core incrementally.

Phase 7
Implement GitHub work-management adapter and source-control adapter.

Phase 8
Implement provider adapters.

Phase 9
Run Node and Python against the same conformance expectations.

Phase 10
Run AlienIntent self-hosting proof using Python implementation.

Phase 11
Retire Node implementation only after parity and operational proof.
```

---

# 15. GitHub terminology

GitHub uses overloaded terminology.

AlienIntent documentation must distinguish the following precisely.

## GitHub App

A GitHub App is **not software installed into an operating system**.

It is a GitHub-side:

- machine identity;
- permission definition;
- event subscription definition.

A useful mental model:

> **The GitHub App is AlienIntent's GitHub security badge.**

## GitHub App installation

A GitHub App installation is GitHub's term for:

> **an organization or account granting that App access to selected resources.**

Nothing is installed on Linux, Windows, macOS, or a server.

## App private key

A credential used by software to prove that it is the registered GitHub App.

## Installation access token

A short-lived GitHub token issued after authenticating as the App for a specific GitHub App installation.

## Webhook

An HTTP request GitHub sends to AlienIntent when a subscribed event occurs.

Useful mental model:

> **The webhook is GitHub ringing AlienIntent's doorbell.**

## GitHub Project

A GitHub-hosted configurable project/work-management workspace.

It can provide:

- Kanban-style boards;
- tables;
- roadmaps;
- custom fields;
- workflow states;
- filters;
- grouping;
- charts;
- automations.

It is not a repository.

It is not source code.

It is not inherently the AlienIntent domain model.

---

# 16. How AlienIntent updates GitHub

The GitHub App provides identity and authorization.

The protocol/interface is the GitHub API over HTTPS.

Conceptually:

```text
AlienIntent
   |
   | HTTPS
   | Authorization: installation access token
   |
   v
api.github.com
```

AlienIntent may use GitHub REST and/or GraphQL APIs according to supported operations.

The conceptual layers are:

```text
GitHub App      = identity and authorization
GitHub API      = protocol/interface
GitHub Project  = hosted work-management data/model
AlienIntent     = application making decisions and issuing API operations
```

---

# 17. Project items and repository Issues

A GitHub Project may contain:

- GitHub Issues;
- Pull Requests;
- Project Draft Issues.

A Project Draft Issue can exist without belonging to a repository.

Therefore a Product Manager does **not** inherently need to know the final implementation repository merely to capture product intent.

Example:

```text
Project Draft Item:
    "Show supplier capability headroom during sourcing"

Lifecycle:
    CAPTURE
```

Later technical decomposition may create repository-bound implementation work.

This distinction must be considered when finalizing the FactoryChecks canonical backlog model.

---

# 18. Jira and other work-management systems

AlienIntent must not assume that GitHub Projects is universally authoritative.

A customer may use:

```text
Jira        = backlog/workflow
GitHub      = source control
AlienIntent = execution control
```

That must be a valid future architecture.

AlienIntent should then receive lifecycle changes from Jira and perform source-control work through GitHub.

Example:

```text
          Jira
           |
       lifecycle
           |
           v
      AlienIntent
           |
     +-----+------+
     |            |
     v            v
  GitHub       Codex
 source         worker
```

AlienIntent should therefore model:

> **Work Management Provider**

not:

> **GitHub Project**

GitHub Projects is the first adapter/reference implementation, not the universal architecture.

---

# 19. FactoryChecks versus AlienIntent

FactoryChecks and AlienIntent are now separate products/systems.

## FactoryChecks owns

- FactoryChecks product intent;
- FactoryChecks product backlog;
- FactoryChecks repositories;
- FC v2.0 Development Project;
- FactoryChecks-specific product planning.

## AlienIntent owns

- engineering-work orchestration;
- execution policy;
- lifecycle execution behavior;
- work isolation;
- verification;
- review coordination;
- evidence;
- provider routing;
- future learning/policy optimization;
- adapters to external work-management and source-control systems.

FactoryChecks is an early proving ground and future user of AlienIntent.

---

# 20. Existing FactoryChecks GitHub assets

The existing FactoryChecks GitHub Project, GitHub App, and webhook do not disappear simply because AlienIntent is separated from FactoryChecks.

They remain FactoryChecks-side infrastructure unless explicitly redesigned.

## FactoryChecks GitHub Project

Keep it.

It remains the FactoryChecks project-management/work-lifecycle surface.

## FactoryChecks GitHub App

Keep it for now.

It may remain the restricted GitHub machine identity used by the AlienIntent service when AlienIntent is configured to act on FactoryChecks resources.

The App does not contain AlienIntent.

The App does not execute AlienIntent.

The App is only a GitHub identity and permission boundary.

## FactoryChecks webhook

Keep it until deliberate cutover.

It may later notify the AlienIntent service responsible for FactoryChecks work.

---

# 21. Terminology for running AlienIntent

Avoid the phrase:

> **AlienIntent runtime**

unless specifically discussing executable code versus documentation/configuration.

It was confusing because “runtime” suggests a JRE-style interpreter/environment.

Use:

- **AlienIntent** = the software product
- **AlienIntent process/service** = a running copy of the application
- **AlienIntent deployment** = a configured running environment serving a particular engineering environment
- **profile** = deployment configuration
- **GitHub App** = GitHub machine identity and permissions
- **GitHub App installation** = GitHub granting that App access to an account/org/resources
- **webhook** = HTTP event notification
- **worker/agent** = Codex, Claude, etc.

Do not use the phrase:

> “FactoryChecks AlienIntent installation”

Use:

> **the AlienIntent deployment that manages FactoryChecks development**

---

# 22. Conceptual deployment model

The same AlienIntent application can be configured for different engineering environments.

Example:

```text
ALIENINTENT SELF-HOSTING

AlienLogicLab/alienintent
AlienIntent Project
AlienIntent GitHub App
        |
        v
AlienIntent service
        |
        v
agents
```

and separately:

```text
FACTORYCHECKS DEVELOPMENT

FactoryChecks repository/repositories
FC v2.0 Development Project
FactoryChecks GitHub App
        |
        v
AlienIntent service
        |
        v
agents
```

They may run on the same physical host or separate hosts.

They must use isolated:

- configuration;
- credentials;
- operational state;
- worktrees;
- installation identity.

Same software, different deployment configuration.

---

# 23. Why separate GitHub Apps

A single App could theoretically be granted access to multiple environments.

The preferred design uses separate restricted identities where practical to reduce blast radius.

Example:

```text
AlienIntent self-host GitHub App
    access:
        AlienLogicLab/alienintent

FactoryChecks GitHub App
    access:
        FactoryChecks resources
```

This prevents compromise of one App credential from automatically granting access to unrelated environments.

---

# 24. Future user experience

The manual GitHub App setup currently required during bootstrap is not the desired final user experience.

## Self-hosted AlienIntent

A future self-hosted experience should approach:

```text
alienintent init
```

followed by guided setup.

A GitHub App Manifest or equivalent automation should reduce manual configuration to a browser approval flow where possible.

The user should not have to manually reproduce a long GitHub configuration checklist.

## Hosted AlienIntent

A hosted AlienIntent service could own a public GitHub App.

Customers would:

1. choose "Install AlienIntent";
2. select their organization;
3. choose repositories;
4. approve permissions.

Alien Logic Lab would retain the App private key and operate the hosted service.

For self-hosting, customers should own their own App identity/private key.

---

# 25. FactoryChecks Product Backlog authority

Current approved FactoryChecks backlog rule:

> **GitHub Issues are the permanent canonical FactoryChecks Product Backlog.**

Current project rule:

> **FC v2.0 Development represents lifecycle state and views.**

However, GitHub Projects support draft issues that do not belong to repositories.

This creates an architectural question that should be explicitly reviewed:

> Should early product intent remain canonical GitHub Issues, or should early-stage Product Backlog items exist as Project Draft Issues until technical ownership/repository placement is known?

Do not silently change the existing FactoryChecks backlog authority rule.

Treat this as a Founder architecture/product-management decision.

---

# 26. Product Issue versus execution artifact

The distinction must remain:

> **The Product Backlog records product intent and planning.**

A Product Issue/item may be:

- exploratory;
- strategic;
- broad;
- incomplete;
- not yet assigned to a technical repository.

A bounded execution artifact is created only after decomposition/readiness work demonstrates that the work is sufficiently specified.

Execution readiness does not itself mean execution is authorized.

Explicit release into IMPLEMENT is the execution authorization boundary.

---

# 27. Canonical lifecycle

The complete work lifecycle must include the upstream definition stages and downstream execution stages.

Current lifecycle:

```text
CAPTURE
    ↓
SPECIFY
    ↓
PLAN
    ↓
TASKS
    ↓
READY
    ↓
IMPLEMENT
    ↓
VERIFY
    ↓
REVIEW
    ↓
ACCEPT
    ↓
DONE
```

The GitHub Project must not be reduced to only the runtime-dispatched portion.

The Project represents the authoritative lifecycle of work.

AlienIntent acts on lifecycle transitions according to explicit policy.

---

# 28. Why there is no MERGE state

This rule must never be preserved merely as:

> “No MERGE.”

The reason is architectural:

> **Merge is a repository operation, not a work-lifecycle semantic state.**

Lifecycle semantics:

```text
IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE
```

After ACCEPT, closure may include:

- merge/landing;
- publishing;
- deployment;
- bookkeeping;
- closing an Issue;
- recording evidence;
- other finalization.

If closure succeeds and no known work remains:

```text
DONE
```

If closure reveals that material implementation work remains:

```text
IMPLEMENT
```

There is no separate MERGE:

- queue;
- lane;
- lifecycle state;
- agent role.

Reasons:

1. Merge is an implementation detail of a source-control system.
2. Not all future AlienIntent-controlled work will require Git merge.
3. ACCEPT already represents authority accepting the result.
4. DONE represents completed operational closure.
5. MERGE would add ceremony without a new semantic state.

Durable rule:

> **Do not model repository mechanics as lifecycle semantics. Merge/landing is a closure operation performed after ACCEPT on the path to DONE, not a lifecycle state.**

---

# 29. VERIFY versus REVIEW

The distinction remains:

> **VERIFY should eliminate everything mechanically knowable before REVIEW spends model intelligence on judgment.**

## VERIFY

Examples:

- tests;
- build;
- types;
- lint;
- deterministic security checks;
- architecture gates;
- proven-red checks;
- mutation tests;
- ratchets;
- other mechanically evaluable criteria.

## REVIEW

Examples:

- Intent Fit;
- architecture;
- simplicity;
- maintainability;
- robustness;
- unnecessary abstraction;
- engineering judgment.

Recurring REVIEW findings that can be mechanized should graduate into VERIFY.

---

# 30. ACCEPT and closure

ACCEPT is the authority decision that the engineering result is acceptable.

After ACCEPT, closure performs operational finalization.

Closure may include source-control landing but is not synonymous with merge.

DONE means:

- required closure completed;
- required publication/deployment/landing completed when applicable;
- no known work remains for the item.

---

# 31. Quality and evidence direction

AlienIntent exists to improve the probability that agents produce useful, verifiable engineering outcomes.

The broader loop remains:

> **Measure engineering quality → learn agent behavior → apply better remedies → measure again.**

RAI:

```text
Produce
    ↓
Measure
    ↓
Critique
    ↓
Improve
    ↓
Measure Again
```

RAI is not autonomous model self-modification.

Trajectory and evidence must remain separate concepts:

- **Engineering Trajectory Record** = what happened;
- **Quality Evidence** = measurements and learning derived from what happened.

Git is a checkpoint/interoperability layer, not the complete engineering evidence record.

---

# 32. Model routing

Long-term model routing principle:

> **Use the least-capable model that can reliably satisfy the required engineering-quality bar.**

Routing must be informed by:

- task class;
- lifecycle stage;
- risk;
- quality requirement;
- provider capability;
- cost;
- observed historical performance.

Do not encode simplistic rules such as:

> “review = cheap model.”

---

# 33. Current separation work still outstanding

Before calling the FactoryChecks/AlienIntent separation finished:

## A. FactoryChecks backlog reconciliation

Complete the approved reconciliation of legacy FactoryChecks backlog sources against canonical GitHub backlog items.

The reconciliation must identify:

- existing mappings;
- duplicates;
- completion status;
- completion evidence;
- missing Product Items;
- legacy material that should become historical/supporting documentation.

## B. Add five FabSpace-derived Product Backlog items

The five durable candidate improvements discovered while examining FabSpace must be added after reconciliation approval.

Current remembered set:

1. guided inspector/facility walkthrough;
2. DFM feedback before sourcing;
3. KiCad/EDA integration;
4. virtual facility tour;
5. capability headroom instead of binary capability matching.

Before creation, verify final titles/descriptions against the retained source/reconciliation material.

## C. Correct AlienIntent Project lifecycle

The AlienIntent GitHub Project was initially configured with only:

```text
IMPLEMENT
VERIFY
REVIEW
ACCEPT
DONE
```

That is incomplete.

It must represent the full lifecycle:

```text
CAPTURE
SPECIFY
PLAN
TASKS
READY
IMPLEMENT
VERIFY
REVIEW
ACCEPT
DONE
```

Do not add MERGE.

## D. Create/fix AlienIntent GitHub App

AlienIntent self-hosting needs a GitHub App owned by AlienLogicLab and granted access to AlienLogicLab/alienintent.

This is separate from the existing FactoryChecks GitHub App.

## E. Complete live self-hosting proof

After App/profile/webhook setup, run the live proof.

Only then proceed to substantial autonomous AlienIntent backlog execution and later FactoryChecks field proving.

---

# 34. Current GitHub App contract from extracted implementation

The current extracted implementation expects, subject to architectural redesign:

- App owner: AlienLogicLab;
- App installation account: AlienLogicLab;
- selected repository access: `alienintent`;
- repository Issues: read;
- repository Metadata: read;
- organization Projects: write;
- subscriptions:
  - issue_comment;
  - projects_v2_item.

Workers currently publish Issue result comments through separate worker identities rather than through the App.

This is a property of the current implementation contract, not necessarily the final cross-provider AlienIntent architecture.

---

# 35. Self-hosting purpose

Self-hosting means:

> **AlienIntent uses AlienIntent to develop AlienIntent.**

Conceptually:

```text
AlienIntent Project
        |
        v
AlienIntent GitHub App
        |
        v
AlienIntent service
        |
        v
Codex / Claude / other workers
        |
        v
AlienIntent repository
```

Self-hosting is an operational proof.

It is not the definition of the product architecture.

---

# 36. FactoryChecks as proving ground

After AlienIntent self-hosting passes, FactoryChecks becomes the primary real-world proving ground.

The intended relationship:

```text
Product intent
    ↓
SPECIFY
    ↓
PLAN
    ↓
TASKS
    ↓
READY
    ↓
AlienIntent execution
    ↓
VERIFY
    ↓
REVIEW
    ↓
ACCEPT
    ↓
DONE
```

FactoryChecks development and AlienIntent validation then become the same real-world activity.

Do not freeze FactoryChecks indefinitely while perfecting AlienIntent infrastructure.

---

# 37. Governance rule for major architectural changes

AlienIntent itself must obey the methodology it is intended to enforce.

Therefore:

> **AlienIntent may not begin implementation of a major architectural change until the Product Intent, architecture, constraints, and acceptance criteria for that change have been explicitly captured and approved.**

This exists specifically to prevent accidental implementation decisions from silently becoming product architecture.

---

# 38. Anti-ceremony operating rule

Repository cleanliness matters, but known, understood, authorized work must never block execution merely because it is uncommitted.

> **Known authorized work is not dirt. Unexplained or conflicting work is the blocker.**

Protect against:

- real concurrency;
- authority ambiguity;
- destructive/irreversible state changes;
- live production changes;
- credential exposure;
- genuine conflicts.

Do not protect against imaginary collaborators or ceremonial cleanliness.

The human operator is not the message bus.

> **Evidence. Authority. Real risk. Execute.**

---

# 39. Immediate architectural deliverables before Python implementation

Before substantial Python implementation begins, create and approve:

1. AlienIntent Product Intent
2. Ubiquitous Language v1
3. bounded-context hypotheses
4. Hexagonal Architecture specification
5. core ports
6. Anti-Corruption Layer rules
7. Python engineering standard
8. EOS inheritance/contribution contract
9. behavioral compatibility inventory from Node implementation
10. architecture fitness rules
11. conformance-test strategy
12. Python migration plan

Only then begin the canonical implementation.

---

# 40. Final architectural statement

AlienIntent is not:

- a GitHub Project wrapper;
- a GitHub Issue bot;
- a Node.js artifact;
- a FactoryChecks subsystem;
- a Codex launcher;
- a Jira replacement;
- a Git-specific workflow engine.

AlienIntent is intended to become:

> **A vendor-neutral, evidence-producing agentic software-engineering control system that turns product intent into bounded, authorized engineering work; coordinates interchangeable agents and tools through explicit ports and adapters; verifies mechanical and qualitative requirements; preserves engineering trajectory and quality evidence; and learns from repeated execution without allowing external systems to define its domain model.**

Its architecture must be deliberate.

Its implementation must follow the architecture.

Its integrations must remain replaceable.

Its behavior must be evidence-driven.

Its own development must obey the same intent-first discipline it is built to enforce.
