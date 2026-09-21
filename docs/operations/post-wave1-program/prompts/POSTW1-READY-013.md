# POSTW1-READY-013 — Agent-Ready assessment of the Wave 2 BIU set

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §6.

## 1. Objective

Assess every one of the 46 candidate Wave 2 BIUs using the **audited** outcome-handling process,
so that Phase 14 can report which are genuinely release-eligible.

Exit gate: all intended Wave 2 release candidates are READY, or explicitly excluded or blocked.

## 2. The rules, and why each exists

- **Fresh current assessment.** Not inherited, not assumed from the plan's eligibility counts.
- **Exact baseline.** Record the repository SHA each assessment was made against.
- **Explicit provider/model provenance** on every assessment.
- **Terminal result validated structurally** — success is not inferred from an assessment having
  been attempted.
- **Every non-READY outcome follows the canonical handling matrix**
  (`docs/evidence/wave2-agent-ready-outcome-matrix.json` is Wave 1's;
  `docs/evidence/wave1-agent-ready-outcome-matrix.json` is the audited one — use the audited
  matrix): only READY permits implementation, and every non-READY outcome carries a next action
  and a reassessment trigger.
- **No disposition coerced to READY.** This is the one the checker enforces hardest.
- **SPLIT_RECOMMENDED invokes the defined split/replan process**
  (`docs/evidence/wave1-biu-split-replan-design.json`) rather than improvising. Phase 5 designed
  it precisely so a future split is not a judgement call.
- **NEEDS_CLARIFICATION creates explicit clarification authority** — name who can answer.
- **BLOCKED remains blocked until inputs change.** Resolved prerequisites do not retroactively
  rewrite a verdict; a reassessment is required.
- **Assessment execution failure is not a disposition.** LRN-008 records a verifier that exited
  success with no verdict and became DURABLE_RESULT_MISSING rather than ACCEPT. Put failures in
  `execution_failures`, never in `disposition`.

## 3. The bar must not silently vary

23 of the 46 BIUs carry open authority gaps. A BIU waiting on a Founder decision is **not**
READY, whatever else is true of it. The checker refuses any READY with a non-empty
`open_authority_gaps`, so a BIU you believe otherwise complete still cannot be marked ready while
its gap is open — record it as BLOCKED with the gap as its reassessment trigger.

Phase 12 reported 14 eligible now and noted that nine further BIUs "require separate authority".
Do not collapse that distinction into a readiness count: separate authority is not the same as an
open gap, and the difference will matter to the Founder.

## 4. Inputs

`docs/evidence/wave2-candidate-bius.json` (46 BIUs, 16 fields each) ·
`docs/evidence/wave1-agent-ready-outcome-matrix.json` (the audited matrix) ·
`docs/evidence/wave2-design-verification.json` (five open gaps) ·
`docs/evidence/wave1-biu-split-replan-design.json` (the split process) ·
`docs/evidence/wave2-dependency-dag.json`

## 5. Assess honestly, including against the decomposition

An assessment that returns 46 READY would be evidence that the bar moved, not that the work is
good. Equally, marking everything BLOCKED to be safe is not assessment. Wave 1's own Agent-Ready
returned BLOCKED, SPLIT_RECOMMENDED and NEEDS_CLARIFICATION at different times and each was
correct then.

One specific thing to judge rather than assume: Phase 12's integration capstone **WO-220211**
carries a single compound acceptance criterion covering inventory, ambiguity, premise/proof,
design applicability, compilation and lint consumption, with proof fixture FX-A marked
`PLANNED_NOT_EXECUTED`. The coordinator review declined to call that a defect and referred the
question here. Decide whether it is assessable as written.

## 6. Deliverables

- `docs/evidence/wave2-agent-ready-assessments.json` (authoritative), with `assessments`,
  `required_bius` (all 46 ids), `execution_failures`, `resolution_history`, and provenance
- `docs/evidence/wave2-agent-ready-assessments.md` (prose companion)

Each assessment: `biu_id`, `disposition`, `open_authority_gaps`, `provider`, `model`,
`baseline_sha`, `assessed_at`, `terminal_result_valid`, `implementation_allowed`, `next_action`,
`reassessment_trigger`, plus `split_process_ref` where SPLIT_RECOMMENDED and
`clarification_authority` where NEEDS_CLARIFICATION.

## 7. Acceptance

```
python3 tools/evidence/check_agent_ready_set.py docs/evidence/wave2-agent-ready-assessments.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Do not edit any checker. **Dispute what you believe wrong** in `DISPUTED` and leave it failing.

## 8. Out of scope

Do not release, implement, or advance any lifecycle state — this is assessment only. Do not
create, amend or weaken any requirement, or close any authority gap. Do not modify prior
deliverables, Wave 1 evidence, Project state or worker contracts. Do not `git commit`, push, or
use the network. Do not begin Phase 14.

## 9. Terminal report — this block only

```
ASSESSED=<n of 46>
READY=<n> BLOCKED=<n> NEEDS_CLARIFICATION=<n> SPLIT_RECOMMENDED=<n>
GAP_BLOCKED_NOT_READY=<n, must equal the number carrying open gaps>
SEPARATE_AUTHORITY_REQUIRED=<n>
EXECUTION_FAILURES=<n>
WO_220211_ASSESSABLE=<yes | no, with disposition>
BASELINE_SHA=<the sha assessed against>
READY_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
