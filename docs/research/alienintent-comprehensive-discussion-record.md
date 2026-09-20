# AlienIntent — Comprehensive Discussion Record

**Reconstructed through:** 2026-09-20  
**Scope:** AlienIntent-related product, architecture, strategy, methodology, research, lessons, and durable decisions discussed with ChatGPT.  
**Explicit exclusion:** operational coordinator instructions, copy/paste prompts to Claude/Codex, and step-by-step “what to do next” directions are intentionally omitted except where the outcome established a durable product or architectural decision.

This record goes back as far as the available conversation history and retained project context allow. Earlier references use **B-DISP** where that was the project name at the time.

---

## 1. Executive Summary

AlienIntent began as a response to a very practical problem: powerful coding agents could produce useful code, but they were not reliable enough to be trusted with unbounded interpretation, architecture, self-verification, workflow state, or project memory.

The system that began as **B-DISP** inside FactoryChecks became a standalone Alien Logic Lab product called **AlienIntent**.

The product direction matured into:

> **Authorized requirements in → verified working software out.**

The deeper strategic direction later became:

> **AlienIntent is a software factory plus a project cognitive intelligence factory.**

The software is one durable output. The other is the project-owned cognition, evidence, tools, skills, accumulated experience, and specialized intelligence needed to continue understanding and evolving that software.

The strongest constitutional principle is:

> **Intelligence proposes; deterministic policy disposes; authority remains explicit.**


## 2. Origin: FactoryChecks and B-DISP

B-DISP emerged from FactoryChecks development after repeated problems with frontier coding agents:

- loss of architectural intent;
- repeated rediscovery of prior decisions;
- scope drift;
- agents redefining the work while implementing it;
- self-grading;
- excessive token use;
- humans acting as a message bus between agents and tools;
- lack of durable execution evidence.

The practical objective became:

> **Make LLM agents produce useful, verifiable engineering outcomes.**

A foundational distinction emerged:

- Product Backlog belongs to the product/work-management side.
- Execution Queue belongs to the execution/control side.

A Product Issue may remain strategic or incomplete. A BIU must be bounded enough to execute.


## 3. BIU — Bounded Implementation Unit

BIU means:

> **Bounded Implementation Unit**

A BIU is not merely a task ticket. It is a bounded implementation contract whose intent, scope, constraints, dependencies, acceptance criteria, and verification expectations are explicit enough that an agent can execute it without inventing architecture or redefining the problem.

The long-term BIU contract includes:

- Intent;
- requirement links;
- fixed decisions;
- boundaries;
- dependencies;
- required capabilities;
- budgets;
- completion criteria;
- verification obligations;
- evidence obligations;
- non-goals;
- candidate-custody requirements;
- release policy.

This later aligned strongly with prior-art ideas around task contracts and requirements compilation.


## 4. Agent-Ready

Agent-Ready became the execution-readiness authority.

It answers:

> **Can this BIU be executed without requiring the implementation agent to make a new product or architecture decision?**

It should catch:

- unresolved owner clarifications;
- ambiguous scope;
- conflicting constraints;
- missing acceptance criteria;
- missing verification obligations;
- independent decision centers;
- semantic splits.

Important distinction:

- **Agent-Ready READY** = the contract is executable.
- **Project Status READY** = the BIU is eligible for release into execution.


## 5. Lifecycle

The full lifecycle became:

```text
CAPTURE
→ SPECIFY
→ PLAN
→ TASKS
→ READY
→ IMPLEMENT
→ VERIFY
→ REVIEW
→ ACCEPT
→ DONE
```

Key meanings:

- **CAPTURE** — product work exists.
- **SPECIFY** — requirement becomes explicit.
- **PLAN** — implementation/dependency strategy is formed.
- **TASKS** — bounded units are prepared.
- **READY** — a BIU is eligible for release.
- **IMPLEMENT** — producer performs the bounded work.
- **VERIFY** — mechanically knowable facts are checked.
- **REVIEW** — engineering judgment is applied.
- **ACCEPT** — authority accepts the engineering result.
- **DONE** — operational closure is complete.

No `MERGE` state was added because merge/landing is a repository operation, not a domain lifecycle state.

Durable rule:

> **Do not model repository mechanics as lifecycle semantics.**


## 6. VERIFY vs REVIEW

