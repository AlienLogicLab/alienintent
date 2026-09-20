# AlienIntent — Software Factory + Project Cognitive Intelligence Factory

**Date:** 2026-09-20  
**Status:** Research-backed strategic direction  
**Authority:** Founder-approved strategic direction informed by prior-art research.  
**Implementation note:** This document guides architecture and roadmap decisions but does not by itself authorize implementation outside the approved AlienIntent work program.
**Supersedes:** [2026-09-20-cognitive-factory-strategy-pre-research.md](2026-09-20-cognitive-factory-strategy-pre-research.md) — the pre-research provisional record.
**Research basis:** [prior-art research spike](../research/alienintent-prior-art-cognitive-factory-research-spike.md).

## Strategic thesis

AlienIntent is evolving beyond an agent-orchestration system.

> **AlienIntent is an open, provider-neutral software factory that converts authorized requirements into verified software while building and governing the project-owned cognition, evidence, and specialized capabilities needed to improve how that software is understood and evolved over time.**

The factory therefore produces two durable outputs:

1. **Working software**
2. **Project-owned cognitive capability**

The second output may include governed requirements, architecture knowledge, decision history, Engineering Trajectory, Quality Evidence, project-specific knowledge, reusable skills, domain tools, specialized agent roles, routing knowledge, and accumulated operating experience.

The software is one product of the factory.

The durable specialized intelligence capable of continuing to evolve that software is the other.

## Category positioning

Prior-art research confirms that AlienIntent is **not inventing the software-factory category** and should make no such claim.

The field is already converging around AI software factories, requirements-to-work decomposition, persistent project memory, reusable agent skills, project knowledge bases, architecture drift detection, persistent orchestrators, multi-provider agents, self-evolving coding agents, trace-derived skills, and continuous agent improvement.

The closest systems found include:

- 8090 Software Factory;
- OpenVibely;
- Software Factory Foundation;
- Compound Engineering;
- MemoryGraph / Engram and related project-memory systems;
- self-evolving coding-agent research such as Socratic-SWE.

Therefore:

> **AlienIntent’s job is no longer to prove that this category should exist. The category is forming already. Its job is to build a materially better implementation of it.**

## What AlienIntent should compete on

### Project-owned cognitive sovereignty

> **Model providers supply replaceable reasoning capacity; the project owns its cognition.**

Project continuity must not depend on one model provider, one agent identity, one chat session, one proprietary memory system, or one vendor-specific orchestration surface.

AlienIntent owns persistent project cognition, project authority, project evidence, specialization rules, and learned project knowledge.

### Typed authoritative cognition

AlienIntent should avoid treating all durable knowledge as generic “memory.”

Project Cognition should consist of bounded, typed objects such as:

- Requirement
- Decision
- ArchitectureRule
- BIU
- Dependency
- Candidate
- Observation
- Verdict
- EngineeringTrajectory
- QualityEvidence
- HumanDecision
- ProviderCapability
- Skill
- Tool
- SpecialistRole

These objects have semantics, provenance, lifecycle, ownership, and authority rules.

### Explicit authority

Reasoning capability does not grant authority.

Director intelligence may interpret, plan, decompose, recommend, diagnose, and propose recovery.

It may not silently promote its own reasoning into Founder, product, architecture, security, deployment, or acceptance authority.

### Deterministic kernel + broad Director intelligence

AlienIntent should preserve a clear split.

**Director / Coordinator intelligence**
- interprets requirements;
- detects ambiguity;
- proposes decomposition;
- creates dependency graphs;
- diagnoses failures;
- proposes recovery;
- recommends providers/models;
- identifies missing authority.

**Deterministic kernel**
- owns canonical state;
- validates proposals;
- enforces lifecycle;
- enforces budgets;
- enforces capabilities;
- controls scheduling;
- controls candidate custody;
- controls verification admissibility;
- controls effect execution.

> **Intelligence proposes; deterministic policy disposes; authority remains explicit.**

### Definition ≠ Observation ≠ Verdict

AlienIntent must permanently separate:

