# AlienIntent — Software Factory + Project Cognitive Intelligence Factory

**Date:** 2026-09-20  
**Status:** Provenance — pre-research provisional strategy record. Retained for history; not current direction.  
**Superseded by:** [alienintent-software-cognitive-intelligence-factory.md](alienintent-software-cognitive-intelligence-factory.md), the research-backed record.  
**Why retained:** it states the pre-research thesis and the open questions (§16, §17, §21) that defined the prior-art spike; that framing is not reproduced in the successor.  
**Implementation authority:** This document records product direction and architectural principles discussed and accepted by the Founder. It does **not** by itself authorize implementation beyond already-approved Wave 1 / Wave 2 work.  
**Immediate priority remains:** complete the autonomous software-factory control loop before pursuing the deeper cognitive-intelligence-factory work.

---

## 1. Why this record exists

AlienIntent began as an attempt to make LLM software agents produce useful, verifiable outcomes without requiring the human Founder to act as a message bus between coding agents, reviewers, GitHub, and workflow state.

The near-term product direction became:

> **Authorized requirements in → verified working software out.**

The deeper direction developed from a further observation:

A mature software project does not merely need source code. It accumulates institutional knowledge, architectural decisions, product intent, requirements, operating history, engineering trajectory, quality evidence, failure patterns, model/provider performance, and reusable ways of reasoning about the system.

Today much of that knowledge becomes trapped inside chat transcripts, individual model sessions, local human memory, issue comments, disconnected Markdown, arbitrary logs, and filesystem archaeology.

The Founder explicitly wants AlienIntent to prevent that loss and build a flywheel in which project execution continuously matures the project’s own specialized intelligence.

The resulting strategic thesis is:

> **AlienIntent is a software factory plus a project cognitive intelligence factory.**

The software is one product of the factory.

The other product is:

> **durable specialized intelligence capable of continuing to understand, verify, evolve, and operate the software project.**

---

## 2. Core software-factory thesis

AlienIntent is intended to behave literally like a software factory.

For Alien Logic Lab projects, or eventually as a contract software-manufacturing system:

> **Provide authorized requirements; receive an application that satisfies those requirements.**

The factory should not require the customer or Founder to manage individual model sessions.

The intended operational model is:

```text
Product intent / requirements
        ↓
authorized Product Requirements
        ↓
SPECIFY
        ↓
PLAN
        ↓
TASKS
        ↓
BIUs
        ↓
Agent-Ready
        ↓
READY
        ↓
automatic eligible-work selection
        ↓
IMPLEMENT
        ↓
VERIFY
        ↓
REVIEW
        ↓
ACCEPT
        ↓
closure
        ↓
DONE
        ↓
working software
```

Given a populated backlog, external product priorities, sufficient execution authority, and no unresolved blocker, AlienIntent should continue consuming eligible work until the executable backlog is exhausted, external reality blocks progress, or a genuine authority decision is required.

Humans should manage **work and intent**, not model sessions.

---

## 3. The Director / Coordinator remains part of the final architecture

AlienIntent should not eliminate the reasoning role currently being performed manually by a long-running Claude coordinator session.

Instead, AlienIntent should internalize and govern that role.

A permanent **Director / Coordinator** capability remains valuable because deterministic workflow machinery alone is not sufficient for interpreting ambiguous requirements, detecting semantic conflicts, decomposing product requirements, constructing sensible BIU boundaries, identifying dependency DAGs, recognizing when several failures have one architectural root cause, deciding what context a worker needs, interpreting verifier findings, distinguishing routine repair from replanning, and identifying when a genuine Founder/product/architecture decision is required.

Target architecture:

```text
Founder / Product Authority
        ↓
AlienIntent
        │
        ├── Director / Coordinator Intelligence
        │      - interpret
        │      - plan
        │      - decompose
        │      - detect ambiguity
        │      - propose BIUs / DAGs
        │      - interpret failures
        │      - recommend recovery
        │      - propose provider/model routing
        │
        ├── Deterministic Kernel
        │      - canonical state
        │      - policy
        │      - lifecycle
        │      - scheduling
        │      - budgets
        │      - capabilities
        │      - candidate custody
        │      - evidence
        │      - verdict admissibility
        │
        └── Worker / Specialist Agents
               - PRODUCER
               - VERIFIER
               - future specialists
```

Constitutional operating principle:

> **Intelligence proposes; deterministic policy disposes; authority remains explicit.**

The Director reasons broadly.

The deterministic kernel authorizes narrowly.

---

## 4. AlienIntent owns the cognition

This is a constitutional principle.

