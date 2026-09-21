# POSTW1-PACKET-014 — Founder approval packet and final report

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §4. This is
the programme's last phase. An independent fresh-Claude accuracy check follows.

## 1. Objective

Prepare the **complete Founder approval packet** and the single durable final report. Under
amendment §11 this is prepared automatically rather than offered; under §12 the report is the
programme's terminal artifact.

## 2. Everything the packet must contain

From amendment §11, all of it:

executive summary · Wave 1 final evidence conclusions · Learning Ledger summary · Gap Trap
promotions · unresolved ownership gaps · Agent-Ready process changes · split/replan design ·
bootstrap retirement decisions and recommendations · final Wave 1 architecture reconciliation ·
Wave 2 selected requirements · Design Contracts · Design Verification results · dependency DAG ·
candidate BIUs · Agent-Ready results · unresolved risks and UNKNOWNs · explicit Founder decisions
required · recommended decisions · repository SHAs · deterministic validation results · review
dispositions · estimated model/token/cost data where known · routing and yield observations.

Where a value is genuinely unknown — token usage and cost are UNKNOWN for all 11 Wave 1 BIUs and
for every dispatch in this programme — record UNKNOWN. Never a zero.

## 3. The sources

All under `docs/evidence/`: `wave1-learning-ledger` · `wave1-gap-trap-promotion-backlog` ·
`wave1-agent-ready-outcome-matrix` · `wave1-biu-split-replan-design` ·
`wave1-bootstrap-retirement-matrix` · `wave1-final-retrospective` ·
`wave2-specified-requirements` · `wave2-design-contracts` · `wave2-design-verification` ·
`wave2-dependency-dag` · `wave2-candidate-bius` · `wave2-agent-ready-assessments`.

Programme state: `docs/operations/post-wave1-program/program-state.json` (23 tasks, 7 open
Founder decisions, all non-blocking).

**Orchestration record**:
`docs/operations/post-wave1-program/prework/POSTW1-PACKET-014-orchestration-record.json`. This is
the coordinator's own account of how it ran the programme, explicitly labelled participant
evidence. It includes the coordinator's eight recorded errors and the four disputes dispatched
sessions raised against it, all upheld. Use it for the orchestration-effectiveness section, and
treat its self-assessment as a claim rather than a finding.

## 4. Deliverables

- `docs/operations/post-wave1-program/reports/FINAL-REPORT.md` — the durable final report
- `docs/evidence/wave2-founder-approval-packet.json` — the structured packet

The final report must answer, per amendment §12:

**What happened** — what Wave 1 proved, what failed, what was learned, what was corrected.
**What changed** — requirement and decision amendments, new deterministic controls, process
changes, design and process capabilities added.
**What remains unresolved** — NEW_CAPABILITY_GAP items, Founder decisions, residual UNKNOWNs,
accepted risks, deferred work.
**Wave 2** — proposed scope, verified architecture, plan and DAG, BIU set, Agent-Ready state,
execution prerequisites.
**Factory effectiveness** — which known failure classes moved from model REVIEW to deterministic
control, where model cognition is still required, evidence of reduced repeated reasoning where
measurable.
**Orchestration effectiveness** — model and provider usage by task class, deterministic work
substituted for model work, review utilisation, repair cycles, token/cost where available and
UNKNOWN where not, routing recommendations for Wave 2.
**Founder action** — a concise final section: APPROVALS REQUIRED, DECISIONS REQUIRED, OPTIONAL
FOLLOW-UPS. If no Founder decisions remain before Wave 2 execution, say so explicitly.

## 5. Two things the report must state plainly, not soften

**Wave 2 has zero READY BIUs.** All 46 were assessed; 45 BLOCKED, 1 NEEDS_CLARIFICATION. Its
single assessable entry point, WO-220101, waits on clarification AR13-CQ-001. Forty-six
well-formed BIUs must not be presented as though they were startable. Say what must happen before
Wave 2 can begin.

**Seven Founder decisions are open and their leverage is uneven.** 23 of 46 DAG nodes are
gap-blocked with heavy overlap: resolving `R1-GAP-013-ALLOCATION` alone frees zero nodes
completely, `R1-GAP-039-ORCHESTRATION` zero, `R1-GAP-039-REAL-OUTCOME` one,
`R2-GAP-051-EDGE-AUTHORITY` one, and `R1-GAP-MONITOR-HOST` five. The two SF-REQ-039 gaps together
free six. Only resolving all five unblocks the plan. A reader given raw per-gap counts would
prioritise wrongly.

## 6. Recommendations are recommendations

Give a recommended disposition for each open decision, clearly marked as a recommendation. Do not
create, amend or weaken any requirement, assign Priority or Wave, or close any authority gap.

## 7. Acceptance

```
python3 tools/evidence/check_wave1.py --negative-controls
```

All twelve programme checkers should still pass against their artifacts; report any that do not.
Do not edit any checker. Dispute what you believe wrong in `DISPUTED` and leave it unrepaired.

## 8. Out of scope

Do not begin Wave 2 execution. Do not modify prior deliverables or Wave 1 evidence, lifecycle
state, Project state or worker contracts. Do not `git commit`, push, or use the network.

## 9. Terminal report — this block only

```
PACKET_SECTIONS=<n of 23>
FINAL_REPORT_SECTIONS=<n of 7>
OPEN_FOUNDER_DECISIONS=<n> RECOMMENDED=<n>
WAVE2_READY_BIUS=<n>
WAVE2_EXECUTION_PREREQUISITES=<n>
UNKNOWNS_RECORDED=<n>
CHECKERS_PASSING=<n of 12>
FAILURE_CLASSES_MOVED_TO_DETERMINISTIC=<n>
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