- **Definition** — what must be true.
- **Observation** — what was actually observed.
- **Verdict** — whether the definition has been satisfied.

A worker statement such as “tests passed” is not itself a verdict.

### Factory-yield-driven specialization

Specialization should be justified by evidence that it materially improves:

- first-pass acceptance;
- rework rate;
- architecture adherence;
- drift prevention;
- escaped-defect rate;
- latency;
- cost;
- context efficiency;
- reliability.

> **Specialize because the factory data says to specialize.**

## Project Cognition

Project Cognition is the engineering-project adaptation of Persistent Contextual Cognition.

Its purpose is to preserve the durable intelligence necessary to understand and evolve the project independently of transient model sessions.

Potential contents include product intent, governed requirements, architecture authority, Ubiquitous Language, decisions, plans, dependency graphs, BIUs, current work state, Engineering Trajectory, Quality Evidence, known failure patterns, successful repair patterns, provider/model outcomes, learned project knowledge, specialized skills, specialized tools, unresolved questions, and operational knowledge.

> **Project Cognition is not just memory. It is governed institutional intelligence belonging to the project.**

## Better working environment for intelligence

AlienIntent should not rely primarily on increasingly elaborate prompts to force disciplined behavior.

> **Give intelligence a better working environment.**

Models should reason over bounded, authoritative objects whenever possible instead of reconstructing project truth through filesystem archaeology.

Semantic tools should increasingly look like:

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
simulate_schedule(wip)
request_human_decision(...)
```

This should reduce hallucination, wasted context, duplicated investigation, inconsistent interpretation, tool mistakes, and token burn.

## The Director / Coordinator

AlienIntent should retain a permanent Director / Coordinator capability.

Workers solve bounded tasks.

The Director maintains coherence across the engineering objective.

Responsibilities may include requirement interpretation, ambiguity detection, planning, BIU decomposition, dependency construction, context selection, provider/model proposal, failure diagnosis, rework strategy, authority-gap detection, and project-level coherence.

The Director itself should be provider-neutral:

```text
DirectorPort
    ├── ClaudeDirector
    ├── GPTDirector
    ├── GeminiDirector
    ├── LocalDirector
    └── EnsembleDirector
```

AlienIntent owns the Director identity and Project Cognition.

The model provider supplies reasoning capacity.

## Event-triggered intelligence

Persistent Director identity does not imply one permanently running model session.

AlienIntent should preserve durable Director role, Project Cognition, and project state.

Reasoning invocations occur when events require intelligence.

Examples:

```text
RequirementEnteredSPECIFY
PlanningRequired
VerificationRejected
BIUBlocked
BacklogExhausted
ArchitectureConflictDetected
ExecutionBudgetExceeded
HumanDecisionAnswered
ProviderUnavailable
```

Typical loop:

```text
event
  ↓
retrieve relevant cognition
  ↓
invoke appropriate intelligence
  ↓
receive structured proposal
  ↓
deterministic validation
  ↓
execute / reject / escalate
  ↓
record outcome
```

## Structured Director outputs

The Director should not drive workflow through free-form prose.

It should increasingly emit structured proposals that the deterministic kernel validates for schema, authority references, lifecycle legality, capabilities, budgets, and dependencies.

## Cognitive flywheel

AlienIntent should create a flywheel in which real project execution matures Project Cognition:

```text
project execution
      ↓
Engineering Trajectory
      ↓
Quality Evidence
      ↓
recurring pattern detected
      ↓
candidate project knowledge
      ↓
specialization materially beneficial?
      ↓
if justified:
   ├── knowledge object
   ├── retrieval strategy
   ├── skill
   ├── tool
   ├── specialist role
   ├── routing-policy proposal
   ├── context policy
   └── eventually specialized model