A durable distinction:

> **VERIFY should eliminate everything mechanically knowable before REVIEW spends model intelligence on judgment.**

VERIFY includes:

- tests;
- build;
- types;
- lint;
- security checks;
- architecture fitness;
- proven-red tests;
- mutation tests;
- ratchets;
- reproducibility checks.

REVIEW includes:

- intent fit;
- simplicity;
- maintainability;
- robustness;
- unnecessary abstraction;
- misplaced ownership;
- whether a simpler correct implementation was available.

Recurring REVIEW findings that can be mechanized should graduate into VERIFY.


## 7. Bounded Change and Minimum Necessary Work

A core engineering principle became:

> **Only change what is necessary to satisfy the approved scope.**

Agents should not perform:

- opportunistic refactoring;
- speculative abstraction;
- unrelated cleanup;
- unrelated dependency upgrades;
- architecture redesign;
- “while I am here” improvements.

A related rule:

> **Do not introduce a new mechanism unless the requirement cannot be satisfied correctly and more simply using an existing canonical mechanism.**

This later became a cross-lifecycle AlienIntent invariant covering IMPLEMENT, VERIFY, REVIEW, ACCEPT, and closure-to-DONE.

The quality objective is:

> **minimum correct code producing the required capability with no known defect.**


## 8. Architectural Reset

When B-DISP was extracted from FactoryChecks, the inherited Node implementation was explicitly demoted from architectural authority.

Binding reset:

> **AlienIntent must be designed with intent. Existing implementation history is evidence and behavioral reference, not architectural authority.**

Correct order:

```text
product intent
→ domain model
→ architecture
→ constraints
→ technology
```

not:

```text
existing code
→ therefore architecture
```


## 9. Python Canonical Direction

The Node implementation became the **bootstrap implementation**.

Canonical AlienIntent is being built in **Python**, deliberately chosen for its ecosystem around:

- agent tooling;
- orchestration;
- evaluation;
- evidence;
- learning;
- model/provider integrations;
- research tooling.

The Node implementation remains a behavioral oracle and temporary control plane.

Sovereignty path:

```text
Node bootstrap
→ executes BIUs that build Python AlienIntent
→ Python reaches parity/capability
→ Python proves itself live
→ Python becomes canonical
→ Node is retired
```


## 10. DDD, Hexagonal Architecture, and ACLs

AlienIntent adopted:

- Domain-Driven Design;
- Hexagonal Architecture;
- Anti-Corruption Layers.

The core domain must not leak concepts from:

- GitHub;
- Jira;
- Claude;
- Codex;
- source control;
- provider-specific APIs.

Examples:

- GitHub/Jira are Work Management adapters.
- Git is a Source Control adapter.
- Claude/Codex/Gemini are provider adapters.
- external vocabulary enters through ACLs.

Architecture fitness should mechanically enforce these boundaries.


## 11. Work Management vs Execution Authority

A binding split was established.

External Work Management owns canonical upstream state through READY:

- product backlog;
- priorities;
- CAPTURE/SPECIFY/PLAN/TASKS/READY;
- business context.

AlienIntent owns canonical execution-control/evidence state after release:

- IMPLEMENT through DONE;
- invocation;
- worker state;
- retries;
- recovery;
- candidate custody;
- execution evidence;
- cost/routing evidence.

External downstream statuses are projections of AlienIntent state, not competing authority.


## 12. Scheduling and Solve-for-N

Desired operating model:

> **Load the backlog, prioritize externally, and let AlienIntent continuously consume eligible READY BIUs.**

AlienIntent must not invent product priority.

Default scheduling:

1. highest-priority eligible READY BIU;
2. FIFO among equals/unprioritized;
3. skip blocked dependencies;
4. respect WIP/capacity;
5. refill slots automatically.

Default WIP:

> **one active mutating work stream**

Architecture:

> **solve for N**

Larger deployments may increase concurrency when dependencies and repository safety allow.


## 13. Automatic Release

A durable decision:

> **Automatic release defaults ON, configurable OFF.**

The current Node bootstrap does not implement READY → IMPLEMENT automatic release.

During Wave 1, the Claude coordinator temporarily fills that gap by moving eligible READY BIUs to IMPLEMENT under deterministic conditions.

