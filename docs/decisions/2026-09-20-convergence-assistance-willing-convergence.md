# AlienIntent — Convergence Assistance / Willing Convergence

**Date:** 2026-09-20  
**Status:** Founder strategic/product decision — make durable immediately  
**Canonical path:** this file. Renamed from `alienintent-convergence-assistance-willing-convergence.md` under documentation normalization; content unchanged.
**Purpose:** Define and test a factory capability that helps agents finish bounded work willingly and efficiently rather than relying primarily on repeated rejection or increasingly coercive prompting.

## 1. Core principle

AlienIntent should optimize for:

> **willing convergence, not merely enforced compliance.**

The factory must preserve hard boundaries:

- no scope expansion;
- no regression;
- no fake DONE;
- no silent architecture change;
- no evidence deletion;
- no requirement reinterpretation.

But the preferred mechanism for getting an agent across the finish line is not repeated punishment.

The preferred mechanism is:

> **clarity, preserved progress, a visible finish line, appropriately narrowed context, and the smallest sufficient path to completion.**

## 2. Problem statement

Generic coding agents often show a recurring failure mode near completion:

1. early implementation proceeds quickly because the solution space is broad;
2. later verification narrows the remaining problem;
3. the final defects require exactness rather than broad creativity;
4. repeated repair cycles increase friction;
5. the agent begins to reinterpret requirements, broaden scope, rewrite working code, delete valid proof, trade one property for another, or declare plausible completion without discriminating evidence.

This creates **distance-to-done friction**.

The factory must detect this state and change the agent's working environment before repair loops become expensive or non-convergent.

## 3. Linked invariant: monotonic repair

This decision operates together with the existing Convergent Repair / Monotonic Progress rule.

### Behavioral monotonicity

For unchanged governing requirements and acceptance criteria:

> **Previously verified behavior must remain correct.**

### Evidence monotonicity

For unchanged governing requirements and acceptance criteria:

> **Previously valid evidence must remain valid or be explicitly superseded.**

### Convergence-assistance complement

Monotonic repair is the protective boundary.

Convergence Assistance is the positive mechanism.

> **The system should not merely prevent bad repairs. It should actively make the correct finishing move easier to see and execute.**

## 4. Completion Context

As a BIU approaches completion, AlienIntent should be able to generate a **Completion Context**.

A Completion Context is a focused repair context containing:

- BIU identity;
- current candidate identity;
- governing requirement/contract references;
- already satisfied acceptance criteria;
- previously verified behavior that must remain intact;
- evidence that must be preserved;
- unresolved blocking findings;
- unresolved acceptance criteria;
- any explicitly superseded evidence;
- smallest known sufficient next action;
- explicit non-goals;
- completion condition;
- applicable budget / retry limits.

Example:

```text
PY-04 completion context

Already proven:
- AC1
- AC3
- AC4
- AC5
- AC7
- AC11
- architecture fitness
- candidate custody

Preserve:
- existing passing evidence for all above criteria

Unresolved:
- AC2 FIFO among absent-priority items lacks discriminating proof

Why current proof is insufficient:
- observed order could be explained by ID order instead of FIFO

Smallest sufficient next action:
- create two absent-priority items whose insertion order differs from ID order
- assert exact expected order
- reverse insertion order and assert the result reverses
- do not alter scheduling logic unless the new proof demonstrates a behavior defect

Completion condition:
- AC2 is independently verified with discriminating evidence
- all previously accepted proof remains valid
```

The Completion Context should make the finish line visible.

## 5. Context should contract as distance-to-done decreases

Early implementation may require broad context.

Near completion, broad context may encourage unnecessary reconsideration.

AlienIntent should support progressive context contraction:

```text
early work
→ broad problem / architecture / repository context

mid work
→ bounded BIU + current implementation context

late work
→ resolved set + unresolved set + preservation obligations + smallest sufficient completion path
```

The system should avoid repeatedly re-presenting the entire project when only one narrow obligation remains.

## 6. Preserve agency

Convergence Assistance should specify the required outcome and evidence, not prescribe exact code unless exact code is the requirement.

Preferred:

> “Produce discriminating FIFO evidence. Existing scheduling behavior appears correct. Do not alter scheduling logic unless the proof demonstrates a defect.”