```

The project must operate for the cognition to mature.

## Skills are one artifact type, not the cognition system

Skills are already established prior art.

AlienIntent should treat them as one cognitive artifact type among several.

Potential progression:

```text
knowledge
→ patterns
→ retrieval structures
→ skills
→ tools
→ specialized roles
→ routing policies
→ evaluations
→ specialized models
```

Learning principle:

> **Propose, never dispose.**

## Specialization is project-dependent

Not every project requires sophisticated cognitive infrastructure.

A small project may need only requirements, architecture, decisions, and limited durable knowledge.

A large/complex project may justify architecture, requirements, security, regulatory, domain, operations, data, or verification specialists.

AlienIntent should possess the capability to manufacture specialized cognition when the project justifies it.

It should not create specialist-agent bureaucracy by default.

## Heterogeneous control intelligence

No single model is assumed optimal.

Example future routing:

```text
Architecture reasoning      → provider/model A
Requirements decomposition → provider/model B
Large-context analysis     → provider/model C
Routine coordination       → local specialized model
Implementation             → provider/model D
Verification               → independent provider/model E
Deterministic scheduling   → no model
```

## Prior-art implications

The research-backed conclusions are:

### 8090 Software Factory
Very close in Requirements, Blueprints, Work Orders, Knowledge Base, Skills, drift detection, and unified agent behavior.

### OpenVibely
Very close in persistent project context, memory, skill curation, autonomous SDLC loops, long-running goals, multi-provider agents, worktrees, and review workflows.

### Software Factory Foundation
Confirms that software factories with explicit roles, persistent memory, machine-readable architecture, structured handoffs, and self-improvement are becoming a category.

### Compound Engineering
Validates the principle that engineering knowledge should compound and influence future work.

### MemoryGraph / Engram
Show that low-level persistent project-memory and provenance systems already exist.

### Self-evolving agent research
Confirms that memory, skills, tools, models, and collaboration structures can evolve from software-engineering trajectories and executable feedback.

## What AlienIntent should not claim

AlienIntent should not claim invention of software factories, persistent project memory, project knowledge bases, reusable agent skills, requirements-to-work decomposition, architecture drift detection, persistent orchestration, self-evolving coding agents, trace-derived skills, or multi-provider agents.

AlienIntent’s value must come from the quality of its integrated implementation.

## Commercial interpretation

AlienIntent may eventually support a contract software-manufacturing model:

> **Provide authorized requirements; receive verified software.**

For sufficiently complex projects, delivery could also include governed requirements, architecture, decisions, Engineering Trajectory, Quality Evidence, Project Cognition, reusable skills, specialized tools, and project-specific intelligence assets.

A possible stronger proposition is:

> **Software plus a vendor-neutral, auditable cognitive operating system for continuing to evolve it.**

This remains a strategic hypothesis, not yet a validated commercial claim.

## Frontier creation environments

Frontier creation tools such as Google AI Studio / Antigravity, OpenAI Codex / ChatGPT Work, Anthropic Claude Artifacts / Claude Code, and future equivalents should be treated as upstream ideation/prototyping environments.

> **Create anywhere. Productionize through AlienIntent.**

AlienIntent should ingest their outputs through provider-neutral Artifact Intake rather than depend on provider UI internals.

## Build vs integrate

AlienIntent should likely own semantically:

- authority model;
- BIU semantics;
- lifecycle;
- deterministic kernel;
- evidence model;
- Candidate / Observation / Verdict semantics;
- Engineering Trajectory;
- Quality Evidence;
- Project Cognition domain model;
- Director proposal/validation boundary;
- specialization governance;
- factory-yield measurement.

AlienIntent should evaluate existing components before building:

- graph memory;
- vector retrieval;
- source graphs;
- code intelligence;
- generic skill formats;
- provenance stores;
- MCP-compatible tooling.

Storage technology is not the product.

Governed project cognition is.

## Roadmap relationship

This strategic direction must not derail the current implementation path.

```text
Wave 1
continuous autonomous software-factory control loop
        ↓
Wave 2
Requirements IR + Director-assisted Requirements→BIU compilation
        ↓
Project Cognition primitives
        ↓
Engineering Trajectory / Quality Evidence
        ↓
