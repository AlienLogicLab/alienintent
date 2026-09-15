# Recursive Artifact Improvement (RAI)

**Status:** Development discipline first; product automation deferred.

RAI is bounded: implement → adversarially inspect → identify concrete defects → repair → re-evaluate → stop when no BLOCKING/MATERIAL defect remains.

## Current decision
1. Build B-DISP with iteration/evidence primitives.
2. Use RAI manually as the development discipline.
3. Collect evidence across real work.
4. Derive recursion semantics from observed failure modes.
5. Add bounded RAI execution to B-DISP.
6. Do not add open-ended recursive autonomy.

## Iteration
Iteration 0 is the baseline. The current model is a **single linear chain**: one iteration per ordinal, contiguous from 0, each later iteration directly references the immediately preceding iteration. Branching histories are deferred.

## Capability epoch
Evaluation evidence records provider/model plus available model, harness, and prompt-set versions. Epoch data is snapshotted into iterations/evaluations so later caller mutation cannot rewrite provenance.

## Findings and evaluations
Findings are BLOCKING, MATERIAL, or ADVISORY and belong to exactly one iteration. A classification/review pass may not mix iterations or duplicate finding identities.

## Mandatory anti-slop question
> **What did the previous iteration add or retain that is unnecessary, speculative, redundant, or more complex than the simplest correct solution?**

## Manual stopping semantics
- no open BLOCKING/MATERIAL finding → STOP
- open BLOCKING/MATERIAL finding within authority → CONTINUE
- open BLOCKING/MATERIAL finding outside authority → ESCALATE

ADVISORY findings do not justify another iteration by themselves. Initially surface at most three open BLOCKING/MATERIAL findings per iteration/pass.

Raw observations are preserved. Derived conclusions may evolve. Worker logs are diagnostic evidence, not canonical truth. Outcome evidence outranks process evidence.

RAI does not replace Spec Kit specification/planning/convergence, Agent Ready readiness, or B-DISP admission/verification/closure.

## Deferred
No recursive executor, automatic repair loop, iteration-count loop, "repeat until good", autonomous architecture changes, scope expansion, or advisory-triggered recursion.
