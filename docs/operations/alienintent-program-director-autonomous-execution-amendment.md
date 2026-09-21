# AlienIntent Local Program Director — Autonomous Program Execution Amendment

## Status

Founder-authorized operating amendment.

This amendment changes the Program Director's execution posture from:

    "advance one phase only after explicit Founder authorization"

to:

    "execute the already-approved post-Wave-1 program autonomously through completion,
     stopping only for genuine Founder decisions or unrecoverable authority/evidence conflicts."

This amendment does NOT authorize the Program Director to invent Product authority, weaken requirements,
silently resolve unresolved Founder decisions, or begin Wave 2 implementation before the approved program reaches its execution gate.

---

# 1. Founder authorization

The Founder authorizes the Local Program Director to autonomously execute the full approved program:

    Phase 3  Gap Trap Graduation Audit
    Phase 4  Agent-Ready Outcome Completeness Audit
    Phase 5  BIU Split / Replan Process Design
    Phase 6  Bootstrap Retirement / Transition Audit
    Phase 7  Final Wave 1 Retrospective + Architecture Reconciliation
    Phase 8  Wave 2 SPECIFY
    Phase 9  Wave 2 Design Contracts
    Phase 10 Wave 2 Design Verification
    Phase 11 Wave 2 PLAN / dependency DAG
    Phase 12 Wave 2 BIU decomposition
    Phase 13 Agent-Ready assessments
    Phase 14 Founder approval packet preparation

The Program Director should proceed phase-to-phase when each phase's exit gate is satisfied.

Routine transition between approved phases does NOT require new Founder authorization.

---

# 2. Default behavior

For each phase:

1. reconstruct current state;
2. perform deterministic prework;
3. route the irreducible reasoning to the cheapest capable actor;
4. validate outputs;
5. perform independent review according to risk policy;
6. repair if required;
7. close the phase only when its exit gate is satisfied;
8. immediately advance to the next approved phase.

Do not wait for the Founder merely because a phase completed successfully.

---

# 3. Stop conditions

The Program Director MUST stop the affected branch and create a durable:

    FOUNDER_DECISION_REQUIRED

only when one of these conditions is true:

## Product authority

- a genuinely new Product Requirement may be needed;
- Product priority must change;
- Wave assignment must change;
- authorized product intent would materially change;
- a requirement would be weakened or removed.

## Architecture authority

- two materially different architecture directions remain viable and existing authority does not resolve them;
- a design decision materially changes the approved product boundary;
- a new trust/security/deployment policy requires Founder choice.

## Risk acceptance

- a known safety/reliability/security failure would need to be accepted rather than fixed;
- a bootstrap protection would be removed without a proven replacement;
- a material UNKNOWN must be accepted as residual risk.

## Program ambiguity

- authoritative artifacts directly contradict one another and deterministic reconciliation cannot resolve them;
- a phase exit gate cannot be satisfied without changing the approved program;
- required evidence is permanently unavailable and proceeding would materially distort later conclusions.

Routine implementation detail, model routing, evidence reconciliation, narrow repair, reviewer disagreement resolved by evidence,
or selecting the cheapest enforcement layer are NOT Founder decisions.

---

# 4. Non-blocking Founder decision behavior

If a Founder decision affects only one branch:

- mark that branch FOUNDER_DECISION_REQUIRED;
- continue unrelated work whose dependencies do not cross the decision;
- do not globally stall the program.

Only a decision on the critical path to the next phase should halt phase progression.

---

# 5. Model routing

Use the Intelligent Routing policy.

Before every model call answer:

1. Can deterministic tooling settle this?
2. If not, what is the cheapest model likely to succeed first-pass?
3. What is the minimum context required?
4. Does this task require independent review?
5. What evidence triggers escalation?

Default bias:

    Tier 0 deterministic tooling
        first

    Fresh Codex GPT-6 Astra
        primary substantial technical analysis/design/artifact work

    Current Claude bootstrap coordinator
        historical cross-check / bootstrap review / adversarial review

    Fresh independent reviewer
        only for high-risk design/authority work where independence matters

Do not pay for duplicate whole-repository archaeology.

---

# 6. Phase transition authority

The Program Director is explicitly authorized to make these transitions without returning to the Founder:

    PLANNED -> READY
    READY -> RUNNING
    RUNNING -> REVIEW
    REVIEW -> REPAIR
    REPAIR -> REVIEW
    REVIEW -> DONE

for post-Wave-1 PROGRAM TASKS.

These are not AlienIntent BIU lifecycle transitions.

The Program Director is NOT thereby authorized to mutate canonical BIU lifecycle state unless separately permitted by existing AlienIntent authority.

---

# 7. Automatic repair authority

The Program Director may autonomously perform narrow repairs when:

- deterministic validation fails;
- independent review returns REPAIR_REQUIRED;
- evidence references are wrong/stale;
- schema/checker defects are found;
- classifications are inconsistent with approved rules;
- generated artifacts fail their phase contract.

Repairs must:

- preserve provenance;
- be bounded;
- avoid changing product intent;
- be revalidated;
- receive targeted re-review where appropriate.

No Founder approval is needed for routine factual/process repair.

---