evidence-driven specialization
```

Wave 1 remains:

> **a prioritized READY backlog continuously executes to DONE without human per-BIU triggering.**

The cognitive-factory direction should influence boundaries and abstractions now where cheap.

It should not turn Wave 1 into a general cognition platform.

## Constitutional principles

### Cognitive sovereignty
> AlienIntent owns project cognition. Providers supply replaceable reasoning capacity.

### Specialization sovereignty
> AlienIntent owns the specialization framework, not the model vendor.

### Better working environment
> Give intelligence a better working environment rather than relying primarily on prompts to enforce discipline.

### Authoritative objects
> Reason over bounded, typed, authoritative project objects whenever possible.

### Persistent learning
> Useful project knowledge must survive transient model sessions.

### Evidence-driven specialization
> Specialize when project complexity and measured evidence justify it.

### Heterogeneous intelligence
> Use different models, deterministic systems, and specialists where each performs best.

### Explicit authority
> Reasoning capability does not itself grant decision authority.

### Definition / Observation / Verdict
> Keep these separate.

### Dual factory output
> AlienIntent builds both the software and, where justified, the durable specialized intelligence needed to continue evolving it.

## Research source record

The supporting prior-art research should be stored separately at:

`docs/research/2026-09-20-software-cognitive-factory-prior-art.md`

That research is the evidence record.

This document is the strategic interpretation of that evidence.

## Current strategic position

> **AlienIntent is an open, provider-neutral software and cognitive intelligence factory that converts authorized requirements into verified software while continuously building and governing the project-owned cognition, evidence, and specialized capabilities required to improve how the project is understood and evolved.**

This is not presented as a novel category claim.

The category is emerging already.

AlienIntent’s objective is to build a materially better implementation of it.


## Human Attention and Decision Routing

Human attention is a constrained factory resource and should be governed deliberately.

AlienIntent should not treat Slack, Teams, email, PagerDuty, or other communication systems as domain authorities. They are interaction adapters.

The durable capability is:

> **authority-aware human attention routing**

The subsystem determines:

- whether a factory event deserves human attention at all;
- who has authority to respond;
- how urgent the interruption is;
- which channel is appropriate;
- what bounded context is necessary to make the decision;
- whether the event can wait for a digest;
- how long AlienIntent may wait;
- when escalation is required;
- how the response becomes durable authority;
- how affected work resumes automatically.

### Why this is more than a Slack adapter

Current platforms already implement important pieces of this problem.

Slack's current agent guidance explicitly recommends human-in-the-loop controls, visible agent state, progressive trust, confirmation only when needed, and avoiding confirmation fatigue. Slack provides agent surfaces, interactive controls, task/status displays, and governance guidance suitable for an AlienIntent adapter.

OpenAI's Agents SDK supports durable interruptions and resumable runs around approval-required tool calls.

Microsoft Agent Framework supports request ports, persisted pending requests, checkpoints, and workflow resumption after a human response.

AWS's Agentic AI guidance explicitly recommends risk-tiered approval instead of routing every action through humans, with reviewer identity, timestamps, escalation paths, and auditable decisions.

Atlassian's Jira agentic-engineering guidance similarly frames human-in-the-loop as approvals, reviews, and uncertainty escalation placed only where human judgment changes the outcome.

These systems demonstrate that approval plumbing is becoming commodity infrastructure.

AlienIntent should therefore **not** attempt to differentiate by merely posting approval buttons to Slack.

Its value should be the higher-level factory semantics:

> **event significance + authority resolution + attention policy + durable decision capture + workflow resumption + measured attention efficiency**

### Proposed bounded capability

Working architecture label:

**Human Attention & Decision Routing**

This is not yet a final Ubiquitous Language term.

Possible domain concepts:

```text
AttentionEvent
DecisionRequest
DecisionAuthority
NotificationClass
EscalationPolicy
DecisionResponse
DecisionRecord
AttentionOutcome
```

Possible ports:

```text
HumanInteractionPort
NotificationPort
DecisionResponsePort
AuthorityResolverPort
```

Adapters may include:

```text
Slack
Microsoft Teams
Email
Telegram
Discord
PagerDuty
Generic Webhook
AlienIntent Control Plane
```

The core must not contain Slack/Teams/PagerDuty concepts.

### Notification classes

A simple initial classification:

#### INFORMATIONAL

Examples:
- milestone reached;
- Wave completed;
- release completed.

Default:
- record in Control Plane;
- optional digest;
- normally no immediate interruption.

#### ATTENTION

Examples:
- unusual rework count;
- provider degradation;
- dependency chain stalled;
- budget approaching threshold.

Default:
- asynchronous notification;
- may be batched/digested.

#### DECISION_REQUIRED

Examples:
- Founder/product/architecture decision;
- conflicting requirements;
- deployment authority required;
- capability request exceeds policy.

Default:
- create durable `HumanDecisionRequired`;
- route to authority owner;
- block only affected work;
- continue independent work;
- automatically resume after durable response.

#### CRITICAL

Examples:
- production outage;
- data-integrity risk;
- security event;
- repeated recovery failure.

Default:
- immediate multi-channel escalation according to deployment policy.

### Attention-routing loop

```text
Factory event
   ↓