This is temporary bootstrap behavior. Canonical Python AlienIntent should own the release policy directly.


## 14. Event-Driven Operation

AlienIntent is intended to be event-driven.

Polling is prohibited except by explicit approved exception.

External vendor events are translated through adapters/ACLs into domain events.

Effective exactly-once behavior is achieved through:

- at-least-once transport;
- dedupe;
- idempotency;
- correlation;
- reconciliation.

Relay/transport is not domain authority.


## 15. Durable Effects and Recovery

The architecture adopted:

- inbox;
- effect intent;
- outbox;
- expected versions;
- reservation fencing;
- idempotent external effects;
- read-back/reconciliation.

If an external effect has an unknown outcome:

> **block conflicting work rather than retry blindly.**

Full event sourcing is not required simply to obtain these properties.


## 16. Candidate Custody

A major invariant emerged:

> **Do not enter VERIFY until the exact candidate is durably identifiable and independently retrievable.**

This was learned after a producer created a local commit that a fresh verifier could not retrieve.

Candidate identity was generalized beyond Git.

Conceptually:

```text
CandidateRef
    ├── LocalArtifactCandidate
    ├── SourceRevisionCandidate
    ├── ArchiveCandidate
    └── future variants
```

Important rule:

> **Candidate immutability is a property of identity and custody, not storage technology.**

For content-addressed local artifacts, changed bytes imply a different candidate identity.


## 17. Independent Verification

Verifier independence is structural.

Default requirements:

- separate invocation;
- isolated workspace/context;
- exact candidate identity;
- separate provenance;
- no self-approval;
- no producer private reasoning/session.

Same model/provider/account/machine may be allowed under normal assurance. Stronger separation is configurable for high-assurance work.


## 18. Capabilities and Budgets

BIUs receive the authority they actually require.

Possible capabilities:

- shell;
- network;
- cloud APIs;
- DB migrations;
- service control;
- deployment authority.

Avoid microscopic permission bureaucracy.

Budget rule:

> **unknown or unreported consumption is not zero.**

Providers advertise which budget dimensions they can enforce.

Current CLI workers can hard-enforce dimensions such as:

- elapsed time;
- attempts;
- retries;
- concurrency;
- cancellation.

If a BIU requires a hard budget dimension that a provider cannot enforce, that provider is ineligible.


## 19. Provider Neutrality and Routing

AlienIntent is provider-neutral.

Long-term routing principle:

> **Use the cheapest capable provider that reliably satisfies the required quality bar.**

Prefer local models where they meet the quality requirement.

Routing should consider:

- task class;
- lifecycle stage;
- assurance;
- provider capability;
- historical performance;
- cost;
- latency.


## 20. Context Engineering

Context Engineering became first-class.

Six context classes were adopted:

- instructions;
- knowledge;
- memory;
- examples;
- tools;
- guardrails.

Important requirements:

- static/dynamic separation;
- provenance/versioning;
- task-specific assembly;
- progressive disclosure;
- context budgets;
- evidence linking context to outcome quality.


## 21. Project Cognition

Earlier Persistent Contextual Cognition ideas were recognized as highly relevant when scoped to an engineering project.

AlienIntent's project-scoped form became:

> **Project Cognition**

Potential contents:

- product intent;
- requirements;
- architecture authority;
- Ubiquitous Language;
- decisions;
- plans;
- BIUs;
- Engineering Trajectory;
- Quality Evidence;
- provider/model history;
- failure patterns;
- repair patterns;
- domain knowledge;
- operational knowledge;
- skills/tools;
- unresolved questions.

Key principle:

> **Project Cognition is governed institutional intelligence belonging to the project, not just “memory.”**


## 22. Cognitive Sovereignty

Constitutional principle:

> **AlienIntent owns project cognition. Providers supply replaceable reasoning capacity.**

The project should remain intelligible if a provider changes or disappears.

A specialized role such as the AlienIntent Director is defined by:

```text
general intelligence
+ role
+ Project Cognition
+ tools
+ authority
+ evidence
+ accumulated experience
+ evaluation history
```

not by the vendor.


## 23. Give Intelligence a Better Working Environment

A key Founder formulation:

> **Give intelligence a better working environment.**

Do not rely mainly on prompting to enforce discipline.

