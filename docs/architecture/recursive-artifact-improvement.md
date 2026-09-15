# Recursive Artifact Improvement (RAI)

**Status:** Development discipline first; product automation deferred.

## Purpose

RAI is the bounded process:

```text
implement → adversarially inspect → identify concrete defects → repair → re-evaluate → stop when no BLOCKING/MATERIAL defect remains
```

It is not open-ended self improvement.

## Current decision

B-DISP SHALL include iteration/evidence primitives now, but SHALL NOT autonomously recurse yet.

1. Build B-DISP with iteration/evidence primitives.
2. Use RAI manually as the development discipline.
3. Collect evidence across real work.
4. Derive recursion semantics from observed failure modes.
5. Add bounded RAI execution to B-DISP.
6. Do not add open-ended recursive autonomy.

## Primitives

### Iteration
Each artifact iteration has stable artifact identity, iteration identity, ordinal, immediate parent, candidate reference, timestamp, and capability epoch. Iteration 0 is the baseline. Later iterations are adjacent diffs, not fresh regenerations.

### Capability epoch
Evaluation evidence records provider, model, model version when available, harness version, and prompt-set version. Model evidence may decay as capabilities change.

### Finding
A finding records evaluator identity, iteration, severity (BLOCKING/MATERIAL/ADVISORY), concise defect statement, evidence references, and lifecycle (OPEN/RESOLVED/REJECTED/SUPERSEDED).

### Evaluation
An evaluation records evaluator, capability epoch, iteration, findings, outcome, completion time, and the anti-slop critique.

## Mandatory anti-slop question

> **What did the previous iteration add or retain that is unnecessary, speculative, redundant, or more complex than the simplest correct solution?**

## Manual stopping semantics

```text
No open BLOCKING/MATERIAL finding → STOP
Open BLOCKING/MATERIAL finding + repair fits authority → CONTINUE
Open BLOCKING/MATERIAL finding + repair crosses authority → ESCALATE
```

ADVISORY findings do not justify another iteration by themselves.

## Finding budget

Initially surface at most three OPEN BLOCKING/MATERIAL findings per evaluation pass. This forces prioritization and avoids speculative defect backlogs.

## Evidence

Raw observations are preserved. Derived conclusions may evolve. Worker logs are diagnostic evidence, not canonical truth. Outcome evidence outranks process evidence.

## Relationship to B-DISP

RAI does not replace Spec Kit specification/planning/convergence, Agent Ready readiness, or B-DISP admission/verification/closure. For now it is a development discipline around B-DISP work.

## Explicitly deferred

No recursive executor, automatic repair loop, iteration-count loop, "repeat until good", autonomous architecture changes, scope expansion, or advisory-triggered recursion.