classify significance
   ↓
human attention required?
   ├── no → record only
   └── yes
        ↓
resolve authority owner
        ↓
determine urgency / SLA
        ↓
select channel
        ↓
send bounded decision context
        ↓
receive response
        ↓
authenticate / validate authority
        ↓
create durable DecisionRecord
        ↓
resume affected work automatically
```

Communication history is not the authority ledger.

If a decision is made through Slack, Teams, email, or another adapter, AlienIntent must convert that interaction into a durable project-owned decision object.

### Minimum-interruption principle

AlienIntent should optimize for:

> **minimum human interruption consistent with correct authority and safe progress**

Routine verifier rejection, retries, scheduling, and expected lifecycle movement should not bother a human unless policy or repeated failure says otherwise.

A human should normally be interrupted only when human judgment materially changes what AlienIntent is authorized to do.

### Human attention as a factory-yield dimension

AlienIntent should measure human attention because measurable attention can be turned into operational value.

Candidate metrics:

- interruptions per accepted BIU;
- decision requests per accepted BIU;
- false-positive escalations;
- percentage of escalations that truly required human authority;
- decisions requiring follow-up clarification;
- median / p95 time-to-decision;
- total work time blocked waiting for human attention;
- percentage of independent work continuing during a blocked decision;
- percentage of decisions resolved asynchronously;
- escalation timeout rate;
- repeated unanswered escalation rate;
- notification volume by class;
- digest versus immediate-notification ratio;
- authority-routing accuracy;
- attention cost per accepted BIU;
- factory throughput lost to human waiting;
- recurring decision classes suitable for future delegated authority.

Long-term, Project Cognition may learn evidence such as:

- a particular decision class never requires Founder involvement;
- a security owner consistently handles one class faster and more accurately;
- routine verifier repair cycles should not generate notifications until a configured threshold;
- one channel produces faster responses for critical events than another;
- certain classes can safely be delegated under policy.

Such learning should produce proposed policy changes rather than silently expanding authority.

### Research conclusion

The market already contains strong building blocks for:

- notifications;
- Slack/Teams interaction;
- approval buttons;
- workflow pause/resume;
- risk-tiered approval;
- audit logs;
- escalation.

Therefore:

> **Communication adapters are commodity-ish. Human-attention governance is the AlienIntent capability worth owning.**

AlienIntent should integrate existing communication platforms rather than rebuild them.

The core product opportunity is to make human attention part of the deterministic factory-control model and Project Cognition.

### Roadmap placement

Do not derail Wave 1.

The concept already fits the approved `HumanDecisionRequired` / Decision Inbox direction.

Near-term:
- preserve a provider-neutral Human Interaction port;
- ensure `HumanDecisionRequired` carries enough structured context for external routing;
- ensure responses become durable decisions;
- ensure affected work resumes automatically.

Later:
- Slack/Teams/email/PagerDuty adapters;
- authority-aware routing;
- escalation policy;
- digesting/batching;
- attention metrics;
- evidence-driven routing/policy improvement.

### Strategic principle

> **Human attention is expensive factory capacity. Measure it, route it deliberately, and consume it only where human judgment creates value.**