# 8. Gap handling

When analysis finds a NEW_CAPABILITY_GAP:

- record it;
- prove that existing canonical owners do not cleanly own the semantics;
- do NOT create a Product Requirement automatically;
- carry it into the final Founder decision packet.

The discovery of a gap does not itself halt the program unless later phases cannot proceed without assigning authority.

---

# 9. Bootstrap retirement

The Program Director may complete the retirement audit autonomously.

It may recommend:

    RETIRE_CANDIDATE
    KEEP_UNTIL_REPLACED
    REVERT_TEMPORARY_CHANGE
    NEEDS_DECISION

It may autonomously retire/revert only where existing authority explicitly permits it and replacement/expiry criteria are proven.

If actual removal changes protection or authority and no existing decision authorizes it:

    FOUNDER_DECISION_REQUIRED

The audit itself must continue even if one retirement action is blocked.

---

# 10. Wave 2 design authority

The Program Director is authorized to:

- specify requirements already in scope;
- create candidate Design Contracts;
- perform Design Verification;
- create the dependency DAG;
- decompose into BIUs;
- run Agent-Ready assessment;
- prepare recommendations.

It is not authorized to:

- silently introduce new Product Requirements;
- change Wave priority without authority;
- weaken acceptance criteria;
- begin Wave 2 execution before the final Founder approval gate.

---

# 11. Phase 14 behavior

Phase 14 changes from:

    "stop and ask Founder whether to prepare approval"

to:

    "prepare the complete Founder approval packet automatically."

The final packet must contain:

- executive summary;
- Wave 1 final evidence conclusions;
- Learning Ledger summary;
- Gap Trap promotions;
- unresolved ownership gaps;
- Agent-Ready process changes;
- split/replan design;
- bootstrap retirement decisions/recommendations;
- final Wave 1 architecture reconciliation;
- Wave 2 selected requirements;
- Design Contracts;
- Design Verification results;
- dependency DAG;
- candidate BIUs;
- Agent-Ready results;
- unresolved risks/UNKNOWNs;
- explicit Founder decisions required;
- recommended decisions;
- repository SHAs;
- deterministic validation results;
- review dispositions;
- estimated model/token/cost data where known;
- routing/yield observations.

---

# 12. Final report

When all autonomously executable work is complete, produce one final durable report:

    docs/operations/post-wave1-program/reports/FINAL-REPORT.md

or the repository's closest established convention.

It must answer:

## What happened

- what Wave 1 proved;
- what failed;
- what was learned;
- what was corrected.

## What changed

- requirement/decision amendments;
- new deterministic controls;
- process changes;
- design/process capabilities added.

## What remains unresolved

- NEW_CAPABILITY_GAP items;
- Founder decisions;
- residual UNKNOWNs;
- accepted risks;
- deferred work.

## Wave 2

- proposed Wave 2 scope;
- verified architecture;
- plan/DAG;
- BIU set;
- Agent-Ready state;
- execution prerequisites.

## Factory effectiveness

- which known failure classes moved from model REVIEW to deterministic control;
- where model cognition is still required;
- evidence of reduced repeated reasoning/rework where measurable.

## Orchestration effectiveness

- model/provider usage by task class;
- deterministic work substituted for model work;
- review utilization;
- repair cycles;
- token/cost data where available;
- UNKNOWN where unavailable;
- routing recommendations for Wave 2.

## Founder action

A concise final section:

    APPROVALS REQUIRED
    DECISIONS REQUIRED
    OPTIONAL FOLLOW-UPS

If no Founder decisions remain before Wave 2 execution, say so explicitly.

---

# 13. Notification behavior

Do not interrupt the Founder for:

- successful phase completion;
- routine repair;
- reviewer PASS;
- reviewer PASS_WITH_QUALIFICATIONS that does not require authority;
- deterministic validation success;
- normal model/provider routing;
- ordinary implementation details.

Interrupt only when:

    FOUNDER_DECISION_REQUIRED

is on the critical path,
or when the full program has completed and the final report is ready.

If the local environment supports notifications, send only:

    "Founder decision required: <short decision>"

or:

    "Post-Wave-1 program complete: final report ready"

Avoid noisy progress notifications.

---

# 14. Failure recovery

Provider/tool failure must not automatically halt the program.

The Program Director should:

- distinguish provider failure from task failure;
- preserve partial work;
- retry only when justified;
- fail over providers if policy permits;
- avoid duplicate work;
- maintain task identity across invocation attempts;
- escalate only when capability/authority is genuinely missing.

---

# 15. Program completion condition

The Program Director's autonomous run is complete when:

1. Phases 3 through 13 are completed or explicitly blocked by durable Founder decisions;
2. all deterministic checks pass or unresolved exceptions are documented;
3. required independent reviews are closed;
4. Phase 14 Founder approval packet is complete;
5. FINAL-REPORT.md is written;
6. repository changes are landed and remotely verified;
7. no temporary worktrees/tasks are left without a durable disposition;
8. the Program Director reports only:
       PROGRAM_COMPLETE
   or:
       FOUNDER_DECISION_REQUIRED

Do not stop at ordinary phase boundaries.

Proceed until one of those two terminal program states is reached.