> **AlienIntent owns the durable cognition required to operate the project. Model providers supply reasoning capacity; they do not own project memory, institutional knowledge, authority, identity, or continuity.**

Claude, GPT, Gemini, local models, and future providers are replaceable reasoning engines.

The project must remain intelligible and operable if any provider changes behavior, changes pricing, removes a model, loses compatibility, or disappears entirely.

The identity of an `AlienIntent Director` comes from AlienIntent:

```text
general intelligence
+ role
+ project cognition
+ tools
+ authority
+ evidence
+ accumulated experience
+ evaluation history
= specialized project intelligence
```

It does **not** come from the model vendor.

---

## 5. Project Cognition — PCC adapted to a software project

The prior Persistent Contextual Cognition idea becomes directly relevant when scoped to a project.

AlienIntent should eventually support **Project Cognition**: a durable, structured representation of the knowledge necessary for agents to reason about and operate a project.

Potential contents include product intent, governed requirements, architecture authority, Ubiquitous Language, decisions, dependency graphs, plans, BIUs, current work state, Engineering Trajectory, Quality Evidence, provider/model capabilities, provider/model outcome history, failure patterns, successful remedies, context-policy history, unresolved decisions, operational knowledge, relevant domain knowledge, and learned project-specific expertise.

This cognition should not depend on a single conversation, one frontier model, one local filesystem layout, or one human remembering everything.

AlienIntent owns it as a first-class project asset.

---

## 6. Bounded authoritative objects instead of filesystem archaeology

A major design principle emerged from the discussion:

> **Models should reason over bounded, typed, authoritative project objects whenever those objects exist.**

A Director should not normally be forced to reconstruct project truth with `grep`, `cat`, `git log`, `gh issue view`, and filesystem search.

Those tools remain useful for implementation and investigation.

But project truth should increasingly be accessible through semantic domain APIs such as:

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

Potential authoritative domain objects include:

```text
Requirement
Decision
ArchitectureRule
BIU
Dependency
Candidate
Observation
Verdict
QualityEvidence
EngineeringTrajectory
ProviderCapability
HumanDecision
```

The intent is not primarily to constrain the model.

The Founder explicitly preferred this formulation:

> **Give intelligence a better working environment.**

The objective is an environment in which disciplined behavior is natural, useful, efficient, and better informed rather than dependent on increasingly elaborate prompts.

This should reduce hallucination, wasted context, duplicated investigation, inconsistent interpretation, tool mistakes, and token burn.

---

## 7. Event-triggered cognition, not permanently running model sessions

A persistent Director does **not** imply one perpetual Claude/GPT/Gemini conversation.

AlienIntent should preserve persistent Director identity, persistent Project Cognition, and persistent factory state while using fresh reasoning invocations when an event actually requires intelligence.

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

Target loop:

```text
OBSERVE
   ↓
identify control problem
   ↓
retrieve relevant authoritative cognition
   ↓
invoke appropriate intelligence
   ↓
receive structured proposal
   ↓
deterministic validation
   ↓
execute / reject / escalate
   ↓
record result
```

This is cheaper and more reliable than leaving a frontier model continuously alive.

---

## 8. Structured proposals, not prose as control state

The Director should increasingly communicate with AlienIntent using structured proposals.

The deterministic kernel can then validate schema, referenced authority, decision class, lifecycle legality, capability requirements, and budget policy.

This preserves high-level model reasoning without turning free-form prose into canonical workflow authority.

---

## 9. Definition ≠ Observation ≠ Verdict

Another constitutional principle:

> **Definition ≠ observation ≠ verdict.**

### Definition
What must be true: requirements, acceptance criteria, architecture rules, SLOs, compatibility obligations.

### Observation
Evidence about reality: exit codes, test results, CI runs, changed files, candidate SHAs, workspace fingerprints, API responses, browser behavior, deployment health.

### Verdict
Policy/authority conclusion derived from definitions plus trusted observations: PASS, REJECT, requirement satisfied, architecture violation, deployment healthy, ACCEPT.

Neither a worker nor an observation may declare itself authoritative simply by saying "done".

---

## 10. The cognitive flywheel

The Founder’s key insight:

> **AlienIntent builds the flywheel for the project. The project must actually operate for the cognition to mature.**

Potential flywheel:

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
   ├── knowledge object
   ├── retrieval strategy
   ├── skill
   ├── tool
   ├── specialist role
   ├── routing-policy proposal
   ├── context policy
   └── eventually specialized model