Instead of forcing agents to rediscover project truth through filesystem archaeology, provide semantic tools over bounded authoritative objects.

Examples:

```text
get_requirement(id)
get_biu(id)
get_decision(id)
get_architecture_rule(topic)
get_dependency_graph(scope)
get_factory_state()
get_verification_findings(biu)
get_evidence(requirement)
get_provider_performance(task_class)
request_human_decision(...)
```

Expected gains:

- less hallucination;
- less duplicated investigation;
- lower token burn;
- fewer tool mistakes;
- more consistent interpretation.


## 24. Director / Coordinator

AlienIntent should permanently include a Director/Coordinator capability.

Workers solve bounded tasks.

The Director maintains coherence across the broader objective.

Possible responsibilities:

- requirement interpretation;
- ambiguity detection;
- decomposition;
- dependency DAGs;
- context selection;
- failure diagnosis;
- recovery proposals;
- provider/model proposals;
- authority-gap detection.

The Director should be provider-neutral.

Conceptually:

```text
DirectorPort
    ├── ClaudeDirector
    ├── GPTDirector
    ├── GeminiDirector
    ├── LocalDirector
    └── EnsembleDirector
```

The Director reasons broadly; the deterministic kernel authorizes narrowly.


## 25. Event-Triggered Director Cognition

Persistent Director identity does not require a permanently running model session.

Persistent:

- Director role;
- Project Cognition;
- state.

Reasoning is invoked when an event actually needs intelligence.

Examples:

- PlanningRequired;
- VerificationRejected;
- BIUBlocked;
- BacklogExhausted;
- ArchitectureConflictDetected;
- HumanDecisionAnswered;
- ProviderUnavailable.


## 26. Definition ≠ Observation ≠ Verdict

A constitutional epistemic rule:

> **Definition ≠ Observation ≠ Verdict**

- Definition = what must be true.
- Observation = what was actually observed.
- Verdict = authorized conclusion.

A worker saying “tests passed” is not itself a verdict.

This principle became central to independent verification and evidence handling.


## 27. Engineering Trajectory and Quality Evidence

Two durable concepts must remain separate.

### Engineering Trajectory
What happened.

Examples:

- invocation;
- candidate;
- lifecycle transition;
- finding;
- repair;
- human decision;
- merge;
- deployment.

### Quality Evidence
What is measured or concluded from what happened.

Examples:

- first-pass acceptance;
- rework count;
- defect classes;
- architecture violations;
- cost;
- latency;
- human attention;
- provider performance.

Git is a checkpoint/interoperability layer, not the complete trajectory record.


## 28. Cognitive Flywheel

The project must operate for cognition to mature.

Conceptual flywheel:

```text
project execution
      ↓
Engineering Trajectory
      ↓
Quality Evidence
      ↓
recurring patterns
      ↓
candidate project knowledge
      ↓
specialization materially beneficial?
      ↓
if justified:
   ├── knowledge
   ├── retrieval strategy
   ├── skill
   ├── tool
   ├── specialist role
   ├── routing proposal
   └── eventually specialized model
```

Rule:

> **Useful learning must not remain trapped in transient model sessions.**


## 29. Evidence-Driven Specialization

Not every project needs sophisticated specialization.

A small project may need:

- requirements;
- architecture;
- decisions;
- limited knowledge.

A complex project may justify:

- architecture specialist;
- security specialist;
- requirements specialist;
- regulatory specialist;
- domain specialist;
- verification specialist.

Rule:

> **Specialize because the project scale, complexity, and measured evidence justify it.**


## 30. Heterogeneous Intelligence

No single model is assumed optimal.

Potential future routing:

```text
architecture reasoning      → provider A
requirements decomposition → provider B
large-context analysis     → provider C
routine coordination       → local specialist
implementation             → provider D
verification               → independent provider E
deterministic scheduling   → no model
```

This is a heterogeneous cognitive architecture.


## 31. Software Factory Direction

The product proposition matured into:

> **AlienIntent is a software-factory control plane that converts authorized product requirements into verified software through an event-driven, evidence-producing agentic engineering process.**

Human role should trend toward:

- ideation;
- product intent;
- priority;
- genuinely novel authority decisions.

Not routine agent/session management.


## 32. Frontier Creation Tools

