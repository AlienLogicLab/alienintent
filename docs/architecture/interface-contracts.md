# B-DISP Interface Contracts

## 1. Spec Kit → Agent Ready / BIU

### Spec Kit owns
- constitution;
- feature specification;
- clarification;
- technical plan;
- task decomposition;
- consistency analysis;
- requirement checklists;
- general workflow orchestration;
- feature convergence.

### Inputs to Agent Ready / BIU
References to:
- `spec.md`;
- `plan.md`;
- `tasks.md`;
- specific task IDs or bounded task groups;
- constitution/architecture constraints when required;
- repository baseline.

### Agent Ready / BIU responsibilities

Agent Ready answers:
> Is this work unit sufficiently understood, cohesive, constrained, and verifiable to hand to an autonomous coding agent?

BIU Builder:
- materializes the canonical BIU;
- fills machine-resolvable fields;
- asks only for unresolved intent/authority;
- invokes Agent Ready through its supported boundary;
- creates a GitHub Issue only after readiness.

### Must NOT cross boundary
Agent Ready / BIU must not:
- rewrite feature specification;
- become the feature planner;
- own whole-feature decomposition;
- copy Spec Kit workflow logic;
- copy Agent Ready internals into FactoryChecks.

---

## 2. Agent Ready / BIU → B-DISP

### Entry condition
B-DISP admission requires a bounded GitHub Issue containing:
- task;
- rationale;
- allowed scope;
- architecture references;
- acceptance criteria;
- proof requirements;
- parent Spec Kit references;
- baseline SHA;
- upstream semantic readiness.

### Canonical references

```text
spec_kit:
    feature
    spec_ref
    plan_ref
    task_ref

biu:
    issue
    baseline_sha
    allowed_scope
    acceptance_criteria
    proof_requirements

execution:
    project_item
    current_phase
```

### B-DISP owns
- current execution authority;
- admission;
- worker identity;
- resource ownership;
- context compilation;
- Morty execution;
- JC verification;
- durable evidence;
- restart/replay;
- operational closure.

### Must NOT cross boundary
B-DISP must not:
- regenerate feature requirements;
- alter Spec Kit planning semantics;
- split features as a general planning function;
- infer a different feature plan;
- declare feature-wide completion.

---

## 3. B-DISP → Spec Kit converge

### B-DISP output condition

B-DISP returns a bounded work unit only after DONE.

DONE means:
- independently verified;
- landed;
- deployed/published if required;
- operationally verified if required;
- no known required work remains for that work unit.

### Output

```text
work_unit:
    issue
    task_ref
    result: DONE
    accepted_candidate
    landed_revision
    verification_evidence
    operational_evidence
    known_nonblocking_findings
```

### Spec Kit converge owns
- full requirement satisfaction;
- overall task completeness;
- creation of missing work;
- feature/specification convergence.

B-DISP DONE must never be interpreted as feature complete.

---

## 4. Operator → B-DISP

### Operator expresses semantic intent

```text
show status
explain blocker
continue valid execution
reconcile durable evidence
inspect resources
install accepted control-plane revision
```

Operators should not need to:
- fabricate webhooks;
- construct Project node IDs;
- edit state JSON;
- manually correlate invocation comments;
- manually derive encoded log paths.

### Read-only
```text
status
explain
doctor
logs
version
resources
```

### Mutating
Future mutating commands must:
- support dry-run where practical;
- show exact intended action;
- use EventRelay/GitHubAuthority semantics;
- preserve evidence;
- never become a second state machine.

### Expert event injection

`emit` may exist only as a lower-level expert/debug operation.

It must:
- construct a canonical event;
- feed EventRelay;
- never directly mutate Project or local lifecycle state.

---

## 5. Authority precedence

Durable chronology is not durable authority.

Example:

```text
T1 Morty COMPLETION_ERROR
T2 JC ACCEPT
T3 Project ACCEPT
```

T1 remains historical evidence but must not route work backward once T2/T3 establish later authority.

Likewise:

```text
T1 FOUNDER_EXCEPTION
T2 Founder resolution
T3 fresh explicit admission
```

T1 remains evidence but is not a permanent veto.

---

## 6. Context isolation

### Morty continuing work
High continuity:
- current authoritative intent;
- prior accepted decisions;
- current repository state;
- relevant prior implementation state.

### JC verification
Deliberate isolation:
- authoritative upstream references;
- BIU;
- candidate;
- diff;
- acceptance criteria;
- proof requirements.

Exclude Morty's reasoning transcript by default.

### Morty closure after JC ACCEPT
Outcome continuity:
- JC ACCEPT;
- accepted SHA;
- material findings;
- closure obligations.

Not the full JC transcript unless required by a contradiction.

---

## 7. Stop-condition contract

Every worker context package states:

```text
goal
allowed_scope
required_evidence
stop_condition
escalation_condition
```

Advisory evidence is never an implicit completion gate.