```

Useful knowledge derived from project execution should become part of Project Cognition rather than remaining trapped in transient model sessions.

That accumulated cognition may ultimately become one of AlienIntent’s most valuable project assets.

---

## 11. Specialization should be evidence-driven and project-dependent

Not every project needs sophisticated cognitive infrastructure.

A small application may need only requirements, architecture, decisions, and a limited durable knowledge base.

A large or complex project may materially benefit from richer specialization.

Examples might include architecture, requirements, security, regulatory, domain, operations, data, and verification specialists.

AlienIntent should not create an agent zoo by default.

The rule is:

> **Specialize because project scale, complexity, and measured evidence demonstrate material benefit.**

When a sufficiently consequential specialization decision crosses product/architecture/operational authority, it remains a Founder or configured-authority decision.

The important product capability is:

> **AlienIntent can manufacture that cognitive infrastructure when the project justifies it.**

---

## 12. Heterogeneous control intelligence

No single model should be presumed optimal for every cognitive task.

AlienIntent should eventually support a heterogeneous intelligence architecture.

Example:

```text
Architecture reasoning      → provider/model A
Requirements decomposition → provider/model B
Large-context analysis     → provider/model C
Routine coordination       → local specialized model
Implementation             → provider/model D
Verification               → independent model/provider E
Deterministic scheduling   → no model
```

The Director itself should be a provider-neutral port.

Possible implementations:

```text
DirectorPort
    ├── ClaudeDirector
    ├── GPTDirector
    ├── GeminiDirector
    ├── LocalDirector
    └── EnsembleDirector
```

Selection should eventually be evidence-routed.

---

## 13. Skills are one output, not the whole cognition system

One likely mechanism for creating better working environments is **skills**.

But Project Cognition is broader than skills.

Potential outputs include:

```text
knowledge
→ patterns
→ retrieval structures
→ skills
→ tools
→ specialized roles
→ routing policies
→ evaluations
→ eventually specialized models
```

A skill should be promoted because accumulated evidence says it improves quality, cost, latency, reliability, first-pass yield, or context efficiency—not merely because an agent generated it.

Learning should generally follow:

> **propose, never dispose.**

Evidence may generate a proposed cognitive improvement.

Configured authority promotes it into active policy/skill/tooling.

---

## 14. Frontier creation environments become upstream suppliers

Frontier-model vendors are increasingly creating ideation/prototyping environments such as Google AI Studio / Antigravity, OpenAI Codex / ChatGPT Work, Anthropic Claude Artifacts / Claude Code, and future equivalents.

AlienIntent should not need to win the ideation-UI market.

Strategic position:

> **Create anywhere. Productionize through AlienIntent.**

Those systems become upstream creation surfaces.

AlienIntent takes their outputs through provider-neutral artifact intake and converts them into governed requirements, BIUs, and verified production software.

Externally generated code is input material, not architectural authority.

---

## 15. Commercial interpretation

The Founder is considering AlienIntent not only for Alien Logic Lab’s own projects but potentially as a **contract software-manufacturing system**.

Possible customer proposition:

> **Provide us with your authorized requirements. We return verified software that satisfies them.**

For projects where scale, complexity, and evidence justify it, the deliverable may eventually include not only software but also project-owned cognitive infrastructure:

```text
application
+ governed requirements
+ architecture knowledge
+ decision history
+ quality evidence
+ engineering trajectory
+ project cognition
+ specialized skills/tools
+ project-specific intelligence assets
```

This is materially different from conventional contract development.

The customer receives not merely the software artifact but potentially a durable cognitive capability for continuing to evolve the software.

No commercial model is canonized by this record.

---

## 16. Prior-art / competitive breadcrumbs

The Founder explicitly believes the underlying idea is unlikely to be unique and wants deeper prior-art research before treating the category thesis as novel.

High-priority breadcrumbs:

### 8090 Software Factory
Investigate project Knowledge Base, institutional knowledge preservation, requirements/blueprints/work orders, agent curation, recurring skills, and whether project cognition is treated as a first-class deliverable.

Starting point:
https://docs.8090.ai/

### OpenVibely
Investigate persistent project context, memory, agents, workflows, multi-provider orchestration, and whether it effectively creates project-owned specialized cognition.

Starting point:
https://github.com/openvibely/openvibely

### Software Factory Foundation
Investigate persistent agent memory, machine-readable architecture, planning/work management, continual improvement, verifiable deployment, and standards overlap.

Starting point:
https://softwarefactory.org/

### Every / Compound Engineering
Investigate compounding engineering knowledge, learnings → reusable skills, skill promotion/governance, and how much durable project cognition exists beyond Markdown/skills.

Starting point:
https://github.com/EveryInc/compound-engineering-plugin

### Project-memory systems
Investigate MemoryGraph, Mnemic, Engram, Menhir, aictx Memory, Codebase-Memory, and similar systems for temporal/provenance support, typed objects, graph relationships, governed writes, retrieval, and project-level institutional knowledge.

### Self-Evolving Coding Agents research
Investigate research on agents that evolve memory, skills, tools, models, collaboration structures, and policies using engineering trajectories and executable feedback.

Previously surfaced reference requiring independent verification during the formal spike:
https://arxiv.org/abs/2608.03392

### Socratic-SWE
Investigate mining historical solving trajectories, structured reusable skills, measurable improvement from prior failures/repairs, and implications for evidence-driven specialization.

Previously surfaced reference requiring independent verification during the formal spike:
https://arxiv.org/abs/2606.07412

---

## 17. Questions for the prior-art research spike

1. Who already explicitly treats software **and project-specific durable intelligence** as co-products?
2. Which systems preserve project cognition independently of model-provider sessions?
3. Which products generate new skills/tools/agents from project execution evidence?
4. Which systems treat requirements, architecture, decisions, evidence, and trajectories as typed authoritative objects?
5. Which systems support project-specific specialist agents created from accumulated evidence?
6. Which systems commercially promise "requirements in → verified software out"?
7. Which open-source systems already implement enough of this that AlienIntent should integrate rather than rebuild?
8. Which concepts are well-established in academic literature?
9. What terminology already exists for this category?
10. What is actually novel, if anything, in AlienIntent’s proposed integration?
11. Which ideas are patent-encumbered, restrictively licensed, or risky to copy?
12. Which prior systems failed, and why?
13. What minimum cognitive substrate should AlienIntent build itself versus consume from an existing memory/knowledge framework?

---

## 18. Do not lose the current execution thread

This exploration must **not derail the existing AlienIntent implementation plan**.

Immediate path remains:

```text
Wave 1
continuous autonomous software-factory control loop
        ↓