Google AI Studio / Antigravity, OpenAI Codex / ChatGPT Work, Anthropic Claude Artifacts / Claude Code, and future systems were recognized as upstream ideation/prototyping environments.

Strategic position:

> **Create anywhere. Productionize through AlienIntent.**

Their output should enter through provider-neutral Artifact Intake rather than provider UI coupling.


## 33. Artifact Intake

Proposed input forms:

- repository/branch/commit;
- archive/project export;
- loose files;
- prototype/reference URL;
- supported provider API;
- optional session/intention evidence.

Three authority modes:

1. **Intent/prototype input** — expresses what the user wants.
2. **Candidate implementation input** — code may be reused but must pass normal factory controls.
3. **Reference input** — context only.

Externally generated code is input material, not architectural authority.


## 34. Prior-Art Research

A deeper research spike found that the broad category is not novel.

Important overlaps:

- **8090 Software Factory** — Requirements, Blueprints, Work Orders, Knowledge Base, Skills, drift detection, unified agent.
- **OpenVibely** — persistent project context, memory, skill curation, autonomous SDLC, multi-provider agents.
- **Software Factory Foundation** — category/standards convergence.
- **Compound Engineering** — compounding engineering knowledge.
- **MemoryGraph / Engram** — persistent project-memory/provenance substrates.
- **Self-evolving coding-agent research / Socratic-SWE** — trace-derived skill and learning loops.

Revised position:

> **AlienIntent's job is not to prove the category should exist. The category is forming. AlienIntent's job is to build a materially better implementation.**


## 35. Human Attention and Decision Routing

Slack/Teams/email/PagerDuty integration itself is not the strategic feature.

The higher-value capability is:

> **authority-aware human attention routing**

AlienIntent should decide:

- whether an event deserves interruption;
- who has authority;
- urgency;
- channel;
- context;
- escalation;
- how the answer becomes durable authority;
- how work resumes.

Human attention is treated as scarce factory capacity.


## 36. Human Attention Metrics

Possible measures:

- interruptions per accepted BIU;
- false-positive escalations;
- time-to-decision;
- work blocked waiting on people;
- authority-routing accuracy;
- attention cost per BIU;
- notification volume;
- recurring decision classes suitable for delegation.

Founder principle:

> **Measure everything that can be turned into value.**


## 37. Control Plane

AlienIntent requires a first-class Control Plane.

Capabilities discussed include:

- status;
- explain;
- replay;
- resume;
- reconcile;
- cancel;
- doctor;
- inspect BIUs/workers/invocations/events/evidence/cost/capabilities/adapters.

Operator-generated actions should flow through normal domain/event interfaces rather than mutate state directly.


## 38. Installer and Self-Hosting

`alienintent init` became a first-class direction.

It should eventually handle:

- repository auth;
- GitHub App setup/discovery;
- transport;
- providers;
- lifecycle mapping;
- secrets;
- service/control-plane setup;
- health;
- diagnostics;
- resume/rollback;
- noninteractive setup.

Self-hosted is canonical.

Alien Logic Lab is not required to host a cloud service.


## 39. EOS Relationship

AlienIntent inherits from Alien Logic Lab EOS.

EOS normalization created a coherent **EOS v1.0** baseline with:

- version identity;
- reviewed engineering principles;
- playbook ontology;
- project registry;
- strategic-initiative normalization;
- execution-record class;
- public-repository exception;
- conformance tooling.

AlienIntent is intended to inherit from EOS and contribute generalized improvements back through governance.


## 40. Pre-Python Gate Reclassification

A large pre-Python gate was created and then recognized as too bureaucratic.

Reclassification found:

- many items were already resolved by authority;
- several were implementation checklists;
- no real Founder-level decision blocked Python.

The gate became:

> **design/traceability backlog, not dozens of independent release blockers.**

This was an important correction against process ceremony.


## 41. PY-01 — Architecture Skeleton

PY-01 established the Python skeleton and architecture fitness tooling.

The first verifier rejected it because architecture checks could be bypassed.

Findings included:

- layering bypass through imports;
- vendor-type checks missing string annotations;
- vendor base classes not checked;
- path-dependent layer detection;
- nested annotation bypass;
- CI not enforcing the checks.

After repair, independent verification accepted the candidate.

Lesson:

> **Architecture checks must prove they fail on realistic violations, not merely pass on compliant code.**


