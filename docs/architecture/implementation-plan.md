# B-DISP Implementation Plan

**Constraint:** Do not implement functionality owned by GitHub Spec Kit or Agent Ready.

## Phase 0 — Audit before expansion

Inventory:
- AGENTS.md;
- Morty bootstrap;
- JC bootstrap;
- agent-facing runbook instructions;
- Issue/BIU boilerplate;
- recovery instructions;
- skills;
- durable diagnostics;
- Founder decision patterns.

Classify:
- KEEP
- MOVE_TO_DETERMINISTIC_STATE
- MOVE_TO_CONTEXT_COMPILER
- SUPERSEDED
- REMOVE

Deliverable:
`docs/architecture/b-disp-scaffolding-audit.md`

Gate:
Every KEEP item names a demonstrated failure it prevents.

## Phase 1 — Read-only execution projection

Commands:

```text
b-disp status <issue>
b-disp explain <issue>
b-disp doctor
b-disp logs <issue>
b-disp version
b-disp resources
```

Must show:
- Spec Kit artifact references;
- BIU/Issue;
- current Project state;
- expected role;
- active invocation;
- latest authoritative local outcomes;
- deterministically provable supersession warnings;
- worker resource ownership;
- installed/worker revision differences;
- known vs unknown.

No mutation. No LLM explanation.

## Phase 2 — Context compiler

Interface:

```text
compile-context issue role phase
```

Outputs:
- Morty implement packet;
- Morty closure packet;
- JC verification packet;
- operator packet.

Measure:
- context bytes;
- input tokens;
- repeated GitHub/repository reads;
- context reconstruction ratio.

Acceptance:
Compare current bootstrap versus compiled context on at least one real or replayed work unit and demonstrate reduced reconstruction without correctness loss.

## Phase 3 — Authority supersession and reconcile

Commands:

```text
b-disp reconcile <issue> --dry-run
b-disp reconcile <issue>
```

Prove:
- earlier completion error + later JC ACCEPT;
- earlier Founder exception + later Founder resolution;
- durable result exists but transition incomplete;
- ambiguous evidence fails closed.

No LLM.

## Phase 4 — Continue/re-admission

Commands:

```text
b-disp continue <issue> --dry-run
b-disp continue <issue>
```

Rules:
- use current Project state;
- verify blocker resolution;
- run canonical preflight;
- feed normal EventRelay admission;
- no direct lifecycle mutation.

## Phase 5 — Explicit worker-resource ownership

Model:

```text
resource
capacity
owner invocation
acquired_at
```

Proof:
multiple ACCEPT items sharing one Morty resource are serialized.

No generalized queue.

## Phase 6 — Lifecycle/install hygiene

Commands:

```text
b-disp version
b-disp install
b-disp upgrade
b-disp cleanup-owned
```

Rules:
- preserve evidence;
- install only reviewed/accepted revision;
- never delete B-DISP-owned execution branch before DONE;
- clean only B-DISP-owned resources.

## Phase 7 — Spec Kit integration

Evaluate Spec Kit extension/hook surfaces such as:
- after_tasks;
- before_taskstoissues;
- after_taskstoissues;
- before_implement;
- after_implement.

Expected division:
Spec Kit owns outer feature workflow.
Agent Ready/BIU gates readiness.
B-DISP executes bounded Issue.
Spec Kit converge owns feature completeness.

Deliverable:
one documented integration path with no duplicated Spec Kit semantics.

## Phase 8 — Portability proof

Configure B-DISP against a second sandbox repository without source changes.

Prove:
- Spec Kit refs discoverable/configurable;
- roles/resources configurable;
- bounded status mapping configurable;
- operator commands work;
- B-DISP core unchanged.

Only then call B-DISP reusable infrastructure.