Avoid unnecessary micromanagement such as:

> “Change line 214 to exactly this code.”

The system constrains the target and proof obligations while preserving the agent's ability to solve the bounded problem.

## 7. Positive progress state

Each repair cycle should explicitly preserve and present cumulative progress.

The agent should receive:

- resolved findings;
- unresolved findings;
- previously accepted criteria;
- evidence-preservation obligations.

A fresh repair invocation should not reconstruct the BIU as if nothing has been accomplished.

The default framing should be:

> **These properties are already proven. Keep them proven. These are the only remaining gaps.**

## 8. Local completion feedback

AlienIntent should eventually provide a direct way for the worker to ask:

> **Am I done?**

Conceptually:

```text
alienintent verify-current-biu
```

Possible output:

```text
7/8 obligations satisfied

PASS AC1
PASS AC2
PASS AC3
FAIL AC4 — FIFO evidence is not discriminating
PASS AC5
PASS AC6
PASS AC7
PASS AC8

Completion requires AC4 only.
```

The command/API name is not binding.

The capability is:

> **give the worker an explicit, machine-derived view of remaining completion obligations.**

## 9. Escalating assistance before declaring failure

Repeated failure should trigger progressively stronger assistance rather than immediate repeated rejection with identical context.

Possible sequence:

### Repair attempt 1
Normal repair context.

### Repair attempt 2
Narrower Completion Context.

### Repair attempt 3
Director adds:
- diagnostic explanation;
- similar successful precedent;
- clearer discriminating-proof requirement.

### Repair attempt 4
Route to a model/provider with stronger observed convergence performance for this task class.

### Repair attempt 5
Invoke an appropriate specialist or re-plan the repair.

The exact thresholds should become policy/configuration driven.

The important rule is:

> **Do not spend unlimited cycles giving the same agent essentially the same problem in essentially the same context.**

## 10. Distance-to-done friction

AlienIntent should measure how agent efficiency changes as unresolved work approaches zero.

Candidate measures:

- unresolved acceptance criteria per cycle;
- unresolved blocking findings per cycle;
- repair diff size;
- tokens per unresolved finding;
- elapsed time per unresolved finding;
- repeated-finding count;
- behavioral regressions introduced per repair;
- proof regressions introduced per repair;
- cycles after 90% of acceptance obligations are already satisfied;
- time since last net progress;
- scope-expansion attempts near completion;
- evidence deletions near completion;
- provider/model used for each repair cycle.

Derived concepts may include:

- distance-to-done;
- convergence friction;
- repair efficiency;
- proof stability;
- behavioral stability;
- convergence velocity.

Exact formulas are not yet canonized.

## 11. Convergence vs thrashing

A repair loop is **converging** when each cycle materially does one or more of:

- removes an unresolved blocking finding;
- strengthens insufficient evidence;
- replaces a broad defect with a narrower defect;
- preserves all previously accepted behavior/evidence;
- reduces the smallest remaining completion set.

A repair loop is **thrashing** when one or more of these occur:

- the same blocking finding survives multiple repair attempts substantially unchanged;
- a previously resolved blocking finding reappears without authorized target change;
- behavioral monotonicity is violated;
- evidence monotonicity is violated;
- multiple consecutive cycles produce no net reduction in unresolved obligations;
- repair cost/time exceeds policy;
- producer/verifier disagreement is really about requirement meaning rather than implementation;
- repair diffs grow as the unresolved problem shrinks.

Thrashing should trigger diagnosis rather than blind continuation.

## 12. Thrashing diagnosis

When non-convergence is detected, classify the likely cause:

```text
implementation defect
proof/evidence defect
contract ambiguity
verification defect / false positive
architecture problem
context problem
provider/model weakness
capability limitation
budget limitation
```

Then choose an appropriate remedy:

- narrower context;
- stronger explanation;
- better precedent;
- provider rerouting;
- specialist invocation;
- contract clarification;
- human authority escalation only when genuinely required.

## 13. Factory-yield metrics

Convergence Assistance should become measurable.

Potential metrics:

- repair_convergence_rate;
- distance_to_done_friction;
- cycles_to_accept;
- cycles_after_90_percent_complete;
- repeated_finding_rate;
- proof_regression_rate;
- behavioral_regression_rate;
- evidence_items_gained_per_cycle;
- evidence_items_lost_per_cycle;
- repair_diff_size_per_remaining_finding;
- tokens_per_remaining_finding;
- elapsed_seconds_per_remaining_finding;
- scope_expansion_attempts;
- percentage_of_repairs_preserving_all_prior_proof;
- model/provider convergence performance by task class;
- assistance intervention effectiveness;
- context-contraction effectiveness.

Missing telemetry is UNKNOWN, never zero.

## 14. Experimental hypothesis

Primary hypothesis:

> **A focused Completion Context reduces repair cycles, token use, proof regression, scope drift, and time-to-accept compared with repeatedly giving the worker the full BIU context plus verifier findings.**

Secondary hypotheses:

1. context contraction improves final-stage convergence;
2. explicit resolved/unresolved sets reduce unnecessary rewriting;
3. smallest-sufficient-next-action guidance reduces repair diff size;
4. provider routing based on convergence history reduces late-stage cycles;
5. progress framing improves proof preservation;
6. agents differ materially in “finishing ability” even when they perform similarly during broad implementation.

## 15. Initial test design

Do not disrupt a live BIU solely to test this.

Start collecting baseline evidence from current Wave 1 repair cycles.

For future comparable repair cycles, test at least two treatments where operationally safe:

### Baseline
Existing repair context:
- BIU;
- verifier findings;
- normal project context.

### Convergence-assisted
Completion Context:
- already proven;
- preserve;
- unresolved;
- why current evidence fails;
- smallest sufficient next action;
- exact completion condition;
- narrower relevant context.

Compare:

- cycles to ACCEPT;
- tokens;
- elapsed time;
- diff size;
- repeated findings;
- regression count;
- proof loss;
- scope expansion;
- verifier findings per cycle.

Do not claim causality from a tiny sample.

## 16. Director role

The future AlienIntent Director should own generation of Completion Context proposals.

The deterministic kernel should supply authoritative state:

- current BIU;
- accepted evidence;
- unresolved findings;
- lifecycle;
- candidate identity;
- governing contract.

The Director may propose:

- narrow explanation;
- smallest sufficient next action;
- precedent;
- provider reroute.

It may not:

- change requirements;
- silently relax proof;
- discard accepted evidence;
- redefine DONE.

## 17. Better working environment principle

This capability is an application of the broader AlienIntent constitutional principle:

> **Give intelligence a better working environment.**

The goal is not to force models through ever narrower constraints.

The goal is to make the legitimate completion path obvious, small, and attractive.

Hard invariants remain as the safety boundary.

Convergence Assistance is the positive guidance mechanism.

## 18. Durable product requirement

AlienIntent should have an explicit Product Requirement for this capability.

Suggested title:

> **Convergence Assistance / Distance-to-Done Optimization**

Requirement:

> AlienIntent must be capable of detecting late-stage convergence friction and, when policy permits, presenting workers with a progressively focused completion context that preserves proven behavior/evidence, exposes only unresolved obligations, and identifies the smallest sufficient path to completion. The system must measure whether these interventions improve convergence, cost, quality, and proof stability.

Do not infer product priority or Wave solely from this document.

## 19. Non-goals

This decision does not authorize:

- adding a new Project lifecycle state;
- weakening verifier independence;
- relaxing acceptance criteria;
- removing normal rejection;
- unlimited retries;
- deceptive model manipulation;
- automatically rewriting requirements;
- creating a specialist-agent hierarchy without evidence.

“Convergence Mode” is currently a context/policy concept, not a required visible lifecycle state.

## 20. Immediate durability

This decision should be represented durably in:

1. a Founder/architecture decision record;
2. a Product Requirement in the backlog;
3. future Director/repair-context design;
4. Engineering Trajectory / Quality Evidence metrics;
5. a planned experiment comparing normal repair versus convergence-assisted repair.

Prompts may use the rule, but the capability must not depend on a prompt being remembered.

## 21. Concise constitutional formulation

> **AlienIntent should optimize for willing convergence, not merely enforced compliance. As work approaches completion, the factory should preserve proven progress, contract context around the remaining gap, expose an explicit finish line, and provide the smallest sufficient path to completion while retaining hard guarantees against regression, scope expansion, and fake DONE.**
