# AlienIntent Canonical Architecture

> Design target, not a statement of shipped commands or completed capabilities.
> Current runtime usage and limits are in [operations](../operations.md).

**Status:** Canonical design baseline

## Canonical mission

> **AlienIntent preserves current execution intent and authority across discontinuous agent work, constrains execution, independently verifies outcomes, recovers deterministically, and makes the process operable without requiring reconstruction of conversational history.**

AlienIntent is not the feature-specification system, planning engine, task decomposer, or general workflow engine.

```text
GitHub Spec Kit
    constitution
    specify
    clarify
    plan
    tasks
    analyze / checklist
    workflows / extensions
          ↓
Agent Ready + BIU Builder
          ↓
GitHub Issue
          ↓
AlienIntent
    execution authority
    intent continuity
    role-specific context
    admission
    worker/resource ownership
    Morty execution
    JC verification
    restart/replay/recovery
    ACCEPT → DONE closure
    operator control surface
          ↓
Bounded work-unit DONE
          ↓
Spec Kit converge
          ↓
Feature CONVERGED
```

> **Spec Kit owns what should be built. AlienIntent owns the reliable conversion of an approved bounded work unit into verified, operationally complete software.**

## Explicit non-responsibilities

AlienIntent MUST NOT become:
- a replacement for Spec Kit constitution;
- a requirements-authoring system;
- a feature-specification system;
- a planning engine;
- a general task decomposition engine;
- a generalized workflow engine;
- a feature-level convergence engine;
- a repository-wide branch-management system;
- an autonomous recovery agent;
- another planning LLM;
- a second copy of Agent Ready readiness logic;
- a second copy of Spec Kit task/workflow semantics.

## External principles incorporated

### Intent continuity over longer history

Longer history is not the same as current authority.

> **Preserve history; execute current intent.**

Historical artifacts remain evidence but do not remain authoritative merely because they are durable.

### Role-specific context

Context is compiled by **role + phase**.

- Morty continuing work: high continuity.
- JC: authoritative requirements and evidence, deliberate isolation from Morty's reasoning narrative.
- Operator: current state, blockers, supersession, resource ownership, safest valid next action.

### Reduce obsolete scaffolding

Every persistent instruction should eventually be classified:
- KEEP
- MOVE_TO_DETERMINISTIC_STATE
- MOVE_TO_CONTEXT_COMPILER
- SUPERSEDED
- REMOVE

> **State beats prompt prose.**

## Four canonical interfaces

1. Spec Kit → Agent Ready / BIU
2. Agent Ready / BIU → AlienIntent
3. AlienIntent → Spec Kit converge
4. Operator → AlienIntent

See `interface-contracts.md`.

## AlienIntent responsibilities

### Current execution authority

AlienIntent owns the answer to:
- what bounded Issue is being executed;
- what current Project phase applies;
- what Founder decisions apply;
- what implementation candidate is authoritative;
- what JC acceptance applies;
- what diagnostics are active versus superseded;
- what execution constraints remain;
- what actions are authorized at this phase.

AlienIntent references Spec Kit artifacts. It does not duplicate them as a second requirements store.

### Intent continuity

AlienIntent distinguishes:
- ACTIVE authority;
- SUPERSEDED authority;
- SATISFIED obligations;
- HISTORICAL evidence.

Persist new authority state only if deterministic projection from durable artifacts proves insufficient.

### Role-specific context compiler

Future API:

```text
compileContext(issue, role, phase)
```

Morty / IMPLEMENT:
- Spec Kit artifact references;
- specific task;
- BIU scope;
- baseline;
- acceptance criteria;
- proof requirements;
- current architecture authority;
- relevant implementation state;
- stop condition;
- escalation condition.

Morty / ACCEPT closure:
- accepted candidate/SHA;
- JC acceptance;
- landing state;
- deployment obligations;
- active Founder decisions;
- unresolved closure work;
- known non-blocking findings;
- stop condition.

JC / VERIFY:
- authoritative upstream references;
- BIU;
- candidate/diff;
- acceptance criteria;
- proof requirements.

Exclude Morty's reasoning narrative by default.

Operator:
- current workflow state;
- active invocation;
- authoritative result;
- superseded diagnostics;
- blockers;
- resource ownership;
- installed/candidate mismatch;
- safest valid next action.

### Deterministic workflow control

AlienIntent owns:
- invocation correlation;
- worker identity;
- admission;
- durable result parsing;
- Project transition authority;
- replay protection;
- restart recovery;
- closure routing;
- bounded resource ownership;
- operational completion evidence.

### Worker resource ownership

Per-Issue lanes are insufficient when workers share resources.

```text
resource: morty-worktree
capacity: 1
owner: invocation-id | null
```

This is deterministic mutual exclusion, not a generalized queue.

### Operator control surface

AlienIntent must answer:
1. Where am I?
2. Why am I here?
3. What is currently authoritative?
4. What blocks advancement?
5. What is the safest valid next action?
6. Can AlienIntent perform it?

### ACCEPT → DONE

AlienIntent owns work-unit operational closure.

DONE means the bounded work unit is landed, deployed/published when required, operationally verified when required, and free of known required work.

## Work-unit DONE versus feature CONVERGED

```text
AlienIntent DONE
    =
bounded work unit operationally complete

Spec Kit CONVERGED
    =
feature/specification complete
```

AlienIntent must not determine global feature completeness.

## Advisory evidence and stopping condition

> **Advisory work may run as long as useful, but it must never delay an authoritative handoff once all required evidence is satisfied.**

Every worker packet must contain:
- goal;
- starting authority;
- allowed scope;
- required evidence;
- stop condition;
- escalation condition.

## Prompt/scaffolding audit

Inventory:
- AGENTS.md;
- Morty bootstrap;
- JC bootstrap;
- skills;
- runbooks that instruct agents;
- repeated Issue boilerplate.

For each ask:
1. What demonstrated failure does it prevent?
2. Is it already deterministic?
3. Does the current model still require it?
4. Does it conflict with another instruction?
5. Can it move to structured state?
6. Can it be removed?

## Intended operator surface

Read-only first:

```text
alienintent status <issue>
alienintent explain <issue>
alienintent doctor
alienintent logs <issue>
alienintent version
alienintent resources
```

Later deterministic actions:

```text
alienintent continue <issue>
alienintent reconcile <issue>
alienintent install
alienintent upgrade
alienintent cleanup-owned
```

Expert/debug-only:

```text
alienintent emit ...
```

`emit` must feed EventRelay and never mutate lifecycle state directly.

## Branch/worktree ownership boundary

AlienIntent does not own general repository branch strategy.

AlienIntent may clean up only resources it explicitly owns.

> **Merge is not lifecycle completion. DONE is lifecycle completion.**

## Portability

Project-specific configuration may define:
- repository/project identity;
- bounded status mappings;
- worker roles;
- worker worktrees/resources;
- worker identities;
- Spec Kit artifact discovery rules.

This must not become a general workflow DSL.

## Metrics

Measure:
- input tokens / invocation;
- cached tokens / invocation;
- tool calls / invocation;
- repeated repository/GitHub reads;
- context bytes supplied;
- time to first authoritative action;
- time to authoritative result;
- rework transitions / Issue;
- Founder exceptions / Issue;
- operator interventions / Issue;
- context reconstruction ratio.

## Quality gate

> **Which demonstrated failure does this prevent?**

If none can be named, reject the mechanism.