Wave 2
Requirements IR + Director-assisted Requirements→BIU compilation
        ↓
Wave 2B
frontier creation-tool / Artifact Intake
        ↓
Wave 3+
factory yield, learning, cognitive specialization
```

The cognitive-intelligence-factory concept should influence architecture now where cheap to preserve optionality.

It should **not** cause Wave 1 to expand into a general cognition platform.

Bread crumbs back to immediate work:

- `docs/decisions/alienintent-software-factory-plan.md`
- `docs/work-units/sf-wave1-plan.md`
- Wave 1 BIUs PY-02 through PY-10
- Wave 1 goal:
  > a prioritized READY backlog continuously executes to DONE without human per-BIU triggering.

The cognitive work becomes increasingly relevant after Project Cognition primitives, Requirements IR, Engineering Trajectory, Quality Evidence, and enough real execution evidence exist to justify specialization.

---

## 19. Constitutional principles captured from this discussion

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
> Specialize when project complexity and evidence justify it.

### Heterogeneous intelligence
> Use different models, deterministic systems, and specialists where each performs best.

### Explicit authority
> Reasoning capability does not itself grant decision authority.

### Definition / Observation / Verdict
> Keep these separate.

### Dual factory output
> AlienIntent builds both the software and, where justified, the durable specialized intelligence needed to continue evolving it.

---

## 20. Current strategic thesis

> **AlienIntent is an open, provider-neutral software and cognitive intelligence factory. It converts authorized requirements into verified software while continuously accumulating the project-owned cognition, evidence, tools, skills, and specialized intelligence needed to improve how that software is understood and evolved over time.**

This is a strategic thesis requiring deeper prior-art research before any claim of novelty.

It is nevertheless important enough to preserve now because it should influence how AlienIntent models cognition, authority, evidence, roles, provider abstraction, requirements, trajectories, learned knowledge, and future specialization.

---

## 21. Next research action

Perform a dedicated prior-art / competitive / academic research spike.

Start with:
1. 8090 Software Factory;
2. OpenVibely;
3. Software Factory Foundation;
4. Compound Engineering;
5. governed project-memory systems;
6. self-evolving coding-agent research;
7. Socratic-SWE;
8. adjacent "AI software factory", "agentic SDLC", "organizational memory", "institutional cognition", "software digital twin", "self-improving agent", and "AI-native engineering organization" literature.

Output should distinguish:
- direct competitors;
- adjacent products;
- infrastructure/substrates;
- research;
- useful ideas;
- likely commodity capabilities;
- possible AlienIntent differentiation;
- open-source components worth adopting;
- terminology/category precedents.

Do not treat the preliminary survey as sufficient evidence of novelty.