## 42. Candidate Publication Lesson

PY-01 exposed that a local candidate commit was not necessarily retrievable by a fresh verifier.

This led directly to the custody invariant:

> **exact candidate must be durably identifiable and independently retrievable before VERIFY.**

This must eventually be control-plane enforced, not merely a worker instruction.


## 43. Node Bootstrap Verifier Permission Defect

The first autonomous Claude verifier failed because the Node bootstrap only allowed a permission mode incompatible with headless execution.

A narrow bootstrap fix corrected this.

Lesson:

> autonomous workers need capability configuration that actually supports autonomous operation.

The fix is bootstrap compatibility, not canonical Python capability architecture.


## 44. PY-02 — Execution Domain Kernel

PY-02 produced the first serious factory trajectory.

The first verifier rejected the candidate with three important defects:

### B1
Rework lost the bound execution contract, making DONE unreachable.

### B2
Producer-reported passing tests were environment-dependent and failed in a clean checkout.

### B3
WIP behavior was not genuinely tested; mutation did not break the suite.

This demonstrated:

- producer claims are not verdicts;
- independent reproduction matters;
- mutation/proven-red methods expose inert tests;
- execution environment provenance matters.

The repair was later accepted.


## 45. PY-02 Closure

After ACCEPT, closure stopped on missing landing authority.

This produced a standing closure policy.

After ACCEPT, closure should do only the minimum remaining work necessary to reach DONE.

For each closure obligation:

- already satisfied → record evidence;
- required + authorized → perform it;
- not required → record why;
- missing authority → Founder/Human decision exception;
- material implementation change → RETURN_TO_IMPLEMENT.

Landing must happen **inside the factory**.

Principle:

> **Human grants authority; AlienIntent executes.**


## 46. Start Learning Immediately

PY-02 produced enough evidence to justify capturing trajectories before the full cognition architecture exists.

Rule:

> **If the factory learns something useful, that learning must not exist only in a transient model conversation.**

Immediate direction:

> **Capture now; analyze later.**

Suggested temporary durable outputs:

```text
docs/evidence/execution-trajectories/PY-02.jsonl
docs/evidence/execution-trajectories/PY-02-summary.md
docs/evidence/quality/PY-02-quality-evidence.json
docs/evidence/quality/PY-02-quality-evidence.md
```

Raw trajectory and derived evidence remain separate.


## 47. PY-03

PY-03 implemented the durable operational store.

Its dependency became eligible automatically after PY-02 DONE.

It was re-assessed before execution because the contract/baseline had changed.

After verification and landing:

- accepted SHA remained preserved;
- accepted content remained unchanged;
- Node remained untouched;
- Python test coverage increased;
- architecture fitness remained green.

This showed the dependency-gated factory sequence was becoming repeatable.


## 48. PY-04 — Walking Skeleton

PY-04 is the offline continuous-factory walking skeleton.

It exposed:

- restart duplicate-dispatch concerns;
- durable correlation of worker result;
- capacity-stop semantics;
- bounded-retry ownership questions;
- offline candidate custody.

A valuable behavior appeared:

> minimum-necessary-work rules prevented PY-04 from absorbing retry functionality that belongs to PY-06.

This was an early sign that scope discipline could be operationally useful, not just rhetorical.


## 49. Offline Custody Decision

PY-04 raised the question of immutability without filesystem immutable flags.

Decision:

> **Use custody transfer to an independently retrieved verifier copy.**

The invariant is content-addressed, not Linux-filesystem-specific.

The verifier must verify the digest of the independently retrieved copy before VERIFY proceeds.

This preserved the domain abstraction while avoiding unnecessary infrastructure.


## 50. Continuous Coordinator Behavior

A crucial operating rule:

> **Advance work autonomously through the approved plan. Escalate only when progress requires genuinely missing authority.**

The coordinator should not stop for:

- routine BIU completion;
- ordinary dependency release;
- verifier-directed rework;
- expected state transitions;
- routine retry/recovery.

This is also the desired future behavior of the AlienIntent Director.


## 51. Temporary Node-Era Release Bridge

Until Python AlienIntent implements automatic release, the coordinator temporarily performs READY → IMPLEMENT when:

- Agent-Ready is READY;
- dependencies are satisfied;
- no authority gap exists;
- WIP allows it;
- no invocation is active;
- auto-release policy is ON;
- no hold exists.

The coordinator does not manually launch workers.

Node remains the active factory engine until Python sovereignty.


## 52. Python Sovereignty

Until PY-10 proves takeover:

> **Node bootstrap is currently running the factory process that builds Python AlienIntent.**

After sovereignty:

> **Python AlienIntent runs the factory itself.**

PY-10 is therefore the live proof of control-plane takeover, not just another feature test.


## 53. PY-10 Intended Proof

PY-10 is intended to demonstrate:

- multiple READY BIUs;
- priority ordering;
- equal-priority FIFO;
- dependency handling;
- WIP=1;
- automatic slot refill;
- HumanDecisionRequired;
- independent work continuing while one BIU blocks;
- durable human decision and resume;
- restart without duplicate effects;
- exact candidate custody;
- eventual DONE;
- no per-BIU human release once Python owns auto-release.

Product-level proof:

> **Given a prioritized backlog, sufficient execution authority, and no unresolved blockers, AlienIntent continuously consumes eligible READY BIUs until the executable backlog is exhausted.**


## 54. Software Factory + Cognitive Intelligence Factory

The deeper product thesis is now:

```text
application
+
governed requirements
+
architecture knowledge
+
decision history
+
Engineering Trajectory
+
Quality Evidence
+
Project Cognition
+
skills/tools
+
project-specific intelligence
```

For ALL, this becomes compounding engineering infrastructure.

For future contract software manufacturing, the proposition could become:

> **Provide authorized requirements; receive verified software and, where justified, the durable cognitive capability required to keep evolving it.**


## 55. Current Constitutional Principles

### Cognitive sovereignty
> AlienIntent owns project cognition. Providers supply replaceable reasoning capacity.

### Specialization sovereignty
> AlienIntent owns the specialization framework, not the model vendor.

### Better working environment
> Give intelligence a better working environment rather than relying mainly on prompts.

### Authoritative objects
> Reason over bounded, typed, authoritative project objects whenever possible.

### Persistent learning
> Useful project knowledge must survive transient model sessions.

### Evidence-driven specialization
> Specialize when project complexity and measured evidence justify it.

### Heterogeneous intelligence
> Use the appropriate mix of models, deterministic systems, and specialists.

### Explicit authority
> Reasoning ability does not itself grant authority.

### Definition / Observation / Verdict
> Keep these separate.

### Minimum necessary work
> Agents do no more than required by the BIU and lifecycle obligation.

### Dual factory output
> AlienIntent builds software and, where justified, the durable specialized intelligence needed to continue evolving it.


## 56. Current Strategic Position

The strongest current formulation is:

> **AlienIntent is an open, provider-neutral software and cognitive intelligence factory that converts authorized requirements into verified software while continuously building and governing the project-owned cognition, evidence, and specialized capabilities required to improve how the project is understood and evolved.**

This is not a novel-category claim.

The category already exists in pieces.

AlienIntent's ambition is:

> **build a materially better, more rigorous, more measurable, more autonomous implementation of it.**


## 57. Intentionally Excluded

This record intentionally omits:

- copy/paste coordinator prompts;
- exact Claude/Codex instructions;
- monitoring commands;
- temporary shell troubleshooting;
- manual GitHub UI steps;
- operational “what to do next” instructions.

Where those activities produced durable architecture, product, evidence, or policy lessons, the durable outcome is included instead.

---

## 58. Historical Continuity

AlienIntent's evolution can be summarized as:

```text
FactoryChecks agent workflow pain
        ↓
B-DISP execution control
        ↓
BIU + Agent-Ready
        ↓
self-hosting Node bootstrap
        ↓
architectural reset
        ↓
Python canonical implementation
        ↓
DDD / Hexagonal / ACL
        ↓
deterministic kernel + independent verification
        ↓
software-factory direction
        ↓
continuous backlog execution
        ↓
Requirements IR + Director
        ↓
Project Cognition
        ↓
Engineering Trajectory + Quality Evidence
        ↓
evidence-driven specialization
        ↓
software factory + cognitive intelligence factory
```

Near-term:

> finish the autonomous Python software factory.

Long-term:

> make the factory progressively better at building both the software and the durable intelligence required to evolve that software.
